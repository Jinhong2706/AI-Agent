using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

/// <summary>
/// 核心操作模块：合并场景操作、模型操作、截图功能
/// 提供 SaveScene/NewScene/LoadScene、CreateModel/DeleteObject/PlaceAsset、CaptureScreenshot 等功能
/// </summary>

namespace UnityOps
{
    [OpsMarkdown("核心操作模块", "提供场景管理（新建/保存/加载）、模型操作（创建/删除/放置资产）、截图渲染等核心功能。")]
    public static class CoreOperations
    {
        [Serializable]
        public class ManualParam
        {
            public string action;
            public bool full;
        }

        // ══════════════════════════════════════════
        //  场景操作参数
        // ══════════════════════════════════════════

        /// <summary>save_scene / load_scene 命令参数</summary>
        [Serializable]
        public class SceneParam
        {
            public string action;
            public string scene_name;
        }

        // ══════════════════════════════════════════
        //  模型操作参数
        // ══════════════════════════════════════════

        /// <summary>create 命令参数</summary>
        [Serializable]
        public class CreateParam : ITransformParam
        {
            public string action;
            public string type;
            public string name;
            public Vector3Data position;
            public Vector3Data rotation;
            public Vector3Data scale;

            // ITransformParam 接口实现（属性）
            string ITransformParam.name => name;
            Vector3Data ITransformParam.position => position;
            Vector3Data ITransformParam.rotation => rotation;
            Vector3Data ITransformParam.scale => scale;
        }

        /// <summary>delete 命令参数</summary>
        [Serializable]
        public class DeleteParam
        {
            public string action;
            public string name;
            public bool delete_children;
        }

        /// <summary>place_asset 命令参数</summary>
        [Serializable]
        public class PlaceAssetParam : ITransformParam
        {
            public string action;
            public string asset_path;
            public string name;
            public Vector3Data position;
            public Vector3Data rotation;
            public Vector3Data scale;

            // ITransformParam 接口实现（属性）
            string ITransformParam.name => name;
            Vector3Data ITransformParam.position => position;
            Vector3Data ITransformParam.rotation => rotation;
            Vector3Data ITransformParam.scale => scale;
        }

        // ══════════════════════════════════════════
        //  截图操作参数
        // ══════════════════════════════════════════

        /// <summary>capture_screenshot 命令参数</summary>
        [Serializable]
        public class ScreenshotParam
        {
            public string action;
            public string angle_preset;
            public string output_path;
            public int screenshot_width;
            public int screenshot_height;
            public float fov;
            public Vector3Data camera_target;
            public Vector3Data camera_position;  // 手动相机位置（语义更清晰）
            public Vector3Data position;          // 通用 position 备用
        }

        /// <summary>刷新资产数据库</summary>
        [OpsMarkdown("RefreshAssets/刷新", "**功能**: 刷新 Unity 资产数据库，重新导入修改过的资源文件。\n\n**参数**: 无\n\n**返回值**: JSON `{status, message}`")]
        private static string RefreshAssets()
        {
            AssetDatabase.Refresh();
            Debug.Log("[UnityOpsListener] AssetDatabase.Refresh() 完成");
            return "{\"status\":\"success\",\"message\":\"assets refreshed\"}";
        }

        /// <summary>
        /// 查询手册：收集所有带 [OpsMarkdown] 属性的方法和类，以 Markdown 格式返回。
        /// 调用方式: action = "UnityOpsListener.Manual"
        /// </summary>
        [OpsMarkdown("Manual/手册", "**功能**: 查询所有可用命令的手册文档，返回 Markdown 格式的完整 API 文档。\n\n**参数**: 可选 mode 字符串，\"full\" 输出完整手册含模块概览；无参或其它值则输出精简版。\n\n**返回值**: JSON `{status, manual}` 其中 manual 为 Markdown 格式字符串")]
        public static string Manual(string paramJson)
        {
            var param = JsonUtility.FromJson<ManualParam>(paramJson ?? "{}");
            var sb = new System.Text.StringBuilder();
            sb.AppendLine($"# UnityOps API 手册{Environment.NewLine}{Environment.NewLine}" +
                $"生成时间: {DateTime.Now:yyyy-MM-dd HH:mm:ss}{Environment.NewLine}");

            var asm = Assembly.GetExecutingAssembly();
            
            // 按类分组收集
            var classDocs = new System.Collections.Generic.List<(string className, string title, string description)>();
            var methodDocs = new System.Collections.Generic.List<(string className, string methodName, string title, string description)>();

            foreach (Type type in asm.GetTypes())
            {
                // 收集类的 OpsMarkdown
                var classAttr = type.GetCustomAttribute<OpsMarkdownAttribute>();
                if (classAttr != null)
                    classDocs.Add((type.Name, classAttr.Title, classAttr.Description));

                // 收集方法的 OpsMarkdown
                foreach (MethodInfo method in type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static))
                {
                    var methodAttr = method.GetCustomAttribute<OpsMarkdownAttribute>();
                    if (methodAttr != null)
                        methodDocs.Add((type.Name, method.Name, methodAttr.Title, methodAttr.Description));
                }
            }

