#!/usr/bin/env python3
"""
高考志愿梯度健康度检查工具

功能：
1. 检查志愿草表的冲/稳/保比例是否合理
2. 识别高风险填报组合
3. 检测常见填报错误
4. 输出健康度评估报告

用法：
    # 通过 JSON 文件检查
    python health_check.py --input volunteer_draft.json

    # 通过命令行参数检查（简单模式）
    python health_check.py --total 10 --rush 3 --stable 4 --safe 2 --unspecified 1

JSON 输入格式：
{
    "student_rank": 30000,
    "province": "浙江",
    "subject_type": "物理类",
    "volunteers": [
        {"order": 1, "name": "南京邮电大学", "school_rank": 25000, "major": "计算机", "obey_transfer": true},
        {"order": 2, "name": "杭州电子科技大学", "school_rank": 28000, "major": "软件工程", "obey_transfer": true},
        ...
    ]
}
"""

import argparse
import json
import sys
from datetime import datetime


class HealthChecker:
    """志愿梯度健康度检查器"""

    def __init__(self, student_rank: int, province: str = "", subject_type: str = ""):
        self.student_rank = student_rank
        self.province = province
        self.subject_type = subject_type
        self.issues = []  # 收集所有问题

    def classify_tier(self, school_rank: int) -> str:
        """根据院校录取位次判断档次"""
        diff_ratio = (school_rank - self.student_rank) / self.student_rank

        if diff_ratio <= -0.05:
            return "冲刺"
        elif diff_ratio <= 0.05:
            return "稳妥"
        else:
            return "保底"

    def check_volunteers(self, volunteers: list) -> dict:
        """
        检查志愿列表，返回健康度评估结果

        Args:
            volunteers: 志愿列表，每项包含 order, name, school_rank, major, obey_transfer 等

        Returns:
            评估结果字典
        """
        self.issues = []

        if not volunteers:
            self.issues.append({
                "level": "❌",
                "category": "基础检查",
                "message": "志愿列表为空"
            })
            return self._build_result(volunteers, {})

        # 1. 分类统计
        tier_count = {"冲刺": 0, "稳妥": 0, "保底": 0, "未分类": 0}
        tier_list = {"冲刺": [], "稳妥": [], "保底": [], "未分类": []}

        for v in volunteers:
            rank = v.get("school_rank")
            if rank and rank > 0:
                tier = self.classify_tier(rank)
            else:
                tier = "未分类"

            tier_count[tier] += 1
            tier_list[tier].append(v.get("name", f"第{v.get('order', '?')}志愿"))

        total = len(volunteers)

        # 2. 比例检查
        self._check_ratio(tier_count, total)

        # 3. 排序检查（冲刺应在前，保底应在后）
        self._check_order(volunteers, tier_list)

        # 4. 不服从调剂检查
        self._check_transfer(volunteers)

        # 5. 空白志愿检查
        unspecified_count = sum(1 for v in volunteers if v.get("name") in [None, "", "-"])
        if unspecified_count > 0:
            self.issues.append({
                "level": "⚠️",
                "category": "完整度",
                "message": f"有 {unspecified_count} 个志愿未填写（共 {total} 个）"
            })

        # 6. 重复院校检查
        names = [v.get("name", "") for v in volunteers if v.get("name") not in ["", None, "-"]]
        duplicates = [n for n in set(names) if names.count(n) > 1]
        if duplicates:
            self.issues.append({
                "level": "❌",
                "category": "重复检查",
                "message": f"存在重复院校：{', '.join(duplicates)}"
            })

        # 7. 计算健康度评分
        score = self._calc_score(tier_count, total)

        return self._build_result(volunteers, tier_count, score)

    def check_simple(self, total: int, rush: int, stable: int, safe: int,
                     unspecified: int = 0) -> dict:
        """简单模式检查（仅数量，无具体院校信息）"""
        self.issues = []
        tier_count = {"冲刺": rush, "稳妥": stable, "保底": safe, "未分类": unspecified}

        self._check_ratio(tier_count, total)

        if unspecified > 0:
            self.issues.append({
                "level": "⚠️",
                "category": "完整度",
                "message": f"有 {unspecified} 个志愿未填写（共 {total} 个）"
            })

        score = self._calc_score(tier_count, total)

        return {
            "total": total,
            "tier_count": tier_count,
            "score": score,
            "issues": self.issues
        }

    def _check_ratio(self, tier_count: dict, total: int):
        """检查冲稳保比例是否合理"""
        if total == 0:
            return

        rush_ratio = tier_count["冲刺"] / total
        stable_ratio = tier_count["稳妥"] / total
        safe_ratio = tier_count["保底"] / total

        # 无保底志愿
        if tier_count["保底"] == 0:
            self.issues.append({
                "level": "❌",
                "category": "梯度比例",
                "message": "没有保底志愿，存在滑档风险！强烈建议至少填报 2 所保底院校"
            })

        # 保底过少
        elif tier_count["保底"] == 1:
            self.issues.append({
                "level": "⚠️",
                "category": "梯度比例",
                "message": "保底志愿仅有 1 所，建议增加到 2 所以上"
            })

        # 冲刺过多
        if rush_ratio > 0.5:
            self.issues.append({
                "level": "⚠️",
                "category": "梯度比例",
                "message": f"冲刺志愿占比 {rush_ratio*100:.0f}%（{tier_count['冲刺']}/{total}），比例偏高，滑档风险增加"
            })

        # 全部同档次
        if tier_count["冲刺"] == total:
            self.issues.append({
                "level": "❌",
                "category": "梯度比例",
                "message": "全部志愿均为冲刺档，极度危险！几乎没有录取保障"
            })
        elif tier_count["稳妥"] == total:
            self.issues.append({
                "level": "⚠️",
                "category": "梯度比例",
                "message": "全部志愿均为稳妥档，过于保守，可能错过更好的院校机会"
            })
        elif tier_count["保底"] == total:
            self.issues.append({
                "level": "⚠️",
                "category": "梯度比例",
                "message": "全部志愿均为保底档，过于保守，浪费了分数"
            })

        # 稳妥偏少
        if stable_ratio < 0.3 and total >= 6:
            self.issues.append({
                "level": "⚠️",
                "category": "梯度比例",
                "message": f"稳妥志愿占比仅 {stable_ratio*100:.0f}%（{tier_count['稳妥']}/{total}），建议占比 40-50%"
            })

    def _check_order(self, volunteers: list, tier_list: dict):
        """检查志愿排序是否合理"""
        # 检查是否有保底院校排在冲刺院校前面
        rush_indices = [v["order"] - 1 for v in volunteers
                        if v.get("school_rank") and self.classify_tier(v["school_rank"]) == "冲刺"]
        safe_indices = [v["order"] - 1 for v in volunteers
                        if v.get("school_rank") and self.classify_tier(v["school_rank"]) == "保底"]

        if rush_indices and safe_indices:
            # 如果最小的保底index小于最大的冲刺index，说明有保底排在了冲刺前面
            if min(safe_indices) < max(rush_indices):
                self.issues.append({
                    "level": "⚠️",
                    "category": "排序检查",
                    "message": "部分保底院校排在了冲刺院校前面，建议调整为：冲刺 → 稳妥 → 保底"
                })

    def _check_transfer(self, volunteers: list):
        """检查不服从调剂的风险"""
        no_transfer = [v for v in volunteers if v.get("obey_transfer") is False]
        no_transfer_count = len(no_transfer)

        if no_transfer_count > 0:
            names = [v.get("name", f"第{v.get('order')}志愿") for v in no_transfer]
            self.issues.append({
                "level": "⚠️",
                "category": "调剂检查",
                "message": f"有 {no_transfer_count} 所志愿选择不服从调剂（{', '.join(names)}），平行志愿下被退档后该批次不再投档"
            })

        # 冲刺档不服从调剂 = 高风险
        high_risk = [v for v in no_transfer
                     if v.get("school_rank") and self.classify_tier(v["school_rank"]) == "冲刺"]
        if high_risk:
            names = [v.get("name", f"第{v.get('order')}志愿") for v in high_risk]
            self.issues.append({
                "level": "❌",
                "category": "调剂检查",
                "message": f"冲刺档不服从调剂（{', '.join(names)}）风险极高！冲刺档本身就录取不确定性大，不服从调剂极易退档"
            })

    def _calc_score(self, tier_count: dict, total: int) -> int:
        """计算健康度评分（0-100）"""
        if total == 0:
            return 0

        score = 100

        # 比例合理性（满分 60）
        rush_ratio = tier_count["冲刺"] / total
        stable_ratio = tier_count["稳妥"] / total
        safe_ratio = tier_count["保底"] / total

        # 理想比例：冲20-30%，稳40-50%，保20-30%
        ideal_rush = 0.25
        ideal_stable = 0.45
        ideal_safe = 0.30

        ratio_penalty = (
            abs(rush_ratio - ideal_rush) +
            abs(stable_ratio - ideal_stable) +
            abs(safe_ratio - ideal_safe)
        ) * 100

        score -= int(min(ratio_penalty * 2, 60))

        # 没有保底扣 30
        if tier_count["保底"] == 0:
            score -= 30

        # 冲刺过多扣分
        if rush_ratio > 0.5:
            score -= 10

        # 不服从调剂扣分
        # 这部分在 issues 中已体现，这里做额外扣分

        return max(0, min(100, score))

    def _build_result(self, volunteers: list, tier_count: dict, score: int = None) -> dict:
        """构建结果"""
        if score is None:
            score = self._calc_score(tier_count, len(volunteers))

        # 综合评级
        if score >= 85:
            grade = "优秀"
            emoji = "🟢"
        elif score >= 70:
            grade = "良好"
            emoji = "🟡"
        elif score >= 50:
            grade = "一般"
            emoji = "🟠"
        else:
            grade = "危险"
            emoji = "🔴"

        return {
            "score": score,
            "grade": grade,
            "emoji": emoji,
            "total": len(volunteers),
            "tier_count": tier_count,
            "issues": self.issues
        }


