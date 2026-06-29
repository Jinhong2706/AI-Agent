#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能描述优化循环脚本

自动优化技能的 description 字段以提高触发准确性。

用法:
    python run_loop.py --eval-set <path-to-eval.json> --skill-path <path-to-skill> [--model <model-id>] [--max-iterations 5] [--verbose]

示例:
    python run_loop.py --eval-set evals/trigger-eval.json --skill-path skills/my-skill --model qwen3.5-plus
"""

import os
import sys
import json
import yaml
import random
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

class DescriptionOptimizer:
    """技能描述优化器"""
    
    def __init__(self, eval_set_path, skill_path, model_id=None, max_iterations=5, verbose=False):
        self.eval_set_path = Path(eval_set_path)
        self.skill_path = Path(skill_path)
        self.model_id = model_id or 'qwen3.5-plus'
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # 加载评估集
        self.eval_set = self.load_eval_set()
        
        # 拆分训练集和测试集（60/40）
        self.train_set, self.test_set = self.split_eval_set()
        
        # 加载当前技能描述
        self.current_description = self.load_skill_description()
        
        # 结果跟踪
        self.iteration_results = []
        self.best_description = None
        self.best_test_score = 0
    
    def load_eval_set(self):
        """加载评估集"""
        print(f"📊 加载评估集：{self.eval_set_path}")
        
        try:
            with open(self.eval_set_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                evals = data
            elif isinstance(data, dict) and 'evals' in data:
                evals = data['evals']
            else:
                raise ValueError("评估集格式错误")
            
            print(f"  ✓ 加载 {len(evals)} 个评估查询")
            return evals
        
        except Exception as e:
            print(f"❌ 加载评估集失败：{e}")
            sys.exit(1)
    
    def split_eval_set(self):
        """拆分训练集和测试集（60/40）"""
        random.seed(42)  # 可重复性
        
        evals = self.eval_set.copy()
        random.shuffle(evals)
        
        split_idx = int(len(evals) * 0.6)
        train_set = evals[:split_idx]
        test_set = evals[split_idx:]
        
        print(f"  ✓ 训练集：{len(train_set)} 个查询 (60%)")
        print(f"  ✓ 测试集：{len(test_set)} 个查询 (40%)")
        
        return train_set, test_set
    
    def load_skill_description(self):
        """加载当前技能描述"""
        skill_md_path = self.skill_path / 'SKILL.md'
        
        try:
            content = skill_md_path.read_text(encoding='utf-8')
            
            # 解析 frontmatter
            if not content.startswith('---'):
                raise ValueError("SKILL.md 缺少 YAML frontmatter")
            
            end_index = content.find('---', 3)
            if end_index == -1:
                raise ValueError("SKILL.md frontmatter 格式错误")
            
            frontmatter_str = content[3:end_index].strip()
            frontmatter = yaml.safe_load(frontmatter_str)
            
            if 'description' not in frontmatter:
                raise ValueError("SKILL.md 缺少 description 字段")
            
            description = frontmatter['description']
            print(f"  ✓ 当前描述：{len(description)} 字符")
            
            return description
        
        except Exception as e:
            print(f"❌ 加载技能描述失败：{e}")
            sys.exit(1)
    
    def evaluate_description(self, description, eval_set):
        """
        评估描述在给定评估集上的表现
        
        返回：触发率（正确触发的比例）
        """
        if not eval_set:
            return 0.0
        
        correct = 0
        
        for eval_item in eval_set:
            query = eval_item.get('query', '')
            should_trigger = eval_item.get('should_trigger', True)
            
            # 模拟触发判断（简化版本）
            # 实际应该调用 Claude API 检查是否触发技能
            # 这里使用简单的关键词匹配作为示例
            
            triggered = self.simulate_trigger(query, description)
            
            if triggered == should_trigger:
                correct += 1
        
        return correct / len(eval_set)
    
    def simulate_trigger(self, query, description):
        """
        模拟触发判断
        
        注意：这是简化版本。实际应该调用 Claude API。
        """
        # 简单的关键词匹配（仅用于演示）
        query_lower = query.lower()
        desc_lower = description.lower()
        
        # 如果查询包含描述中的关键词，认为会触发
        keywords = [word for word in desc_lower.split() if len(word) > 3]
        
        match_count = sum(1 for keyword in keywords if keyword in query_lower)
        
        # 阈值判断（简化）
        return match_count >= 1
    
    def optimize_description(self, current_description, train_results):
        """
        使用 AI 优化描述
        
        基于训练集的失败案例，生成改进的描述
        """
        # 准备失败案例
        failed_cases = []
        for result in train_results:
            if not result['correct']:
                failed_cases.append({
                    'query': result['query'],
                    'should_trigger': result['should_trigger'],
                    'triggered': result['triggered']
                })
        
        if not failed_cases:
            return current_description
        
        # 构建优化 prompt
        prompt = f"""你是一个技能描述优化专家。当前技能描述在某些测试案例上表现不佳。

