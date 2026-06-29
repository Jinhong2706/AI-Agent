#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化技能模板脚本

用法:
    python init_skill.py <skill-name> --path <output-directory> [--resources scripts,references,assets] [--examples]

示例:
    python init_skill.py my-skill --path skills/public
    python init_skill.py my-skill --path skills/public --resources scripts,references
    python init_skill.py my-skill --path skills/public --resources scripts --examples
"""

import os
import sys
import argparse
from datetime import datetime

# 设置标准输出编码为 UTF-8（解决 Windows GBK 编码问题）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def create_skill_template(skill_name, output_path, resources=None, include_examples=False):
    """
    创建技能模板目录结构
    
    Args:
        skill_name: 技能名称（将用作目录名）
        output_path: 输出目录路径
        resources: 要创建的资源目录列表 ['scripts', 'references', 'assets']
        include_examples: 是否包含示例文件
    """
    if resources is None:
        resources = []
    
    # 规范化技能名称（只允许字母、数字、连字符）
    skill_name = skill_name.lower().replace(' ', '-').replace('_', '-')
    skill_name = ''.join(c if c.isalnum() or c == '-' else '-' for c in skill_name)
    
    # 创建技能目录
    skill_dir = os.path.join(output_path, skill_name)
    os.makedirs(skill_dir, exist_ok=True)
    
    print(f"✅ 创建技能目录：{skill_dir}")
    
    # 创建资源目录
    for resource in resources:
        resource_dir = os.path.join(skill_dir, resource)
        os.makedirs(resource_dir, exist_ok=True)
        print(f"  ✅ 创建资源目录：{resource}/")
    
    # 创建 SKILL.md 模板
    skill_md_path = os.path.join(skill_dir, 'SKILL.md')
    skill_md_content = generate_skill_md_template(skill_name, resources)
    
    with open(skill_md_path, 'w', encoding='utf-8') as f:
        f.write(skill_md_content)
    
    print(f"  ✅ 创建 SKILL.md 模板")
    
    # 创建示例文件（如果请求）
    if include_examples:
        create_example_files(skill_dir, resources)
        print(f"  ✅ 创建示例文件")
    
    # 创建 evals 目录和模板
    evals_dir = os.path.join(skill_dir, 'evals')
    os.makedirs(evals_dir, exist_ok=True)
    
    evals_json_path = os.path.join(evals_dir, 'evals.json')
    evals_json_content = generate_evals_json_template(skill_name)
    
    with open(evals_json_path, 'w', encoding='utf-8') as f:
        f.write(evals_json_content)
    
    print(f"  ✅ 创建 evals/evals.json 模板")
    
    print(f"\n🎉 技能 '{skill_name}' 初始化完成！")
    print(f"\n下一步:")
    print(f"  1. 编辑 {skill_dir}/SKILL.md 添加你的技能逻辑")
    print(f"  2. 在 {skill_dir}/evals/evals.json 中添加测试用例")
    print(f"  3. 运行测试验证技能工作正常")
    print(f"  4. 使用 package_skill.py 打包技能")
    
    return skill_dir

def generate_skill_md_template(skill_name, resources):
    """生成 SKILL.md 模板内容"""
    
    # 根据资源目录生成引用
    resources_section = ""
    if 'scripts' in resources:
        resources_section += """
### Scripts

在 `scripts/` 目录中添加可执行脚本：

```python
# scripts/example.py
def example_function():
    \"\"\"示例函数\"\"\"
    pass
```
"""
    
    if 'references' in resources:
        resources_section += """
### References

在 `references/` 目录中添加参考文档：

- `references/domain-knowledge.md` - 领域知识
- `references/api-reference.md` - API 参考
- `references/examples.md` - 使用示例
"""
    
    if 'assets' in resources:
        resources_section += """
### Assets

在 `assets/` 目录中添加资源文件：

- `assets/template.html` - HTML 模板
- `assets/logo.png` - 品牌标识
"""
    
    template = f"""---
name: {skill_name}
description: [在此描述技能的功能和触发条件。包括技能做什么以及何时使用它。例如："处理 PDF 文件的技能。当需要提取 PDF 文本、合并 PDF、旋转页面或转换 PDF 格式时使用。"]
---

# {skill_name.replace('-', ' ').title()}

[在此提供技能的详细使用说明。这是技能触发后加载的主要内容。]

## 何时使用此技能

[明确说明技能的触发条件和使用场景。]

## 核心功能

### 功能 1

[描述第一个核心功能]

**示例**:
```
用户请求示例
```

**输出**:
```
预期输出示例
```

### 功能 2

[描述第二个核心功能]

## 工作流程

[如果技能涉及多步骤流程，在此描述:]

1. **步骤 1**: [描述]
2. **步骤 2**: [描述]
3. **步骤 3**: [描述]

## 输出格式

[如果技能生成特定格式的输出，在此定义:]

```
[输出格式模板]
```

{resources_section}

## 最佳实践

- [最佳实践 1]
- [最佳实践 2]
- [最佳实践 3]

## 常见错误和解决方案

### 错误 1

**问题**: [描述常见问题]

**解决方案**: [描述如何解决]

