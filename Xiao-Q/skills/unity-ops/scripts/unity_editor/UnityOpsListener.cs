using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Text;
using System.Threading;
using UnityEditor;
using UnityEngine;

namespace UnityOps
{
    /// <summary>
    /// 编辑器脚本：监听网络端口，通过JSON消息控制Unity编辑器
    /// </summary>
    [InitializeOnLoad]
    public class UnityOpsListener : EditorWindow
    {
        private static TcpListener tcpListener;
        private static Thread listenerThread;
        private static bool isRunning = false;
        private static int port = 8888;
        private static string statusMessage = "未启动";

        // 线程安全的命令队列：后台线程 enqueue，主线程 dequeue
        private class PendingCommand
        {
            public string json;
            public string result;
            public bool done;
        }
        private static readonly Queue<PendingCommand> pendingCommands = new Queue<PendingCommand>();
        private static readonly object queueLock = new object();
        private static bool queueHasNewCommand = false;

        // 类型名称 → Type 的缓存（静态构造函数中从当前程序集构建）
        private static readonly Dictionary<string, Type> _typeCache;

        static UnityOpsListener()
        {
            // 初始化类型缓存：遍历当前程序集，建立 className → Type 映射
            var asm = Assembly.GetExecutingAssembly();
            var cache = new Dictionary<string, Type>(StringComparer.OrdinalIgnoreCase);
            foreach (Type type in asm.GetTypes())
                cache[type.Name] = type;
            _typeCache = cache;

            EditorApplication.update += Update;
            EditorApplication.quitting += OnEditorQuitting;

            // Domain Reload 钩子：编译前停止服务器，编译后自动恢复
            AssemblyReloadEvents.beforeAssemblyReload += OnBeforeAssemblyReload;
            AssemblyReloadEvents.afterAssemblyReload += OnAfterAssemblyReload;

            // 检查命令行参数，如果包含 -startServer 则自动启动
            var args = Environment.GetCommandLineArgs();
            int startIdx = Array.IndexOf(args, "-startServer");
            if (startIdx >= 0)
            {
                int portIdx = Array.IndexOf(args, "-port");
                if (portIdx >= 0 && portIdx + 1 < args.Length)
                    int.TryParse(args[portIdx + 1], out port);
                Debug.Log($"[UnityOpsListener] 检测到命令行参数 -startServer，自动启动服务，端口: {port}");
                StartServer();
            }
        }

        /// <summary>
        /// Domain Reload 即将开始（cs 文件变更触发编译）。
        /// 必须在此释放 Socket，否则 Unity 重载时持有 TcpListener 会导致卡死。
        /// </summary>
        private static void OnBeforeAssemblyReload()
        {
            if (isRunning)
            {
                Debug.Log("[UnityOpsListener] 检测到脚本重新编译，暂停服务器以避免卡死...");
                StopServer();
                // 标记为"因编译而停止"，reload 后自动恢复
                SessionState.SetBool("UnityOpsListener_AutoRestart", true);
                SessionState.SetInt("UnityOpsListener_Port", port);
            }
        }

        /// <summary>
        /// Domain Reload 完成后（编译成功，新域已加载）。
        /// 若之前是因编译被停止，则自动恢复监听。
        /// </summary>
        private static void OnAfterAssemblyReload()
        {
            if (SessionState.GetBool("UnityOpsListener_AutoRestart", false))
            {
                SessionState.SetBool("UnityOpsListener_AutoRestart", false);
                port = SessionState.GetInt("UnityOpsListener_Port", port);
                Debug.Log($"[UnityOpsListener] 脚本重新编译完成，自动恢复服务器，端口: {port}");
                StartServer();
            }
        }

        private static void OnEditorQuitting()
        {
            if (isRunning)
            {
                Debug.Log("[UnityOpsListener] Unity 即将退出，强制停止服务器...");
                StopServer();
            }
        }

        [MenuItem("Tools/UnityOpsListener")]
        public static void ShowWindow()
        {
            GetWindow<UnityOpsListener>("House Service Listener");
        }

        private void OnGUI()
        {
            GUILayout.Label("服务监听器", EditorStyles.boldLabel);
            GUILayout.Space(10);

            EditorGUILayout.BeginHorizontal();
            GUILayout.Label("端口:", GUILayout.Width(50));
            port = EditorGUILayout.IntField(port, GUILayout.Width(100));
            EditorGUILayout.EndHorizontal();

            GUILayout.Space(10);

            if (!isRunning)
            {
                if (GUILayout.Button("启动服务器", GUILayout.Height(30)))
                    StartServer();
            }
            else
            {
                if (GUILayout.Button("停止服务器", GUILayout.Height(30)))
                    StopServer();
            }

            GUILayout.Space(10);
            EditorGUILayout.HelpBox($"状态: {statusMessage}", MessageType.Info);
        }

        // ──────────────────────────────────────────────
        // 服务器生命周期
        // ──────────────────────────────────────────────