当前描述:
{current_description}

失败案例:
{json.dumps(failed_cases, ensure_ascii=False, indent=2)}

请分析失败原因，并优化描述以提高触发准确性。

要求:
1. 保持描述简洁（200-500 字符）
2. 明确包含触发条件（"当...时"）
3. 覆盖失败案例中的场景
4. 避免过度泛化

只返回优化后的描述，不要其他内容。"""
        
        # 调用 AI（这里使用示例，实际应该调用 Claude API）
        # 示例实现：简单修改描述
        optimized = current_description
        
        # 添加失败案例中的关键词
        for case in failed_cases[:3]:  # 最多添加 3 个
            if case['should_trigger'] and not case['triggered']:
                # 应该触发但未触发 - 添加相关关键词
                keywords = case['query'].split()[:3]
                for keyword in keywords:
                    if len(keyword) > 2 and keyword.lower() not in optimized.lower():
                        optimized += f" 包括{keyword}"
                        break
        
        return optimized
    
    def run_iteration(self, iteration_num):
        """运行一次优化迭代"""
        print(f"\n{'='*60}")
        print(f"🔄 迭代 #{iteration_num}")
        print(f"{'='*60}")
        
        # 1. 评估当前描述
        print("\n📊 评估当前描述...")
        
        train_score = self.evaluate_description(self.current_description, self.train_set)
        test_score = self.evaluate_description(self.current_description, self.test_set)
        
        print(f"  训练集得分：{train_score:.2%}")
        print(f"  测试集得分：{test_score:.2%}")
        
        # 记录结果
        iteration_result = {
            'iteration': iteration_num,
            'description': self.current_description,
            'train_score': train_score,
            'test_score': test_score,
            'timestamp': datetime.now().isoformat()
        }
        
        self.iteration_results.append(iteration_result)
        
        # 更新最佳描述（基于测试集得分）
        if test_score > self.best_test_score:
            self.best_test_score = test_score
            self.best_description = self.current_description
            print(f"  ✨ 新最佳描述！测试得分：{test_score:.2%}")
        
        # 2. 生成详细评估结果
        train_results = []
        for eval_item in self.train_set:
            query = eval_item.get('query', '')
            should_trigger = eval_item.get('should_trigger', True)
            triggered = self.simulate_trigger(query, self.current_description)
            
            train_results.append({
                'query': query,
                'should_trigger': should_trigger,
                'triggered': triggered,
                'correct': triggered == should_trigger
            })
        
        # 3. 优化描述
        if iteration_num < self.max_iterations:
            print("\n🤖 优化描述...")
            new_description = self.optimize_description(self.current_description, train_results)
            
            if new_description != self.current_description:
                print(f"  ✓ 生成新描述：{len(new_description)} 字符")
                self.current_description = new_description
            else:
                print("  ⚠️  未生成新描述（可能已收敛）")
                return False
        
        return True
    
    def run(self):
        """运行完整的优化循环"""
        print(f"\n{'='*60}")
        print(f"🚀 技能描述优化循环")
        print(f"{'='*60}")
        print(f"技能路径：{self.skill_path}")
        print(f"模型：{self.model_id}")
        print(f"最大迭代次数：{self.max_iterations}")
        
        # 运行迭代
        for i in range(1, self.max_iterations + 1):
            if not self.run_iteration(i):
                print("\n⚠️  提前终止（未生成新描述）")
                break
        
        # 生成报告
        self.generate_report()
        
        # 应用最佳描述
        if self.best_description:
            self.apply_best_description()
        
        return self.best_description
    
    def generate_report(self):
        """生成优化报告"""
        print(f"\n{'='*60}")
        print(f"📊 优化报告")
        print(f"{'='*60}")
        
        # 汇总统计
        print(f"\n总迭代次数：{len(self.iteration_results)}")
        print(f"最佳测试得分：{self.best_test_score:.2%}")
        
        # 每次迭代的结果
        print(f"\n迭代历史:")
        for result in self.iteration_results:
            print(f"  迭代 #{result['iteration']}: "
                  f"训练={result['train_score']:.2%}, "
                  f"测试={result['test_score']:.2%}")
        
        # 保存报告
        report_path = self.skill_path / 'optimization_report.json'
        report = {
            'skill_path': str(self.skill_path),
            'completed_at': datetime.now().isoformat(),
            'total_iterations': len(self.iteration_results),
            'best_test_score': self.best_test_score,
            'best_description': self.best_description,
            'iteration_history': self.iteration_results
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 报告已保存：{report_path}")
    
    def apply_best_description(self):
        """应用最佳描述到 SKILL.md"""
        if not self.best_description:
            return
        
        skill_md_path = self.skill_path / 'SKILL.md'
        content = skill_md_path.read_text(encoding='utf-8')
        
        # 解析 frontmatter
        end_index = content.find('---', 3)
        if end_index == -1:
            print("❌ 无法解析 SKILL.md frontmatter")
            return
        
        frontmatter_str = content[3:end_index].strip()
        frontmatter = yaml.safe_load(frontmatter_str)
        
        # 更新描述
        old_description = frontmatter.get('description', '')
        frontmatter['description'] = self.best_description
        
        # 重新构建 frontmatter
        new_frontmatter = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
        
        # 替换原内容
        new_content = f"---\n{new_frontmatter}---\n{content[end_index+3:]}"
        
        # 保存
        skill_md_path.write_text(new_content, encoding='utf-8')
        
        print(f"\n✅ 已应用最佳描述到 SKILL.md")
        print(f"  旧描述：{len(old_description)} 字符")
        print(f"  新描述：{len(self.best_description)} 字符")
        print(f"  测试得分：{self.best_test_score:.2%}")


def main():
    parser = argparse.ArgumentParser(
        description='优化技能描述以提高触发准确性',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python run_loop.py --eval-set evals/trigger-eval.json --skill-path skills/my-skill
  python run_loop.py --eval-set evals/trigger-eval.json --skill-path skills/my-skill --max-iterations 10
        '''
    )
    
    parser.add_argument('--eval-set', required=True, help='触发评估集路径（JSON）')
    parser.add_argument('--skill-path', required=True, help='技能目录路径')
    parser.add_argument('--model', default=None, help='使用的模型 ID（默认：qwen3.5-plus）')
    parser.add_argument('--max-iterations', type=int, default=5, help='最大迭代次数（默认：5）')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.eval_set):
        print(f"❌ 错误：评估集不存在：{args.eval_set}")
        sys.exit(1)
    
    if not os.path.exists(args.skill_path):
        print(f"❌ 错误：技能目录不存在：{args.skill_path}")
        sys.exit(1)
    
    # 运行优化
    optimizer = DescriptionOptimizer(
        args.eval_set,
        args.skill_path,
        args.model,
        args.max_iterations,
        args.verbose
    )
    
    best_description = optimizer.run()
    
    if best_description:
        print(f"\n🎉 优化完成!")
        print(f"\n最佳描述:")
        print(f"{best_description}")
        sys.exit(0)
    else:
        print(f"\n❌ 优化失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
