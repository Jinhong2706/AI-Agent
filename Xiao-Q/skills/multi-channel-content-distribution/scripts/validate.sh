#!/bin/bash
# 多渠道内容分发 - 内容验证脚本
# 用途：验证各平台适配内容是否满足格式要求
# 用法：bash scripts/validate.sh <content_file>
# 返回：检查项通过/未通过的详细报告

set -euo pipefail

CONTENT_FILE="${1:-}"
if [ -z "$CONTENT_FILE" ]; then
    echo "错误：请指定内容文件路径"
    echo "用法：bash scripts/validate.sh <content_file>"
    exit 1
fi

if [ ! -f "$CONTENT_FILE" ]; then
    echo "错误：文件不存在：$CONTENT_FILE"
    exit 1
fi

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
RESULTS=()

# 辅助函数：记录检查结果
check_pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    RESULTS+=("✅ PASS | $1")
    echo "  ✅ 通过：$1"
}

check_fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    RESULTS+=("❌ FAIL | $1 | $2")
    echo "  ❌ 未通过：$1 — $2"
}

check_warn() {
    WARN_COUNT=$((WARN_COUNT + 1))
    RESULTS+=("⚠️  WARN | $1 | $2")
    echo "  ⚠️  警告：$1 — $2"
}

echo "============================================"
echo "  多渠道内容分发 - 内容格式验证"
echo "============================================"
echo "  文件：$CONTENT_FILE"
echo "  时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""

# 读取文件内容
CONTENT=$(cat "$CONTENT_FILE")
TOTAL_CHARS=$(echo -n "$CONTENT" | wc -m)
TOTAL_LINES=$(echo "$CONTENT" | wc -l)

echo "--- 检查项 1/10：平台覆盖率 ---"
# 检查是否包含至少4个平台的适配版本
PLATFORM_KEYWORDS=("微信公众号" "小红书" "抖音" "B站" "知乎" "微博")
FOUND_PLATFORMS=0
for platform in "${PLATFORM_KEYWORDS[@]}"; do
    if echo "$CONTENT" | grep -q "$platform"; then
        FOUND_PLATFORMS=$((FOUND_PLATFORMS + 1))
        echo "  发现平台：$platform"
    fi
done
if [ "$FOUND_PLATFORMS" -ge 4 ]; then
    check_pass "平台覆盖率：检测到 $FOUND_PLATFORMS 个平台版本（要求 ≥ 4）"
else
    check_fail "平台覆盖率：仅检测到 $FOUND_PLATFORMS 个平台版本（要求 ≥ 4）" "请确保内容包含至少4个平台的适配版本"
fi
echo ""

echo "--- 检查项 2/10：各平台字数限制 ---"
# 微信公众号：1500-3000字
WECHAT_CHARS=$(echo "$CONTENT" | sed -n '/微信公众号/,/小红书/p' | head -n -1 | wc -m)
if [ "$WECHAT_CHARS" -ge 1000 ] && [ "$WECHAT_CHARS" -le 3500 ]; then
    check_pass "微信公众号字数：${WECHAT_CHARS}字（范围 1000-3500）"
else
    check_warn "微信公众号字数：${WECHAT_CHARS}字（建议范围 1000-3500）" "字数可能偏多或偏少，建议调整"
fi

# 小红书：300-800字
XHS_CHARS=$(echo "$CONTENT" | sed -n '/小红书/,/抖音/p' | head -n -1 | wc -m)
if [ "$XHS_CHARS" -ge 200 ] && [ "$XHS_CHARS" -le 1000 ]; then
    check_pass "小红书字数：${XHS_CHARS}字（范围 200-1000）"
else
    check_warn "小红书字数：${XHS_CHARS}字（建议范围 200-1000）" "小红书内容建议控制在800字以内"
fi

# 抖音脚本：100-300字
DOUYIN_CHARS=$(echo "$CONTENT" | sed -n '/抖音/,/B站\|Bilibili/p' | head -n -1 | wc -m)
if [ "$DOUYIN_CHARS" -ge 50 ] && [ "$DOUYIN_CHARS" -le 500 ]; then
    check_pass "抖音脚本字数：${DOUYIN_CHARS}字（范围 50-500）"
else
    check_warn "抖音脚本字数：${DOUYIN_CHARS}字（建议范围 50-500）" "短视频脚本应更精简"
fi
echo ""

echo "--- 检查项 3/10：标签/话题使用 ---"
# 小红书标签检测（应含 # 标签）
XHS_TAG_COUNT=$(echo "$CONTENT" | sed -n '/小红书/,/抖音/p' | grep -oE '#[^#[:space:]]+' | wc -l)
if [ "$XHS_TAG_COUNT" -ge 3 ]; then
    check_pass "小红书标签数量：${XHS_TAG_COUNT}个（要求 ≥ 3）"
else
    check_fail "小红书标签数量：${XHS_TAG_COUNT}个（要求 ≥ 3）" "小红书内容应包含3-8个标签"
fi

# 微博话题标签检测
WEIBO_TAG_COUNT=$(echo "$CONTENT" | sed -n '/微博/,/$/p' | grep -oE '#[^#]+#' | wc -l)
if [ "$WEIBO_TAG_COUNT" -ge 1 ]; then
    check_pass "微博话题标签：${WEIBO_TAG_COUNT}个（要求 ≥ 1）"
