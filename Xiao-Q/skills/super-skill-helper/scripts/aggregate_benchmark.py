#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基准测试结果聚合脚本

聚合迭代运行的结果，生成 benchmark.json 和 benchmark.md。

用法:
    python aggregate_benchmark.py <workspace>/iteration-N --skill-name <name>

示例:
    python aggregate_benchmark.py my-skill-workspace/iteration-1 --skill-name my-skill
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev


def aggregate_benchmark(workspace_path, skill_name):
    """
    聚合基准测试结果
    
    Args:
        workspace_path: 工作区路径（iteration-N 目录）
        skill_name: 技能名称
    """
    workspace = Path(workspace_path)
    
    if not workspace.exists():
        print(f"❌ 工作区不存在：{workspace}")
        sys.exit(1)
    
    print(f"📊 聚合基准测试结果")
    print(f"工作区：{workspace}")
    print(f"技能：{skill_name}")
    print("=" * 60)
    
    # 收集所有运行结果
    runs = collect_runs(workspace)
    
    if not runs:
        print("❌ 未找到任何运行结果")
        sys.exit(1)
    
    print(f"✓ 找到 {len(runs)} 个运行结果")
    
    # 按评估分组
    evals = group_by_eval(runs)
    print(f"✓ 覆盖 {len(evals)} 个评估用例")
    
    # 计算统计数据
    benchmark_data = calculate_statistics(evals)
    
    # 生成 benchmark.json
    benchmark_json_path = workspace / 'benchmark.json'
    with open(benchmark_json_path, 'w', encoding='utf-8') as f:
        json.dump(benchmark_data, f, ensure_ascii=False, indent=2)
    print(f"✓ 生成：{benchmark_json_path}")
    
    # 生成 benchmark.md
    benchmark_md_path = workspace / 'benchmark.md'
    markdown_content = generate_markdown_report(benchmark_data, skill_name)
    with open(benchmark_md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    print(f"✓ 生成：{benchmark_md_path}")
    
    # 打印摘要
    print_summary(benchmark_data)
    
    return benchmark_data


def collect_runs(workspace):
    """收集所有运行结果"""
    runs = []
    
    # 查找所有 eval 目录
    for eval_dir in workspace.glob('eval-*'):
        if not eval_dir.is_dir():
            continue
        
        # 查找 with_skill 和 baseline 运行
        with_skill_dir = eval_dir / 'with_skill'
        baseline_dir = eval_dir / 'without_skill'  # 或 old_skill
        
        if with_skill_dir.exists():
            run_data = {
                'eval_name': eval_dir.name,
                'with_skill': load_run_data(with_skill_dir)
            }
            
            # 尝试加载基线
            if baseline_dir.exists():
                run_data['baseline'] = load_run_data(baseline_dir)
            
            runs.append(run_data)
    
    return runs


def load_run_data(run_dir):
    """加载单个运行的数据"""
    data = {
        'outputs': [],
        'grading': None,
        'timing': None
    }
    
    # 加载输出文件列表
    outputs_dir = run_dir / 'outputs'
    if outputs_dir.exists():
        data['outputs'] = [f.name for f in outputs_dir.iterdir() if f.is_file()]
    
    # 加载评分结果
    grading_path = run_dir / 'grading.json'
    if grading_path.exists():
        with open(grading_path, 'r', encoding='utf-8') as f:
            data['grading'] = json.load(f)
    
    # 加载时序数据
    timing_path = run_dir / 'timing.json'
    if timing_path.exists():
        with open(timing_path, 'r', encoding='utf-8') as f:
            data['timing'] = json.load(f)
    
    return data


def group_by_eval(runs):
    """按评估用例分组运行结果"""
    evals = {}
    
    for run in runs:
        eval_name = run['eval_name']
        evals[eval_name] = run
    
    return evals


def calculate_statistics(evals):
    """计算统计数据"""
    benchmark = {
        'skill_name': 'skill',
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_evals': len(evals),
            'with_skill_pass_rate': 0.0,
            'baseline_pass_rate': 0.0,
            'improvement': 0.0
        },
        'evals': []
    }
    
    all_with_skill_rates = []
    all_baseline_rates = []
    
    for eval_name, run in evals.items():
        eval_data = {
            'eval_name': eval_name,
            'with_skill': {},
            'baseline': {}
        }
        
        # 计算 with_skill 通过率
        if run['with_skill']['grading']:
            grading = run['with_skill']['grading']
            total = grading.get('summary', {}).get('total', 0)
            passed = grading.get('summary', {}).get('passed', 0)
            pass_rate = passed / total if total > 0 else 0.0
            
            eval_data['with_skill'] = {
                'pass_rate': pass_rate,
                'total_assertions': total,
                'passed_assertions': passed,
                'timing': run['with_skill']['timing']
            }
            all_with_skill_rates.append(pass_rate)
        
        # 计算 baseline 通过率
        if run['baseline']['grading']:
            grading = run['baseline']['grading']
            total = grading.get('summary', {}).get('total', 0)
            passed = grading.get('summary', {}).get('passed', 0)
            pass_rate = passed / total if total > 0 else 0.0
            
            eval_data['baseline'] = {
                'pass_rate': pass_rate,
                'total_assertions': total,
                'passed_assertions': passed,
                'timing': run['baseline']['timing']
            }
            all_baseline_rates.append(pass_rate)
        
        benchmark['evals'].append(eval_data)
    
    # 计算总体统计
    if all_with_skill_rates:
        benchmark['summary']['with_skill_pass_rate'] = mean(all_with_skill_rates)
        
        if len(all_with_skill_rates) > 1:
            benchmark['summary']['with_skill_stddev'] = stdev(all_with_skill_rates)
        else:
            benchmark['summary']['with_skill_stddev'] = 0.0
    
    if all_baseline_rates:
        benchmark['summary']['baseline_pass_rate'] = mean(all_baseline_rates)
        
        if len(all_baseline_rates) > 1:
            benchmark['summary']['baseline_stddev'] = stdev(all_baseline_rates)
        else:
            benchmark['summary']['baseline_stddev'] = 0.0
    
    # 计算改进
    if all_with_skill_rates and all_baseline_rates:
        benchmark['summary']['improvement'] = (
            benchmark['summary']['with_skill_pass_rate'] - 
            benchmark['summary']['baseline_pass_rate']
        )
    
    return benchmark