            // 输出模块概览（仅 full 模式）
            if (param.full && classDocs.Count > 0)
            {
                sb.AppendLine("## 模块概览");
                sb.AppendLine();
                foreach (var (className, title, desc) in classDocs)
                {
                    sb.AppendLine($"### {title} (`{className}`)");
                    sb.AppendLine(desc);
                    sb.AppendLine();
                }
            }

            // 输出命令详情
            if (methodDocs.Count > 0)
            {
                if (param.full)
                {
                    sb.AppendLine("---");
                    sb.AppendLine();
                    sb.AppendLine("## 命令详情");
                    sb.AppendLine();
                }

                // 按 action 分组显示
                foreach (var (className, methodName, title, desc) in methodDocs)
                {
                    if (param.full)
                        sb.AppendLine($"### {title}");
                    else
                        sb.AppendLine($"## {title}");

                    sb.AppendLine($"**action**: `{className}.{methodName}`");
                    sb.AppendLine();

                    sb.AppendLine(desc);
                    sb.AppendLine();

                    if (param.full)
                    {
                        sb.AppendLine("---");
                        sb.AppendLine();
                    }
                }
            }

            string markdown = sb.ToString();
            Debug.Log($"[UnityOpsListener] Manual 返回手册，共 {methodDocs.Count} 个命令");
            return $"{{\"status\":\"success\",\"manual\":\"{EscapeJson(markdown)}\"}}";
        }

        // ══════════════════════════════════════════
        //  场景操作方法
        // ══════════════════════════════════════════

        /// <summary>保存当前场景；若未命名则自动生成名字</summary>
        [OpsMarkdown("SaveScene/保存场景", "**功能**: 保存当前活动场景，未命名时自动生成名称并保存到 `Assets/Scenes/`。\n\n**参数** (`SceneParam` JSON):\n| 字段 | 类型 | 必填 | 默认值 | 说明 |\n|------|------|------|--------|------|\n| `scene_name` | string | 否 | 自动生成 | 场景名称（仅未命名场景时使用） |\n\n**返回值**: JSON `{status, path}`")]
        public static string SaveScene(string paramJson)
        {
            var param = JsonUtility.FromJson<SceneParam>(paramJson ?? "{}");
            var scene = EditorSceneManager.GetActiveScene();
            string savePath = scene.path;

            if (string.IsNullOrEmpty(savePath))
            {
                // 未命名场景，分配一个名字
                if (string.IsNullOrEmpty(param.scene_name))
                    param.scene_name = "Scene_" + DateTime.Now.ToString("yyyyMMdd_HHmmss");

                // 确保 Scenes 目录存在
                string dir = "Assets/Scenes";
                if (!AssetDatabase.IsValidFolder(dir))
                    AssetDatabase.CreateFolder("Assets", "Scenes");

                savePath = $"{dir}/{param.scene_name}.unity";
            }

            bool ok = EditorSceneManager.SaveScene(scene, savePath);
            if (ok)
            {
                Debug.Log($"[CoreOperations] 场景已保存: {savePath}");
                return $"{{\"status\":\"success\",\"path\":\"{savePath}\"}}";
            }
            else
            {
                Debug.LogError("[CoreOperations] 保存场景失败");
                return "{\"status\":\"error\",\"message\":\"save scene failed\"}";
            }
        }