else
    check_warn "微博话题标签：${WEIBO_TAG_COUNT}个（建议 ≥ 2）" "微博内容建议添加2-3个话题标签"
fi
echo ""

echo "--- 检查项 4/10：标题质量检查 ---"
# 检查是否包含推荐标题
TITLE_COUNT=$(echo "$CONTENT" | grep -cE "(推荐标题|备选标题|标题方案)" || true)
if [ "$TITLE_COUNT" -ge 1 ]; then
    check_pass "标题方案：检测到 $TITLE_COUNT 处标题标注"
else
    check_fail "标题方案：未检测到标题标注" "每个平台版本应包含2-3个备选标题"
fi

# 检查标题是否具有平台特征
XHS_TITLE=$(echo "$CONTENT" | sed -n '/小红书/,/抖音/p' | grep -iE "(推荐标题|标题)" | head -1 || true)
if echo "$XHS_TITLE" | grep -qE "[｜|！!？?]"; then
    check_pass "小红书标题风格：标题包含符号装饰（符合平台风格）"
else
    check_warn "小红书标题风格：标题缺少符号装饰" "小红书标题建议使用符号增强吸引力"
fi
echo ""

echo "--- 检查项 5/10：内容结构完整性 ---"
# 检查报告结构
REQUIRED_SECTIONS=("内容概要" "质量评估" "发布排期")
MISSING_SECTIONS=()
for section in "${REQUIRED_SECTIONS[@]}"; do
    if ! echo "$CONTENT" | grep -q "$section"; then
        MISSING_SECTIONS+=("$section")
    fi
done
if [ ${#MISSING_SECTIONS[@]} -eq 0 ]; then
    check_pass "报告结构完整性：所有必要章节均存在"
else
    check_fail "报告结构完整性：缺少章节：${MISSING_SECTIONS[*]}" "请补充缺失的必要章节"
fi
echo ""

echo "--- 检查项 6/10：配图建议检查 ---"
IMG_SUGGESTION_COUNT=$(echo "$CONTENT" | grep -cE "(配图|封面|图片)" || true)
if [ "$IMG_SUGGESTION_COUNT" -ge 2 ]; then
    check_pass "配图建议：检测到 $IMG_SUGGESTION_COUNT 处配图相关描述"
else
    check_warn "配图建议：仅检测到 $IMG_SUGGESTION_COUNT 处配图描述（建议 ≥ 2）" "建议为各版本提供配图建议"
fi
echo ""

echo "--- 检查项 7/10：敏感词基础检查 ---"
SENSITIVE_WORDS=("加微信" "加群" "私聊" "转账" "红包" "免费领取" "限时优惠")
FOUND_SENSITIVE=()
for word in "${SENSITIVE_WORDS[@]}"; do
    if echo "$CONTENT" | grep -q "$word"; then
        FOUND_SENSITIVE+=("$word")
    fi
done
if [ ${#FOUND_SENSITIVE[@]} -eq 0 ]; then
    check_pass "敏感词检查：未发现常见敏感词"
else
    check_warn "敏感词检查：发现可能敏感词：${FOUND_SENSITIVE[*]}" "建议替换或删除这些词汇以避免限流"
fi
echo ""

echo "--- 检查项 8/10：Emoji使用检查（小红书专属） ---"
XHS_EMOJI_COUNT=$(echo "$CONTENT" | sed -n '/小红书/,/抖音/p' | grep -oP '[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]' | wc -l || echo "0")
if [ "$XHS_EMOJI_COUNT" -ge 2 ]; then
    check_pass "小红书Emoji使用：检测到表情符号（符合平台风格）"
else
    check_warn "小红书Emoji使用：Emoji较少" "小红书内容建议适当使用Emoji增强视觉效果"
fi
echo ""

echo "--- 检查项 9/10：内容保真性检查 ---"
# 检查核心关键词是否在各平台版本中均有出现
CORE_KEYWORDS=$(echo "$CONTENT" | sed -n '/核心主题/,/内容类型/p' | head -1 || echo "")
if [ -n "$CORE_KEYWORDS" ]; then
    check_pass "内容保真性：已识别核心主题关键词"
else
    check_warn "内容保真性：未在概要中发现核心主题" "建议在内容概要中明确标注核心主题"
fi
echo ""

echo "--- 检查项 10/10：发布时间建议检查 ---"
TIME_SUGGESTION=$(echo "$CONTENT" | grep -cE "(发布时间|推荐时间|最佳发布)" || true)
if [ "$TIME_SUGGESTION" -ge 1 ]; then
    check_pass "发布时间建议：检测到发布时间推荐"
else
    check_warn "发布时间建议：未检测到发布时间推荐" "建议添加各平台最佳发布时间"
fi
echo ""

# 输出汇总
echo "============================================"
echo "  验证结果汇总"
echo "============================================"
echo "  ✅ 通过：$PASS_COUNT 项"
echo "  ❌ 未通过：$FAIL_COUNT 项"
echo "  ⚠️  警告：$WARN_COUNT 项"
echo "  总计：$((PASS_COUNT + FAIL_COUNT + WARN_COUNT)) 项检查"
echo "============================================"

# 输出详细结果
echo ""
echo "详细结果："
for result in "${RESULTS[@]}"; do
    echo "  $result"
done

# 返回码
if [ "$FAIL_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️  存在未通过项，请根据上述建议修改内容后重新验证"
    exit 1
else
    echo ""
    echo "🎉 所有强制检查项均已通过！"
    exit 0
fi