def generate_markdown_report(benchmark, skill_name):
    """生成 Markdown 报告"""
    md = f"""# 基准测试报告

**技能**: {skill_name}  
**生成时间**: {benchmark['generated_at']}

---

## 执行摘要

| 指标 | With Skill | Baseline | 改进 |
|------|-----------|----------|------|
| **平均通过率** | {benchmark['summary']['with_skill_pass_rate']:.1%} | {benchmark['summary']['baseline_pass_rate']:.1%} | {benchmark['summary']['improvement']:+.1%} |
| **标准差** | {benchmark['summary'].get('with_skill_stddev', 0):.2f} | {benchmark['summary'].get('baseline_stddev', 0):.2f} | - |
| **评估用例数** | {benchmark['summary']['total_evals']} | - | - |

---

## 详细结果

"""
    
    for eval_data in benchmark['evals']:
        eval_name = eval_data['eval_name']
        
        md += f"### {eval_name}\n\n"
        
        # With Skill
        if eval_data['with_skill']:
            ws = eval_data['with_skill']
            md += f"**With Skill**:\n"
            md += f"- 通过率：{ws['pass_rate']:.1%} ({ws['passed_assertions']}/{ws['total_assertions']})\n"
            
            if ws.get('timing'):
                md += f"- 时间：{ws['timing'].get('total_duration_seconds', 0):.1f}s\n"
                md += f"- Token: {ws['timing'].get('total_tokens', 0):,}\n"
        
        md += "\n"
        
        # Baseline
        if eval_data['baseline']:
            bl = eval_data['baseline']
            md += f"**Baseline**:\n"
            md += f"- 通过率：{bl['pass_rate']:.1%} ({bl['passed_assertions']}/{bl['total_assertions']})\n"
            
            if bl.get('timing'):
                md += f"- 时间：{bl['timing'].get('total_duration_seconds', 0):.1f}s\n"
                md += f"- Token: {bl['timing'].get('total_tokens', 0):,}\n"
        
        md += "\n---\n\n"
    
    # 分析洞察
    md += generate_insights(benchmark)
    
    return md


def generate_insights(benchmark):
    """生成分析洞察"""
    insights = "## 分析洞察\n\n"
    
    # 整体表现
    summary = benchmark['summary']
    
    if summary['improvement'] > 0.1:
        insights += "✅ **技能显著提升性能**\n\n"
        insights += f"技能将平均通过率从 {summary['baseline_pass_rate']:.1%} 提升到 {summary['with_skill_pass_rate']:.1%}。\n\n"
    elif summary['improvement'] > 0:
        insights += "⚠️ **技能有轻微改进**\n\n"
        insights += f"技能将平均通过率从 {summary['baseline_pass_rate']:.1%} 提升到 {summary['with_skill_pass_rate']:.1%}。\n\n"
    else:
        insights += "❌ **技能未显示改进**\n\n"
        insights += f"技能的平均通过率 ({summary['with_skill_pass_rate']:.1%}) 低于或等于基线 ({summary['baseline_pass_rate']:.1%})。\n\n"
    
    # 最佳/最差表现
    if benchmark['evals']:
        best_eval = max(benchmark['evals'], 
                       key=lambda x: x['with_skill'].get('pass_rate', 0) if x['with_skill'] else 0)
        worst_eval = min(benchmark['evals'], 
                        key=lambda x: x['with_skill'].get('pass_rate', 0) if x['with_skill'] else 0)
        
        insights += f"**最佳表现**: {best_eval['eval_name']} "
        if best_eval['with_skill']:
            insights += f"({best_eval['with_skill']['pass_rate']:.1%} 通过率)\n\n"
        
        insights += f"**最差表现**: {worst_eval['eval_name']} "
        if worst_eval['with_skill']:
            insights += f"({worst_eval['with_skill']['pass_rate']:.1%} 通过率)\n\n"
    
    return insights


def print_summary(benchmark):
    """打印摘要"""
    print("\n" + "=" * 60)
    print("📊 基准测试摘要")
    print("=" * 60)
    
    summary = benchmark['summary']
    print(f"\n平均通过率:")
    print(f"  With Skill: {summary['with_skill_pass_rate']:.1%}")
    print(f"  Baseline:   {summary['baseline_pass_rate']:.1%}")
    print(f"  改进：      {summary['improvement']:+.1%}")
    
    print(f"\n评估用例数：{summary['total_evals']}")


def main():
    parser = argparse.ArgumentParser(
        description='聚合基准测试结果',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python aggregate_benchmark.py my-skill-workspace/iteration-1 --skill-name my-skill
        '''
    )
    
    parser.add_argument('workspace', help='工作区路径（iteration-N 目录）')
    parser.add_argument('--skill-name', required=True, help='技能名称')
    
    args = parser.parse_args()
    
    aggregate_benchmark(args.workspace, args.skill_name)


if __name__ == '__main__':
    main()