def format_report(result: dict) -> str:
    """格式化健康度评估报告"""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("  志愿梯度健康度评估报告")
    lines.append("=" * 60)
    lines.append("")

    # 总体评分
    score = result.get("score", 0)
    grade = result.get("grade", "未知")
    emoji = result.get("emoji", "")
    lines.append(f"  综合评分：{emoji} {score}/100（{grade}）")
    lines.append("")

    # 档次分布
    tier_count = result.get("tier_count", {})
    total = result.get("total", 1)
    lines.append(f"  {'─' * 40}")
    lines.append(f"  志愿分布：")
    lines.append(f"  {'─' * 40}")

    for tier_name in ["冲刺", "稳妥", "保底", "未分类"]:
        count = tier_count.get(tier_name, 0)
        if count > 0:
            ratio = count / total * 100 if total > 0 else 0
            bar = "█" * int(ratio / 5) + "░" * (20 - int(ratio / 5))
            lines.append(f"  {tier_name}  {bar} {count} 所（{ratio:.0f}%）")

    lines.append("")

    # 问题列表
    issues = result.get("issues", [])
    if issues:
        lines.append(f"  {'─' * 40}")
        lines.append(f"  问题清单：")
        lines.append(f"  {'─' * 40}")

        for issue in issues:
            level = issue.get("level", "⚠️")
            category = issue.get("category", "")
            message = issue.get("message", "")
            lines.append(f"  {level} 【{category}】{message}")
    else:
        lines.append("  ✅ 未发现明显问题，志愿梯度设计合理！")

    # 建议总结
    lines.append("")
    lines.append(f"  {'─' * 40}")
    lines.append(f"  优化建议：")
    lines.append(f"  {'─' * 40}")

    suggestions = _generate_suggestions(result)
    for s in suggestions:
        lines.append(f"  💡 {s}")

    lines.append("")
    lines.append(f"  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60 + "\n")

    return "\n".join(lines)


def _generate_suggestions(result: dict) -> list:
    """根据检查结果生成优化建议"""
    suggestions = []
    tier_count = result.get("tier_count", {})
    total = result.get("total", 1)
    issues = result.get("issues", [])

    # 根据问题生成建议
    has_no_safe = any("没有保底" in i.get("message", "") for i in issues)
    has_rush_too_many = any("冲刺志愿占比" in i.get("message", "") for i in issues)
    has_order_issue = any("保底院校排在" in i.get("message", "") for i in issues)
    has_transfer_issue = any("不服从调剂" in i.get("message", "") for i in issues)

    if has_no_safe:
        suggestions.append("🚨 优先添加 2 所保底院校，防止滑档导致直接进入征集志愿")

    if has_rush_too_many:
        rush = tier_count.get("冲刺", 0)
        suggestions.append(f"建议将部分冲刺志愿替换为稳妥或保底院校（当前冲刺 {rush} 所）")

    if has_order_issue:
        suggestions.append("重新排序志愿：冲刺档 → 稳妥档 → 保底档")

    if has_transfer_issue:
        suggestions.append("冲刺档院校建议选择服从调剂，降低退档风险")

    # 通用建议
    if total >= 6 and tier_count.get("稳妥", 0) < total * 0.3:
        suggestions.append("稳妥档是志愿表的核心（建议占 40-50%），适当增加")

    if not suggestions:
        suggestions.append("当前志愿梯度设计合理，建议在填报前确认各院校招生章程中的特殊要求")

    return suggestions


def main():
    parser = argparse.ArgumentParser(
        description="高考志愿梯度健康度检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # JSON 文件模式（推荐，支持完整院校信息）
  python health_check.py --input volunteer_draft.json

  # 简单模式（仅检查数量比例）
  python health_check.py --total 10 --rush 3 --stable 4 --safe 2 --unspecified 1

JSON 文件格式：
{
    "student_rank": 30000,
    "province": "浙江",
    "volunteers": [
        {"order": 1, "name": "南京邮电大学", "school_rank": 25000, "obey_transfer": true},
        {"order": 2, "name": "杭州电子科技大学", "school_rank": 28000, "obey_transfer": true}
    ]
}
        """
    )
    parser.add_argument("--input", type=str, default=None, help="输入 JSON 志愿文件路径")
    parser.add_argument("--total", type=int, default=None, help="志愿总数（简单模式）")
    parser.add_argument("--rush", type=int, default=0, help="冲刺志愿数量")
    parser.add_argument("--stable", type=int, default=0, help="稳妥志愿数量")
    parser.add_argument("--safe", type=int, default=0, help="保底志愿数量")
    parser.add_argument("--unspecified", type=int, default=0, help="未填写志愿数量")

    args = parser.parse_args()

    if args.input:
        # JSON 文件模式
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

        student_rank = data.get("student_rank", 0)
        province = data.get("province", "")
        subject_type = data.get("subject_type", "")
        volunteers = data.get("volunteers", [])

        checker = HealthChecker(student_rank, province, subject_type)
        result = checker.check_volunteers(volunteers)

        # 在结果中附加院校列表的档次标注
        result["volunteer_details"] = []
        for v in volunteers:
            rank = v.get("school_rank")
            if rank and rank > 0:
                tier = checker.classify_tier(rank)
            else:
                tier = "未分类"
            result["volunteer_details"].append({
                "order": v.get("order", "?"),
                "name": v.get("name", "-"),
                "tier": tier,
                "school_rank": rank,
                "major": v.get("major", "-"),
                "obey_transfer": v.get("obey_transfer", True)
            })

    elif args.total:
        # 简单模式
        checker = HealthChecker(student_rank=0)
        result = checker.check_simple(args.total, args.rush, args.stable, args.safe, args.unspecified)
    else:
        print("❌ 请提供 --input（JSON文件）或 --total（简单模式）")
        parser.print_help()
        sys.exit(1)

    # 输出报告
    print(format_report(result))

    # 附加院校详情（JSON 模式）
    if args.input and "volunteer_details" in result:
        lines = []
        lines.append("  志愿详情：")
        lines.append(f"  {'─' * 40}")
        for v in result["volunteer_details"]:
            transfer_mark = "" if v.get("obey_transfer", True) else " ⚠️不服从调剂"
            lines.append(
                f"  #{v['order']:<2} [{v['tier']}] {v['name']:<20} "
                f"位次:{v.get('school_rank', '-'):<8} "
                f"专业:{v['major']}{transfer_mark}"
            )
        lines.append("")
        print("\n".join(lines))


if __name__ == "__main__":
    main()
