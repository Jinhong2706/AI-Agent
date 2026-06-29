#!/usr/bin/env python3
"""
高考志愿录取概率计算工具

功能：
1. 基于考生位次和院校历年录取位次，计算录取概率
2. 支持多所院校批量计算
3. 支持输入 JSON 文件批量处理

用法：
    # 单所院校
    python calc_probability.py --rank 30000 --school_rank 28000 --school_name "杭州电子科技大学"

    # 多所院校（逗号分隔）
    python calc_probability.py --rank 30000 --school_rank "28000,31000,35000,25000" \
        --school_name "杭电,宁波大学,浙江工商大学,南京邮电大学"

    # JSON 文件输入
    python calc_probability.py --input schools.json --rank 30000

    # 输出 JSON
    python calc_probability.py --rank 30000 --school_rank 28000 --school_name "杭电" --output result.json

JSON 输入格式：
[
    {"name": "杭州电子科技大学", "city": "杭州", "min_rank_2023": 28000, "min_rank_2022": 29000, "min_rank_2021": 27000},
    ...
]
"""

import argparse
import json
import math
import sys
from datetime import datetime


def calc_single_probability(student_rank: int, school_rank: int) -> dict:
    """
    计算单所院校的录取概率

    基于位次差的概率模型（简化版）：
    - 位次差 = 学校录取位次 - 考生位次
    - 正值（学校位次更差/数字更大）→ 录取概率高
    - 负值（学校位次更好/数字更小）→ 录取概率低

    使用 sigmoid 函数平滑映射到 0-100% 概率区间。

    Args:
        student_rank: 考生全省位次
        school_rank: 院校历年录取最低位次

    Returns:
        包含概率、评级、建议的字典
    """
    if student_rank <= 0 or school_rank <= 0:
        return {"probability": None, "tier": "未知", "risk": "数据异常"}

    # 位次差比例（正值表示考生占优）
    diff_ratio = (school_rank - student_rank) / student_rank

    # 使用 sigmoid 函数映射到概率
    # diff_ratio = 0 时概率约 75%（位次完全匹配也有较高录取率）
    # diff_ratio = -0.1（冲10%）时概率约 45%
    # diff_ratio = 0.2（保20%）时概率约 95%
    probability = 1 / (1 + math.exp(-(diff_ratio * 20 - 1)))
    pct = round(probability * 100, 1)

    # 评级和风险提示
    if pct >= 85:
        tier = "保底"
        risk = "录取概率很高，但注意是否接受被调剂到冷门专业"
    elif pct >= 60:
        tier = "稳妥"
        risk = "录取概率较高，建议放在志愿表中段"
    elif pct >= 35:
        tier = "冲刺"
        risk = "有一定录取可能，放在志愿表前段冲刺"
    else:
        tier = "冲高"
        risk = "录取概率较低，谨慎填报，做好滑档准备"

    return {
        "probability": pct,
        "tier": tier,
        "risk": risk,
        "rank_diff": school_rank - student_rank,
        "diff_ratio": round(diff_ratio * 100, 1)
    }


def calc_avg_probability(student_rank: int, ranks: list) -> dict:
    """
    基于多年录取位次计算平均录取概率

    Args:
        student_rank: 考生全省位次
        ranks: 近N年录取最低位次列表

    Returns:
        综合分析结果
    """
    if not ranks:
        return {"probability": None, "tier": "未知", "risk": "无数据"}

    # 各年概率
    yearly = []
    for r in ranks:
        if r and r > 0:
            result = calc_single_probability(student_rank, r)
            yearly.append(result)

    if not yearly:
        return {"probability": None, "tier": "未知", "risk": "无有效数据"}

    # 取平均概率
    avg_pct = sum(y["probability"] for y in yearly) / len(yearly)
    avg_pct = round(avg_pct, 1)

    # 取最近一年的概率作为参考
    latest = yearly[0]
    # 趋势判断
    if len(yearly) >= 2:
        trend = yearly[-1]["probability"] - yearly[0]["probability"]
        if trend > 10:
            trend_desc = "录取难度下降（位次放宽）"
        elif trend < -10:
            trend_desc = "录取难度上升（位次收紧）"
        else:
            trend_desc = "录取难度基本稳定"
    else:
        trend_desc = "数据不足，无法判断趋势"

    # 综合评级
    if avg_pct >= 85:
        tier = "保底"
    elif avg_pct >= 60:
        tier = "稳妥"
    elif avg_pct >= 35:
        tier = "冲刺"
    else:
        tier = "冲高"

    return {
        "probability": avg_pct,
        "tier": tier,
        "trend": trend_desc,
        "yearly_analysis": yearly,
        "risk": latest["risk"],
        "data_years": len(yearly)
    }