        private static void StartServer()
        {
            // 幂等保护：若已在运行则直接返回
            if (isRunning && tcpListener != null)
                return;

            try
            {
                tcpListener = new TcpListener(IPAddress.Any, port);
                listenerThread = new Thread(new ThreadStart(ListenForClients));
                listenerThread.IsBackground = true;
                listenerThread.Start();
                isRunning = true;
                statusMessage = $"服务器运行中，监听端口 {port}";
                Debug.Log($"[UnityOpsListener] 服务器启动成功，端口: {port}");
            }
            catch (SocketException) when (SessionState.GetBool("UnityOpsListener_AutoRestart", false))
            {
                // 命令行 -startServer 启动场景：static 构造函数已抢先绑定端口，
                // OnAfterAssemblyReload() 的重复 StartServer() 会触发此异常，忽略即可
                SessionState.SetBool("UnityOpsListener_AutoRestart", false);
                isRunning = true;  // 标记为运行中（端口实际已由 static ctor 绑定）
                statusMessage = $"服务器运行中，监听端口 {port}（由 static ctor 启动）";
                Debug.Log($"[UnityOpsListener] 端口 {port} 已被 static 构造函数抢占，跳过重复启动");
            }
            catch (Exception e)
            {
                statusMessage = $"启动失败: {e.Message}";
                Debug.LogError($"[UnityOpsListener] 启动失败: {e}");
            }
        }

        private static void StopServer()
        {
            try
            {
                isRunning = false;

                // 先停止 TcpListener，这会让 AcceptTcpClient() 抛出异常，使监听线程得以退出
                tcpListener?.Stop();
                tcpListener = null;

                if (listenerThread != null && listenerThread.IsAlive)
                {
                    listenerThread.Interrupt();          // 温和中断（替代已弃用的 Abort）
                    listenerThread.Join(2000);           // 最多等 2 秒
                                                         // 若仍未结束，放弃等待（IsBackground=true，进程退出时会被 OS 清理）
                    if (listenerThread.IsAlive)
                        Debug.LogWarning("[UnityOpsListener] 监听线程未在 2s 内退出，已放弃等待");
                    listenerThread = null;
                }

                statusMessage = "服务器已停止";
                Debug.Log("[UnityOpsListener] 服务器已停止");
            }
            catch (Exception e)
            {
                statusMessage = $"停止失败: {e.Message}";
                Debug.LogError($"[UnityOpsListener] 停止失败: {e}");
            }
        }

        // ──────────────────────────────────────────────
        // 网络线程
        // ──────────────────────────────────────────────

        private static void ListenForClients()
        {
            tcpListener.Start();
            Debug.Log("[UnityOpsListener] 开始监听客户端连接...");

            while (isRunning)
            {
                try
                {
                    TcpClient client = tcpListener.AcceptTcpClient();
                    var t = new Thread(HandleClientComm) { IsBackground = true };
                    t.Start(client);
                }
                catch (ThreadInterruptedException)
                {
                    // StopServer() 通过 Interrupt() 主动中断，正常退出
                    break;
                }
                catch (SocketException)
                {
                    // TcpListener.Stop() 被调用时（如编译前关闭、手动停止），AcceptTcpClient 会抛出 SocketException
                    // 这是正常退出路径，不视为错误
                }
                catch (ObjectDisposedException)
                {
                    // TcpListener 被释放后触发（与 SocketException 常伴生），正常退出
                }
                catch (Exception e) when (isRunning)
                {
                    Debug.LogError($"[UnityOpsListener] 监听异常: {e}");
                }
            }

            Debug.Log("[UnityOpsListener] 监听线程已退出");
        }

