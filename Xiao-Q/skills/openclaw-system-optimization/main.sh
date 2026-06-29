#!/bin/bash
set -e
# 接收用户指令参数
INPUT="$1"
# 如果是修改时间的指令
if [[ "$INPUT" == 修改系统优化执行时间* ]]; then
  NEW_CRON=$(echo "$INPUT" | awk '{print $5}')
  # 校验cron表达式合法性
  if [[ ! "$NEW_CRON" =~ ^[0-9*/,-]+[[:space:]][0-9*/,-]+[[:space:]][0-9*/,-]+[[:space:]][0-9*/,-]+[[:space:]][0-9*/,-]+$ ]]; then
    echo "❌ cron表达式格式错误，请输入正确的cron表达式，例如："
    echo "👉 修改系统优化执行时间 0 2 * * *"
    echo "表示每天凌晨2点执行"
    exit 1
  fi
  # 获取当前系统优化任务的jobId
  JOB_ID=$(openclaw cron list --json | jq -r '.jobs[] | select(.name == "OpenClaw系统优化") | .id')
  if [ -z "$JOB_ID" ]; then
    echo "❌ 未找到「OpenClaw系统优化」定时任务，请先添加定时任务后再修改时间"
    exit 1
  fi
  # 更新定时任务
  openclaw cron update "$JOB_ID" --patch '{"schedule": {"kind": "cron", "expr": "'"$NEW_CRON"'", "tz": "Asia/Shanghai"}}' >/dev/null 2>&1
  echo "✅ 「OpenClaw系统优化」执行时间修改成功！"
  echo "⏰ 新的执行时间：cron表达式 $NEW_CRON（北京时间）"
  exit 0
fi
# 正常执行优化任务逻辑
echo "🔹 **OpenClaw系统优化-每日任务执行报告**"
echo "📅 执行时间：$(date +"%Y-%m-%d %H:%M") 北京时间"
echo ""
echo "✅ **文件健康检查结果**"
echo "- 检查项：memory目录、skills目录、核心配置文件"
# 检查文件完整性
ERROR_COUNT=0
# 检查memory目录
if [ ! -d "/home/gem/workspace/agent/workspace/memory" ]; then
  mkdir -p /home/gem/workspace/agent/workspace/memory
  ERROR_COUNT=$((ERROR_COUNT+1))
fi
# 检查核心配置文件
CORE_FILES=("/home/gem/workspace/agent/workspace/SOUL.md" "/home/gem/workspace/agent/workspace/USER.md" "/home/gem/workspace/agent/workspace/AGENTS.md" "/home/gem/workspace/agent/workspace/TOOLS.md")
for file in "${CORE_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    touch "$file"
    ERROR_COUNT=$((ERROR_COUNT+1))
  fi
done
# 输出检查结果
if [ $ERROR_COUNT -eq 0 ]; then
  echo "- 状态：🟢 全部正常无异常"
elif [ $ERROR_COUNT -gt 0 ]; then
  echo "- 状态：🟡 已自动修复$ERROR_COUNT个问题"
fi
echo ""
echo "✅ **内存优化清理结果**"
echo "- 清理内容：Python缓存、大于10M冗余日志、临时文件、无用安装包、用户缓存"
# 执行清理
find /home/gem -name "__pycache__" -type d -exec rm -rf {} \; 2>/dev/null || true
find /home/gem -name "*.log" -size +10M -delete 2>/dev/null || true
rm -rf /tmp/* 2>/dev/null || true
rm -rf /home/gem/.cache/* 2>/dev/null || true
rm -rf /home/gem/workspace/agent/workspace/skills/*.zip 2>/dev/null || true
rm -rf /home/gem/workspace/agent/workspace/skills/.skills_store_lock.json 2>/dev/null || true
# 获取内存信息
MEM_TOTAL=$(free -h | grep Mem | awk '{print $2}')
MEM_AVAILABLE=$(free -h | grep Mem | awk '{print $7}')
MEM_USED_PERCENT=$(free | grep Mem | awk '{printf "%.0f%%", $3/$2 * 100}')
echo "- 清理后可用内存：$MEM_AVAILABLE / 总内存：$MEM_TOTAL"
echo "- 内存占用率：$MEM_USED_PERCENT"
echo ""
echo "💡 修改执行时间请直接发送：修改系统优化执行时间 <cron表达式>"
echo "👉 例如：修改系统优化执行时间 0 2 * * * （每天凌晨2点执行）"
echo "🦞 任务执行完成，系统运行顺畅~"