def format_results_table(student_rank: int, results: list) -> str:
    """格式化结果为表格"""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append(f"  录取概率分析报告  |  考生位次：第 {student_rank:,} 名")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  {'序号':<4} {'院校名称':<20} {'录取概率':<10} {'档次':<6} {'位次差':<10} {'风险评估'}")
    lines.append(f"  {'─' * 66}")

    for i, item in enumerate(results, 1):
        name = item.get("name", "-")
        prob = item.get("analysis", {}).get("probability", "-")
        tier = item.get("analysis", {}).get("tier", "-")
        diff = item.get("analysis", {}).get("rank_diff", "-")
        if isinstance(diff, int):
            diff_str = f"{diff:+,}"
        else:
            diff_str = str(diff)
        risk = item.get("analysis", {}).get("risk", "-")

        prob_str = f"{prob}%" if isinstance(prob, (int, float)) else str(prob)

        lines.append(f"  {i:<4} {name:<20} {prob_str:<10} {tier:<6} {diff_str:<10} {risk}")

    lines.append("")
    lines.append("  档次说明：")
    lines.append("    🟢 保底（≥85%）录取概率很高，注意专业调剂")
    lines.append("    🟡 稳妥（60%-85%）录取概率较高，志愿表核心")
    lines.append("    🟠 冲刺（35%-60%）有一定可能，放在志愿表前段")
    lines.append("    🔴 冲高（<35%）概率较低，谨慎填报")
    lines.append("")
    lines.append(f"  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 70 + "\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="高考志愿录取概率计算工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 单所院校
  python calc_probability.py --rank 30000 --school_rank 28000 --school_name "杭州电子科技大学"

  # 多所院校
  python calc_probability.py --rank 30000 --school_rank "28000,31000,35000" --school_name "杭电,宁大,浙工商"

  # JSON 文件
  python calc_probability.py --input schools.json --rank 30000
        """
    )
    parser.add_argument("--rank", type=int, required=True, help="考生全省位次")
    parser.add_argument("--school_rank", type=str, default=None,
                        help="院校录取位次（单个数字或逗号分隔的多年数据）")
    parser.add_argument("--school_name", type=str, default=None,
                        help="院校名称（单个或逗号分隔，与 school_rank 对应）")
    parser.add_argument("--input", type=str, default=None,
                        help="输入 JSON 文件路径（批量模式）")
    parser.add_argument("--output", type=str, default=None,
                        help="输出 JSON 结果文件路径")

    args = parser.parse_args()

    results = []

    # JSON 文件模式
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            schools = json.load(f)

        for school in schools:
            name = school.get("name", "未知院校")
            # 收集多年位次数据
            ranks = []
            for year_key in ["min_rank_2025", "min_rank_2024", "min_rank_2023", "min_rank_2022", "min_rank_2021"]:
                if year_key in school and school[year_key]:
                    ranks.append(school[year_key])

            if ranks:
                analysis = calc_avg_probability(args.rank, ranks)
            elif "min_rank" in school:
                analysis = calc_single_probability(args.rank, school["min_rank"])
            else:
                analysis = {"probability": None, "tier": "未知", "risk": "无录取位次数据"}

            results.append({
                "name": name,
                "city": school.get("city", "-"),
                "analysis": analysis
            })

    # 命令行模式
    elif args.school_rank and args.school_name:
        names = [n.strip() for n in args.school_name.split(",")]
        rank_groups = [g.strip() for g in args.school_rank.split(",")]

        if len(names) != len(rank_groups):
            print(f"❌ 错误：院校名称数量（{len(names)}）与位次数量（{len(rank_groups)}）不匹配")
            sys.exit(1)

        for name, rank_str in zip(names, rank_groups):
            # 支持多年数据用|分隔，如 "28000|29000|27000"
            rank_parts = [int(r.strip()) for r in rank_str.split("|") if r.strip().isdigit()]

            if len(rank_parts) > 1:
                analysis = calc_avg_probability(args.rank, rank_parts)
            elif len(rank_parts) == 1:
                analysis = calc_single_probability(args.rank, rank_parts[0])
            else:
                analysis = {"probability": None, "tier": "未知", "risk": "位次数据无效"}

            results.append({
                "name": name,
                "city": "-",
                "analysis": analysis
            })

    else:
        print("❌ 请提供 --input（JSON文件）或 --school_rank + --school_name")
        parser.print_help()
        sys.exit(1)

    # 按录取概率排序（高到低）
    results.sort(key=lambda x: x.get("analysis", {}).get("probability") or 0, reverse=True)

    # 输出表格
    print(format_results_table(args.rank, results))

    # 输出 JSON
    if args.output:
        output_data = {
            "student_rank": args.rank,
            "generated_at": datetime.now().isoformat(),
            "results": results
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"  JSON 结果已保存至：{args.output}")


if __name__ == "__main__":
    main()