        /// <summary>新建场景（会提示用户保存当前场景）</summary>
        [OpsMarkdown("NewScene/新建场景", "**功能**: 创建一个包含默认游戏对象（Directional Light, Camera）的新场景。\n\n**参数**: 无\n\n**返回值**: JSON `{status, message}`")]
        public static string NewScene()
        {
            var newScene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            Debug.Log("[CoreOperations] 新建场景完成");
            return "{\"status\":\"success\",\"message\":\"new scene created\"}";
        }

        /// <summary>
        /// 根据场景名或路径加载场景。
        /// paramJson 中 scene_name 支持：
        ///   - 场景名（不含扩展名），如 "SampleScene"  → 在 AssetDatabase 中搜索
        ///   - Assets 相对路径，如 "Assets/Scenes/SampleScene.unity"
        /// </summary>
        [OpsMarkdown("LoadScene/加载场景", "**功能**: 按名称或路径加载场景。支持模糊匹配和精确匹配。\n\n**参数** (`SceneParam` JSON):\n| 字段 | 类型 | 必填 | 默认值 | 说明 |\n|------|------|------|--------|------|\n| `scene_name` | string | **是** | - | 场景名（如 `SampleScene`）或路径（如 `Assets/Scenes/SampleScene.unity`） |\n\n**返回值**: JSON `{status, path}`")]
        public static string LoadScene(string paramJson)
        {
            var param = JsonUtility.FromJson<SceneParam>(paramJson ?? "{}");
            if (string.IsNullOrEmpty(param.scene_name))
                return "{\"status\":\"error\",\"message\":\"scene_name is required\"}";

            string scenePath = param.scene_name;

            // 如果不是以 Assets/ 开头，则在 AssetDatabase 中按名字查找
            if (!scenePath.StartsWith("Assets/", StringComparison.OrdinalIgnoreCase))
            {
                // 确保有 .unity 后缀再搜索
                string searchName = scenePath.EndsWith(".unity") ? scenePath : scenePath + ".unity";
                string[] guids = AssetDatabase.FindAssets($"t:Scene {System.IO.Path.GetFileNameWithoutExtension(searchName)}");
                if (guids.Length == 0)
                {
                    string err = $"找不到场景: {param.scene_name}";
                    Debug.LogError($"[CoreOperations] {err}");
                    return $"{{\"status\":\"error\",\"message\":\"{EscapeJson(err)}\"}}";
                }
                // 精确匹配文件名（防止 "Room" 匹配到 "BedRoom"）
                scenePath = null;
                foreach (var guid in guids)
                {
                    string p = AssetDatabase.GUIDToAssetPath(guid);
                    if (System.IO.Path.GetFileNameWithoutExtension(p).Equals(
                            System.IO.Path.GetFileNameWithoutExtension(searchName),
                            StringComparison.OrdinalIgnoreCase))
                    {
                        scenePath = p;
                        break;
                    }
                }
                // 没有精确匹配则取第一个
                if (scenePath == null)
                    scenePath = AssetDatabase.GUIDToAssetPath(guids[0]);
            }

            // 补全 .unity 后缀
            if (!scenePath.EndsWith(".unity"))
                scenePath += ".unity";

            if (!System.IO.File.Exists(System.IO.Path.GetFullPath(
                    System.IO.Path.Combine(Application.dataPath + "/..", scenePath))))
            {
                string err = $"场景文件不存在: {scenePath}";
                Debug.LogError($"[CoreOperations] {err}");
                return $"{{\"status\":\"error\",\"message\":\"{EscapeJson(err)}\"}}";
            }

            EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
            Debug.Log($"[CoreOperations] 场景已加载: {scenePath}");
            return $"{{\"status\":\"success\",\"path\":\"{EscapeJson(scenePath)}\"}}";
        }

        // ══════════════════════════════════════════
        //  模型操作方法
        // ══════════════════════════════════════════

