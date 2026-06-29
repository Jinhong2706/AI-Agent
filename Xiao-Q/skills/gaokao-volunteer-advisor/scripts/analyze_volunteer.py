#!/usr/bin/env python3
"""
高考志愿位次分析工具（增强版）

功能：
1. 根据考生分数和位次，计算冲稳保位次区间
2. 生成结构化的志愿填报分析报告
3. 输出 Markdown 格式报告，方便复制分享

用法：
    python analyze_volunteer.py --score 565 --rank 30000 --province 浙江 --type 物理类

    # 仅分数（无位次时）
    python analyze_volunteer.py --score 565 --province 浙江 --type 物理类

输出：
    控制台报告 + 可选 Markdown 文件（--output report.md）
"""

import argparse
import json
import sys
from datetime import datetime


def calc_rank_ranges(rank: int | None, score: int) -> dict:
    """
    根据位次（或分数估算）计算冲稳保位次区间

    Args:
        rank: 考生全省位次（None 时用分数估算）
        score: 考生高考总分

    Returns:
        包含冲/稳/保三档位次区间和分数区间的字典
    """
    if rank is not None and rank > 0:
        # 基于位次的精确计算
        return {
            "rank": rank,
            "rush": {
                "label": "冲刺",
                "rank_range": [int(rank * 0.85), int(rank * 0.95)],
                "desc": f"位次 {int(rank * 0.85):,} ~ {int(rank * 0.95):,}"
            },
            "stable": {
                "label": "稳妥",
                "rank_range": [int(rank * 0.95), int(rank * 1.05)],
                "desc": f"位次 {int(rank * 0.95):,} ~ {int(rank * 1.05):,}"
            },
            "safe": {
                "label": "保底",
                "rank_range": [int(rank * 1.15), int(rank * 1.30)],
                "desc": f"位次 {int(rank * 1.15):,} ~ {int(rank * 1.30):,}"
            },
            "based_on": "位次（推荐）"
        }
    else:
        # 基于分数的粗略估算（位次未知时的备用方案）
        return {
            "rank": None,
            "rush": {
                "label": "冲刺",
                "score_range": [score + 10, score + 30],
                "desc": f"分数 {score + 10} ~ {score + 30} 分"
            },
            "stable": {
                "label": "稳妥",
                "score_range": [score - 10, score + 10],
                "desc": f"分数 {score - 10} ~ {score + 10} 分"
            },
            "safe": {
                "label": "保底",
                "score_range": [score - 30, score - 10],
                "desc": f"分数 {score - 30} ~ {score - 10} 分"
            },
            "based_on": "分数（粗略，建议补充位次）"
        }