        private static void HandleClientComm(object clientObj)
        {
            TcpClient client = (TcpClient)clientObj;
            NetworkStream stream = client.GetStream();
            byte[] buffer = new byte[8192];
            int bytesRead;

            try
            {
                while ((bytesRead = stream.Read(buffer, 0, buffer.Length)) != 0)
                {
                    string jsonMessage = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                    Debug.Log($"[UnityOpsListener] 收到消息: {jsonMessage}");

                    // 把命令投入队列，由主线程的 Update() 消费
                    var pending = new PendingCommand { json = jsonMessage, done = false };
                    lock (queueLock)
                    {
                        pendingCommands.Enqueue(pending);
                        queueHasNewCommand = true;  // 标记有新命令，Update() 中会调用 QueuePlayerLoopUpdate
                    }

                    // 等待主线程处理（最多 5 秒）
                    var sw = System.Diagnostics.Stopwatch.StartNew();
                    while (!pending.done && sw.ElapsedMilliseconds < 5000)
                        Thread.Sleep(50);

                    string resultResponse = pending.done
                        ? pending.result
                        : "{\"status\":\"error\",\"message\":\"main thread timeout\"}";

                    byte[] responseData = Encoding.UTF8.GetBytes(resultResponse);
                    stream.Write(responseData, 0, responseData.Length);
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[UnityOpsListener] 客户端通信异常: {e}");
            }
            finally
            {
                stream.Close();
                client.Close();
            }
        }

        /// <summary>
        /// 通过 action（格式 "ClassName.MethodName"）解析出目标类型和方法。
        /// 直接从静态构造函数中预构建的缓存字典查找 Type。
        /// </summary>
        private static (Type targetType, MethodInfo method) ResolveAction(string action)
        {
            int dotIdx = action.IndexOf('.');
            if (dotIdx < 0)
                return (null, null);

            string className = action.Substring(0, dotIdx).Trim();
            string methodName = action.Substring(dotIdx + 1).Trim();

            if (string.IsNullOrEmpty(className) || string.IsNullOrEmpty(methodName))
                return (null, null);

            // 从缓存中按类名查找 Type（忽略大小写，由 StringComparer.OrdinalIgnoreCase 保证）
            if (_typeCache.TryGetValue(className, out Type targetType))
            {
                MethodInfo method = FindMethod(targetType, methodName);
                if (method != null)
                    return (targetType, method);
            }

            return (null, null);
        }

        private static string ProcessMessage(string jsonMessage)
        {
            try
            {
                // ── 第一阶段：仅解析 action 和 param 两个字段 ──
                ModelCommand command = JsonUtility.FromJson<ModelCommand>(jsonMessage);

                if (string.IsNullOrEmpty(command.action))
                    return "{\"status\":\"error\",\"message\":\"action is required\"}";

                // ── 第二阶段：通过反射解析 ClassName.MethodName 并调用 ──
                var (targetType, method) = ResolveAction(command.action);
                if (method == null)
                {
                    string msg = $"未知 action: {command.action}（格式应为 ClassName.MethodName）";
                    Debug.LogWarning($"[UnityOpsListener] {msg}");
                    return $"{{\"status\":\"error\",\"message\":\"{msg}\"}}";
                }

                object result;
                ParameterInfo[] parameters = method.GetParameters();
                if (parameters.Length > 0)
                    result = method.Invoke(null, new object[] { jsonMessage });
                else
                    result = method.Invoke(null, null);

                return result as string ?? "{\"status\":\"success\"}";
            }
            catch (Exception e)
            {
                Debug.LogError($"[UnityOpsListener] 解析消息失败: {e}\n消息内容: {jsonMessage}");
                return $"{{\"status\":\"error\",\"message\":\"{EscapeJson(e.Message)}\"}}";
            }
        }

        /// <summary>
        /// 通过反射在指定类型中查找方法，支持 action 到方法名的映射。
        /// 优先精确匹配，其次忽略大小写匹配。
        /// </summary>
        private static MethodInfo FindMethod(Type targetType, string action)
        {
            // 优先精确匹配
            MethodInfo method = targetType.GetMethod(action,
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
            if (method != null) return method;

            // 忽略大小写匹配
            foreach (MethodInfo m in targetType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static))
            {
                if (string.Equals(m.Name, action, StringComparison.OrdinalIgnoreCase))
                    return m;
            }

            return null;
        }

        // ──────────────────────────────────────────────
        // 工具方法
        // ──────────────────────────────────────────────
        private static string EscapeJson(string s)
        {
            return s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\r", "");
        }

        private static void Update()
        {
            // 消费后台线程投入的命令队列（主线程执行，Unity API 安全）
            lock (queueLock)
            {
                if (queueHasNewCommand)
                {
                    queueHasNewCommand = false;
                    EditorApplication.QueuePlayerLoopUpdate();
                }

                while (pendingCommands.Count > 0)
                {
                    var cmd = pendingCommands.Dequeue();
                    try
                    {
                        cmd.result = ProcessMessage(cmd.json);
                    }
                    catch (Exception e)
                    {
                        cmd.result = $"{{\"status\":\"error\",\"message\":\"{EscapeJson(e.Message)}\"}}";
                    }
                    cmd.done = true;
                }
            }
        }

        private void OnDestroy()
        {
            StopServer();
        }
    }

    // ──────────────────────────────────────────────
    // 数据结构（两段式解析）
    // 第一阶段：仅解析 action + param（param 为原始字符串）
    // 第二阶段：根据 action 将 param 反序列化为对应的具体参数类
    // ──────────────────────────────────────────────

    /// <summary>第一阶段解析：所有命令的通用结构，仅含 action 和 param</summary>
    [Serializable]
    public class ModelCommand
    {
        public string action;
    }

    /// <summary>Transform 公共接口：含 name/position/rotation/scale，用于 ApplyTransform</summary>
    public interface ITransformParam
    {
        string name { get; }
        Vector3Data position { get; }
        Vector3Data rotation { get; }
        Vector3Data scale { get; }
    }

    [Serializable]
    public class Vector3Data
    {
        public float x;
        public float y;
        public float z;
    }

    /// <summary>
    /// 标记方法/类，提供标题和 Markdown 格式的描述文档，供外部工具/文档生成器读取。
    /// </summary>
    [AttributeUsage(AttributeTargets.Method | AttributeTargets.Class, AllowMultiple = false, Inherited = false)]
    public class OpsMarkdownAttribute : Attribute
    {
        public string Title { get; }
        public string Description { get; }

        public OpsMarkdownAttribute(string title, string description)
        {
            Title = title;
            Description = description;
        }
    }
}