        /// <summary>创建基本几何体</summary>
        [OpsMarkdown("CreateModel/创建模型", "**功能**: 在场景中创建基本几何体（Cube/Sphere/Cylinder/Capsule/Plane）。\n\n**参数** (`CreateParam` JSON):\n| 字段 | 类型 | 必填 | 默认值 | 说明 |\n|------|------|------|--------|------|\n| `type` | string | **是** | - | 几何体类型: `Cube`, `Sphere`, `Cylinder`, `Capsule`, `Plane` |\n| `name` | string | 否 | Unity 默认 | 对象名称 |\n| `position` | Vector3Data | 否 | (0,0,0) | 世界坐标位置 |\n| `rotation` | Vector3Data | 否 | (0,0,0) | 欧拉角旋转（度） |\n| `scale` | Vector3Data | 否 | (1,1,1) | 缩放比例 |\n\n**返回值**: JSON `{status, name}`")]
        public static string CreateModel(string paramJson)
        {
            var command = JsonUtility.FromJson<CreateParam>(paramJson ?? "{}");
            var primMap = new Dictionary<string, PrimitiveType>
            {
                ["Cube"] = PrimitiveType.Cube,
                ["Sphere"] = PrimitiveType.Sphere,
                ["Cylinder"] = PrimitiveType.Cylinder,
                ["Capsule"] = PrimitiveType.Capsule,
                ["Plane"] = PrimitiveType.Plane
            };
            if (!primMap.TryGetValue(command.type, out var primType))
            {
                string err = $"不支持的类型: {command.type}";
                Debug.LogError($"[CoreOperations] {err}");
                return $"{{\"status\":\"error\",\"message\":\"{err}\"}}";
            }
            GameObject obj = GameObject.CreatePrimitive(primType);

            ApplyTransform(obj, command);
            Undo.RegisterCreatedObjectUndo(obj, "Create Model from Network");
            Debug.Log($"[CoreOperations] 创建成功: {command.type} - {obj.name}");
            return $"{{\"status\":\"success\",\"name\":\"{obj.name}\"}}";
        }

        /// <summary>按名字删除场景中的 GameObject</summary>
        [OpsMarkdown("DeleteObject/删除物体", "**功能**: 按名称删除场景中的 GameObject（支持同名多对象批量删除）。\n\n**参数** (`DeleteParam` JSON):\n| 字段 | 类型 | 必填 | 默认值 | 说明 |\n|------|------|------|--------|------|\n| `name` | string | **是** | - | 要删除的对象名称 |\n| `delete_children` | bool | 否 | false | 是否额外拆解子节点（Undo 粒度控制） |\n\n**返回值**: JSON `{status, name, deleted}`")]
        public static string DeleteObject(string paramJson)
        {
            var command = JsonUtility.FromJson<DeleteParam>(paramJson ?? "{}");
            if (string.IsNullOrEmpty(command.name))
                return "{\"status\":\"error\",\"message\":\"name is required for delete\"}";

            // 查找场景中所有同名对象
            var allObjects = UnityEngine.Object.FindObjectsOfType<GameObject>();
            var targets = new System.Collections.Generic.List<GameObject>();
            foreach (var go in allObjects)
            {
                if (go.name == command.name)
                    targets.Add(go);
            }

            if (targets.Count == 0)
            {
                string err = $"找不到名为 '{command.name}' 的 GameObject";
                Debug.LogWarning($"[CoreOperations] {err}");
                return $"{{\"status\":\"error\",\"message\":\"{EscapeJson(err)}\"}}";
            }

            int deleted = 0;
            foreach (var go in targets)
            {
                // 如果 delete_children=false（默认），只删顶层对象（含其子节点，DestroyImmediate 会级联）
                // 如果 delete_children=true，额外先拆解子节点让它们也被记入 Undo
                Undo.DestroyObjectImmediate(go);
                deleted++;
            }

            Debug.Log($"[CoreOperations] 删除成功: '{command.name}' x{deleted}");
            return $"{{\"status\":\"success\",\"name\":\"{EscapeJson(command.name)}\",\"deleted\":{deleted}}}";
        }