### 错误 2

**问题**: [描述常见问题]

**解决方案**: [描述如何解决]

## 测试用例

参考 `evals/evals.json` 中的测试用例。

## 版本历史

- **v1.0.0** ({datetime.now().strftime('%Y-%m-%d')}) - 初始版本

---

**注意**: 这是一个模板文件。请替换所有 [方括号] 中的内容与你的技能特定信息。
"""
    
    return template

def generate_evals_json_template(skill_name):
    """生成 evals.json 模板内容"""
    
    template = f"""{{
  "skill_name": "{skill_name}",
  "version": "1.0.0",
  "description": "{skill_name.replace('-', ' ').title()} 测试用例",
  "evals": [
    {{
      "id": 1,
      "eval_name": "基本功能测试",
      "prompt": "[在此输入测试 prompt - 用户可能会说什么来触发此技能]",
      "expected_output": "[描述预期的输出]",
      "files": [],
      "assertions": [
        {{
          "name": "包含必需文件",
          "type": "file_exists",
          "expected": "SKILL.md",
          "description": "验证技能包含必需的 SKILL.md 文件"
        }},
        {{
          "name": "包含 description 字段",
          "type": "contains",
          "expected": "description:",
          "description": "验证 SKILL.md 包含 description 字段"
        }}
      ]
    }},
    {{
      "id": 2,
      "eval_name": "边缘情况测试",
      "prompt": "[输入边缘情况的测试 prompt]",
      "expected_output": "[描述边缘情况的预期输出]",
      "files": [],
      "assertions": [
        {{
          "name": "处理边缘情况",
          "type": "contains",
          "expected": "[期望在输出中找到的关键词]",
          "description": "验证技能正确处理边缘情况"
        }}
      ]
    }}
  ]
}}
"""
    
    return template

def create_example_files(skill_dir, resources):
    """创建示例文件"""
    
    # 创建示例脚本
    if 'scripts' in resources:
        scripts_dir = os.path.join(skill_dir, 'scripts')
        example_script = os.path.join(scripts_dir, 'example.py')
        
        with open(example_script, 'w', encoding='utf-8') as f:
            f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例脚本 - 替换为实际功能
"""

def example_function(input_data):
    """
    示例函数
    
    Args:
        input_data: 输入数据
        
    Returns:
        处理结果
    """
    # TODO: 实现实际逻辑
    result = {
        "status": "success",
        "message": "处理完成",
        "data": input_data
    }
    return result

if __name__ == "__main__":
    # 测试示例
    test_input = "测试数据"
    output = example_function(test_input)
    print(f"输入：{test_input}")
    print(f"输出：{output}")
''')
    
    # 创建示例参考文档
    if 'references' in resources:
        references_dir = os.path.join(skill_dir, 'references')
        example_ref = os.path.join(references_dir, 'example.md')
        
        with open(example_ref, 'w', encoding='utf-8') as f:
            f.write('''# 示例参考文档

这是参考文档的示例。参考文档用于存储详细信息，保持 SKILL.md 简洁。

## 何时使用此文档

当需要详细信息时加载此文档，例如：
- 用户询问特定功能
- 需要详细的 API 参考
- 需要复杂的示例

## 内容

### 主题 1

详细内容...

### 主题 2

详细内容...

## 相关资源

- [相关文档链接]
- [API 参考]
- [教程]
''')
    
    # 创建示例资产
    if 'assets' in resources:
        assets_dir = os.path.join(skill_dir, 'assets')
        example_asset = os.path.join(assets_dir, 'template.txt')
        
        with open(example_asset, 'w', encoding='utf-8') as f:
            f.write('''这是示例模板文件。

变量:
- {{variable1}} - 第一个变量
- {{variable2}} - 第二个变量

用法:
替换 {{variable}} 为实际值。
''')

def main():
    parser = argparse.ArgumentParser(
        description='初始化技能模板',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python init_skill.py my-skill --path skills/public
  python init_skill.py my-skill --path skills/public --resources scripts,references
  python init_skill.py my-skill --path skills/public --resources scripts --examples
        '''
    )
    
    parser.add_argument('skill_name', help='技能名称（将用作目录名）')
    parser.add_argument('--path', '-p', required=True, help='输出目录路径')
    parser.add_argument('--resources', '-r', help='要创建的资源目录（逗号分隔：scripts,references,assets）')
    parser.add_argument('--examples', '-e', action='store_true', help='包含示例文件')
    
    args = parser.parse_args()
    
    # 解析资源目录
    resources = None
    if args.resources:
        resources = [r.strip() for r in args.resources.split(',')]
        valid_resources = {'scripts', 'references', 'assets'}
        for r in resources:
            if r not in valid_resources:
                print(f"❌ 错误：无效的资源类型 '{r}'。有效选项：{', '.join(valid_resources)}")
                sys.exit(1)
    
    # 检查输出目录是否存在
    if not os.path.exists(args.path):
        print(f"❌ 错误：输出目录不存在：{args.path}")
        sys.exit(1)
    
    # 创建技能模板
    create_skill_template(args.skill_name, args.path, resources, args.examples)

if __name__ == '__main__':
    main()