def generate_console_report(score: int, province: str, subject_type: str,
                             rank: int | None, analysis: dict) -> str:
    """生成控制台格式的分析报告"""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("          高考志愿填报分析报告")
    lines.append("=" * 60)

    # 考生信息
    lines.append(f"\n  考生信息：{province} | {subject_type} | {score}分")
    if rank:
        lines.append(f"  全省位次：第 {rank:,} 名")
    else:
        lines.append(f"  全省位次：未提供（⚠️ 建议尽快查询一分一段表）")

    lines.append(f"  分析依据：{analysis['based_on']}")

    # 建议区间
    lines.append(f"\n  {'─' * 40}")
    lines.append(f"  建议填报区间：")
    lines.append(f"  {'─' * 40}")

    for key in ["rush", "stable", "safe"]:
        item = analysis[key]
        label = item["label"]
        if "rank_range" in item:
            r = item["rank_range"]
            lines.append(f"  【{label}档】位次 {r[0]:,} ~ {r[1]:,}")
        elif "score_range" in item:
            r = item["score_range"]
            lines.append(f"  【{label}档】分数 {r[0]} ~ {r[1]} 分")

    # 比例建议
    lines.append(f"\n  {'─' * 40}")
    lines.append(f"  志愿比例建议（平行志愿）：")
    lines.append(f"  {'─' * 40}")
    lines.append(f"  冲刺档：2~3 所（约 20-30%）")
    lines.append(f"  稳妥档：3~4 所（约 40-50%）")
    lines.append(f"  保底档：2~3 所（约 20-30%）")

    # 注意事项
    lines.append(f"\n  {'─' * 40}")
    lines.append(f"  注意事项：")
    lines.append(f"  {'─' * 40}")
    tips = [
        "建议参考目标院校近 3 年录取位次数据",
        "冲档院校放在志愿表前面，保底院校放在最后",
        "务必确认是否服从专业调剂",
        "查阅目标院校招生章程中的特殊要求（体检/单科成绩等）"
    ]
    if not rank:
        tips.insert(0, "⚠️ 当前基于分数估算，误差较大，请尽快查询精确位次")

    for tip in tips:
        lines.append(f"  • {tip}")

    lines.append(f"\n{'=' * 60}")
    lines.append(f"  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"{'=' * 60}\n")

    return "\n".join(lines)


def generate_markdown_report(score: int, province: str, subject_type: str,
                              rank: int | None, analysis: dict) -> str:
    """生成 Markdown 格式的分析报告"""
    lines = []
    lines.append("# 高考志愿填报分析报告\n")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # 考生信息
    lines.append("## 考生基本信息\n")
    lines.append(f"- **省份**：{province}")
    lines.append(f"- **科类**：{subject_type}")
    lines.append(f"- **分数**：{score} 分")
    if rank:
        lines.append(f"- **位次**：约第 {rank:,} 名（全省{subject_type}）")
    else:
        lines.append(f"- **位次**：待查询 ⚠️")
    lines.append(f"- **分析依据**：{analysis['based_on']}\n")

    # 建议区间
    lines.append("## 建议填报区间\n")
    lines.append("| 档位 | 范围 | 说明 |")
    lines.append("|------|------|------|")

    tier_info = {
        "rush": "往年录取位次略高的院校，有冲刺机会",
        "stable": "录取概率较高的院校，志愿表核心",
        "safe": "确保有学可上的院校，防止滑档"
    }

    for key in ["rush", "stable", "safe"]:
        item = analysis[key]
        if "rank_range" in item:
            r = item["rank_range"]
            range_str = f"位次 {r[0]:,} ~ {r[1]:,}"
        elif "score_range" in item:
            r = item["score_range"]
            range_str = f"分数 {r[0]} ~ {r[1]} 分"
        else:
            range_str = "-"
        lines.append(f"| {item['label']} | {range_str} | {tier_info[key]} |")

    # 比例建议
    lines.append("\n## 志愿梯度建议\n")
    lines.append("建议按 **2:5:3** 或 **3:4:3** 的比例分配冲/稳/保志愿：")
    lines.append("- 冲刺档：2～3 所（约 20-30%）")
    lines.append("- 稳妥档：3～4 所（约 40-50%）")
    lines.append("- 保底档：2～3 所（约 20-30%）\n")

    # 院校推荐模板
    lines.append("## 推荐院校志愿表（待填写）\n")
    for tier_key, tier_label in [("rush", "冲刺档"), ("stable", "稳妥档"), ("safe", "保底档")]:
        lines.append(f"### {tier_label}\n")
        lines.append("| 序号 | 院校名称 | 所在城市 | 近3年最低位次 | 推荐专业 | 备注 |")
        lines.append("|------|----------|----------|--------------|----------|------|")
        for i in range(1, 4):
            lines.append(f"| {i} | | | | | |")
        lines.append("")

    # 风险提示
    lines.append("---\n")
    lines.append("> 📌 **温馨提醒**：")
    lines.append("> 1. 本建议基于用户提供的数据生成，请以各省考试院官方公布的招生计划和历年数据为准")
    lines.append("> 2. 位次法≠绝对准确，需结合当年招生计划变化、院校热度波动等因素综合判断")
    lines.append("> 3. 建议至少咨询学校老师或专业机构后，再最终确认志愿")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="高考志愿位次分析工具（增强版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python analyze_volunteer.py --score 565 --rank 30000 --province 浙江 --type 物理类
  python analyze_volunteer.py --score 565 --province 广东 --type 物理类
  python analyze_volunteer.py --score 600 --rank 15000 --province 浙江 --type 物理类 --output report.md
        """
    )
    parser.add_argument("--score", type=int, required=True, help="考生高考总分")
    parser.add_argument("--rank", type=int, default=None, help="全省位次（优先于分数）")
    parser.add_argument("--province", type=str, default="全国", help="所在省份")
    parser.add_argument("--type", type=str, default="物理类",
                        help="选科类型（物理类/历史类/理科/文科/综合）")
    parser.add_argument("--output", type=str, default=None,
                        help="输出 Markdown 文件路径（如 report.md）")
    parser.add_argument("--json", type=str, default=None,
                        help="输出 JSON 文件路径（程序化使用）")

    args = parser.parse_args()

    # 计算分析结果
    analysis = calc_rank_ranges(args.rank, args.score)

    # 输出控制台报告
    console_report = generate_console_report(
        args.score, args.province, args.type, args.rank, analysis
    )
    print(console_report)

    # 输出 Markdown 文件
    if args.output:
        md_report = generate_markdown_report(
            args.score, args.province, args.type, args.rank, analysis
        )
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"  Markdown 报告已保存至：{args.output}")

    # 输出 JSON 文件
    if args.json:
        result = {
            "score": args.score,
            "province": args.province,
            "subject_type": args.type,
            "rank": args.rank,
            "analysis": analysis,
            "generated_at": datetime.now().isoformat()
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  JSON 数据已保存至：{args.json}")


if __name__ == "__main__":
    main()