        /// <summary>根据资产路径（FBX/Prefab）实例化并摆放到场景</summary>
        [OpsMarkdown("PlaceAsset/放置资产", "**功能**: 根据资产路径（FBX/Prefab）加载并实例化到场景中。\n\n**参数** (`PlaceAssetParam` JSON):\n| 字段 | 类型 | 必填 | 默认值 | 说明 |\n|------|------|------|--------|------|\n| `asset_path` | string | **是** | - | 资产路径（支持 `Assets/...` 相对路径或绝对路径） |\n| `name` | string | 否 | 原资产名 | 实例化后的对象名称 |\n| `position` | Vector3Data | 否 | (0,0,0) | 世界坐标位置 |\n| `rotation` | Vector3Data | 否 | (0,0,0) | 欧拉角旋转（度） |\n| `scale` | Vector3Data | 否 | (1,1,1) | 缩放比例 |\n\n**返回值**: JSON `{status, name}`")]
        public static string PlaceAsset(string paramJson)
        {
            var command = JsonUtility.FromJson<PlaceAssetParam>(paramJson ?? "{}");
            if (string.IsNullOrEmpty(command.asset_path))
                return "{\"status\":\"error\",\"message\":\"asset_path is required\"}";

            // 支持绝对路径或 Assets/ 相对路径
            string assetPath = command.asset_path;

            // 如果是绝对路径，尝试转换为项目相对路径
            if (Path.IsPathRooted(assetPath))
            {
                string projectRoot = Path.GetFullPath(Application.dataPath + "/..");
                if (assetPath.StartsWith(projectRoot))
                    assetPath = "Assets" + assetPath.Substring(projectRoot.Length).Replace('\\', '/');
            }

            UnityEngine.Object asset = AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(assetPath);
            if (asset == null)
            {
                string err = $"资产加载失败，路径不存在或无效: {assetPath}";
                Debug.LogError($"[CoreOperations] {err}");
                return $"{{\"status\":\"error\",\"message\":\"{EscapeJson(err)}\"}}";
            }

            GameObject instance = null;

            // Prefab
            if (asset is GameObject prefab)
            {
                instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            }
            else
            {
                // FBX 等：取第一个 GameObject 子资产
                UnityEngine.Object[] subAssets = AssetDatabase.LoadAllAssetsAtPath(assetPath);
                foreach (var sub in subAssets)
                {
                    if (sub is GameObject go)
                    {
                        instance = (GameObject)PrefabUtility.InstantiatePrefab(go);
                        break;
                    }
                }
            }

            if (instance == null)
            {
                string err = $"无法从资产创建 GameObject: {assetPath}";
                Debug.LogError($"[CoreOperations] {err}");
                return $"{{\"status\":\"error\",\"message\":\"{EscapeJson(err)}\"}}";
            }

            ApplyTransform(instance, command);
            Undo.RegisterCreatedObjectUndo(instance, "Place Asset from Network");
            Debug.Log($"[CoreOperations] 放置资产成功: {assetPath} -> {instance.name}");
            return $"{{\"status\":\"success\",\"name\":\"{instance.name}\"}}";
        }

        // ══════════════════════════════════════════
        //  截图操作方法
        // ══════════════════════════════════════════

        /// <summary>
        /// 自动计算合适视角后截图，保存为 PNG 并返回绝对路径。
        /// 支持可选的 angle_preset（iso/top/front）和手动 camera_position/camera_target/fov。
        /// 版本兼容：
        ///   Unity 2019.1+  → SceneView.lastActiveSceneView（已稳定）
        ///   Unity 2020.1+  → SceneView.lastActiveSceneView.camera（公开只读）
        ///   Unity 2022+    → 同上，无 API 差异，编译宏主要用于 RenderTexture 格式
        /// </summary>
        [OpsMarkdown("CaptureScreenshot/截屏", "**功能**: 自动计算合适视角后截图，保存为 PNG 并返回绝对路径。\n\n**参数** (`ScreenshotParam` JSON):\n| 字段 | 类型 | 必填 | 默认值 | 说明 |\n|------|------|------|--------|------|\n| `angle_preset` | string | 否 | \"iso\" | 视角预设: `iso`(等距), `top`(俯视), `front`(正视) |\n| `output_path` | string | 否 | auto | 输出路径，默认 `../Screenshots/screenshot_时间戳.png` |\n| `screenshot_width` | int | 否 | 1920 | 图片宽度 |\n| `screenshot_height` | int | 否 | 1080 | 图片高度 |\n| `fov` | float | 否 | 60 | 相机视场角 |\n| `camera_position` | Vector3Data | 否 | auto | 手动指定相机位置 |\n| `camera_target` | Vector3Data | 否 | bounds center | 手动指定相机目标点 |\n\n**返回值**: JSON (status, path, width, height, camera_position, camera_target, fov, bounds_center, bounds_size)")]
        public static string CaptureScreenshot(string paramJson)
        {
            var command = JsonUtility.FromJson<ScreenshotParam>(paramJson ?? "{}");
            try
            {
                // ── 1. 计算场景包围盒 ──────────────────────────
                Bounds sceneBounds = new Bounds(Vector3.zero, Vector3.zero);
                bool boundsInitialized = false;
                foreach (var renderer in UnityEngine.Object.FindObjectsOfType<Renderer>())
                {
                    // 跳过隐藏物体
                    if (!renderer.gameObject.activeInHierarchy) continue;
                    if (!boundsInitialized) { sceneBounds = renderer.bounds; boundsInitialized = true; }
                    else sceneBounds.Encapsulate(renderer.bounds);
                }
                if (!boundsInitialized)
                    return "{\"status\":\"error\",\"message\":\"场景中没有可见物体，无法截图\"}";

                Vector3 center = sceneBounds.center;
                float diagonal = sceneBounds.extents.magnitude * 2f;
                float distance = Mathf.Max(diagonal * 1.5f, 1f);

                // ── 2. 计算相机位置 ────────────────────────────
                Vector3 camPos;
                Vector3 camTarget = center;
                float fov = command.fov > 0 ? command.fov : 60f;

                if (command.camera_position != null)
                {
                    // 手动指定（重拍微调时使用）
                    camPos = new Vector3(command.camera_position.x,
                                         command.camera_position.y,
                                         command.camera_position.z);
                    if (command.camera_target != null)
                        camTarget = new Vector3(command.camera_target.x,
                                                command.camera_target.y,
                                                command.camera_target.z);
                }
                else
                {
                    // 自动计算：根据 angle_preset 选择方向向量
                    string preset = string.IsNullOrEmpty(command.angle_preset)
                        ? "iso" : command.angle_preset.ToLower();

                    Vector3 dir;
                    switch (preset)
                    {
                        case "top":
                            dir = new Vector3(0f, 1f, 0f);
                            break;
                        case "front":
                            dir = new Vector3(0f, 0f, -1f);
                            break;
                        case "iso":
                        default:
                            // 经典3/4等距视角：水平45°，俯仰35°
                            dir = new Vector3(1f, Mathf.Tan(35f * Mathf.Deg2Rad), -1f).normalized;
                            break;
                    }
                    camPos = center + dir * distance;
                }

                // ── 3. 分辨率 ──────────────────────────────────
                int width = command.screenshot_width > 0 ? command.screenshot_width : 1920;
                int height = command.screenshot_height > 0 ? command.screenshot_height : 1080;

                // ── 4. 输出路径 ────────────────────────────────
                string outputPath = command.output_path;
                if (string.IsNullOrEmpty(outputPath))
                {
                    string screenshotsDir = Path.GetFullPath(
                        Path.Combine(Application.dataPath, "..", "Screenshots"));
                    Directory.CreateDirectory(screenshotsDir);
                    outputPath = Path.Combine(screenshotsDir,
                        "screenshot_" + DateTime.Now.ToString("yyyyMMdd_HHmmss") + ".png");
                }

                // ── 5. 构建临时相机并离屏渲染 ─────────────────
                GameObject camGO = new GameObject("__HouseScreenshotCamera__");
                Camera cam = camGO.AddComponent<Camera>();
                cam.fieldOfView = fov;
                cam.nearClipPlane = 0.01f;
                cam.farClipPlane = distance * 10f;
                cam.backgroundColor = new Color(0.2f, 0.2f, 0.2f, 1f);
                cam.clearFlags = CameraClearFlags.SolidColor;

                camGO.transform.position = camPos;
                camGO.transform.LookAt(camTarget);

#if UNITY_2022_1_OR_NEWER
                // 2022+：GraphicsFormat 更精确，但 RenderTextureFormat.ARGB32 仍兼容
                RenderTexture rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32,
                                                     RenderTextureReadWrite.sRGB);
#elif UNITY_2019_1_OR_NEWER
            RenderTexture rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
            rt.sRGB = true;
#else
            RenderTexture rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
#endif
                rt.antiAliasing = 4;
                rt.Create();

                cam.targetTexture = rt;
                cam.Render();

                // 读取像素
                RenderTexture.active = rt;
                Texture2D tex = new Texture2D(width, height, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                tex.Apply();
                RenderTexture.active = null;

                // 写文件
                byte[] pngBytes = tex.EncodeToPNG();
                File.WriteAllBytes(outputPath, pngBytes);

                // 清理
                cam.targetTexture = null;
                UnityEngine.Object.DestroyImmediate(tex);
                rt.Release();
                UnityEngine.Object.DestroyImmediate(rt);
                UnityEngine.Object.DestroyImmediate(camGO);

                Debug.Log($"[CoreOperations] 截图保存: {outputPath}");

                // ── 6. 返回结果（含相机参数，供重拍微调参考） ──
                return "{\"status\":\"success\"" +
                       ",\"path\":\"" + EscapeJson(outputPath) + "\"" +
                       ",\"width\":" + width + ",\"height\":" + height +
                       ",\"bounds_center\":{\"x\":" + center.x.ToString("F3") + ",\"y\":" + center.y.ToString("F3") + ",\"z\":" + center.z.ToString("F3") + "}" +
                       ",\"bounds_size\":{\"x\":" + sceneBounds.size.x.ToString("F3") + ",\"y\":" + sceneBounds.size.y.ToString("F3") + ",\"z\":" + sceneBounds.size.z.ToString("F3") + "}" +
                       ",\"camera_position\":{\"x\":" + camPos.x.ToString("F3") + ",\"y\":" + camPos.y.ToString("F3") + ",\"z\":" + camPos.z.ToString("F3") + "}" +
                       ",\"camera_target\":{\"x\":" + camTarget.x.ToString("F3") + ",\"y\":" + camTarget.y.ToString("F3") + ",\"z\":" + camTarget.z.ToString("F3") + "}" +
                       ",\"fov\":" + fov.ToString("F1") +
                       "}";
            }
            catch (Exception e)
            {
                Debug.LogError($"[CoreOperations] 截图失败: {e}");
                return $"{{\"status\":\"error\",\"message\":\"{EscapeJson(e.Message)}\"}}";
            }
        }

        // ══════════════════════════════════════════
        //  项目信息方法
        // ══════════════════════════════════════════

        /// <summary>获取当前 Unity 项目的资产路径（Assets 目录的绝对路径）</summary>
        [OpsMarkdown("GetAssetPath/获取资产路径", "**功能**: 获取当前 Unity 项目 Assets 目录的绝对路径。\n\n**参数**: 无\n\n**返回值**: JSON `{status, asset_path, project_path}` 其中 `asset_path` 为 `Application.dataPath` 的绝对路径，`project_path` 为项目根目录绝对路径")]
        public static string GetAssetPath()
        {
            string assetPath = Path.GetFullPath(Application.dataPath);
            string projectPath = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
            Debug.Log($"[CoreOperations] 资产路径: {assetPath}, 项目路径: {projectPath}");
            return $"{{\"status\":\"success\",\"asset_path\":\"{EscapeJson(assetPath)}\",\"project_path\":\"{EscapeJson(projectPath)}\"}}";
        }

        // ══════════════════════════════════════════
        //  工具方法
        // ══════════════════════════════════════════

        /// <summary>应用变换（位置、旋转、缩放）到 GameObject</summary>
        public static void ApplyTransform(GameObject obj, ITransformParam command)
        {
            if (!string.IsNullOrEmpty(command.name))
                obj.name = command.name;

            if (command.position != null)
                obj.transform.position = new Vector3(command.position.x, command.position.y, command.position.z);

            if (command.rotation != null)
                obj.transform.eulerAngles = new Vector3(command.rotation.x, command.rotation.y, command.rotation.z);

            if (command.scale != null)
                obj.transform.localScale = new Vector3(FixZero(command.scale.x), FixZero(command.scale.y), FixZero(command.scale.z));
            else
            {
                // 未指定 scale 时，检查当前 localScale 是否含 0 分量并修正
                Vector3 s = obj.transform.localScale;
                if (s.x == 0f || s.y == 0f || s.z == 0f)
                {
                    obj.transform.localScale = new Vector3(FixZero(s.x), FixZero(s.y), FixZero(s.z));
                    Debug.LogWarning($"[CoreOperations] {obj.name} 的 localScale 含零分量，已自动修正为 {obj.transform.localScale}");
                }
            }
        }

        private static float FixZero(float v) => v == 0f ? 1f : v;

        internal static string EscapeJson(string s)
        {
            return s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\r", "");
        }
    }
}
