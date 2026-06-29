\# 创建脚本文件

cat > \~/Desktop/word\_sorter.py << 'EOF'

\#!/usr/bin/env python3

\# -\*- coding: utf-8 -\*-

"""

单词按首字母排序工具

支持中英文、去重、大小写处理

"""



import re

import sys



def extract\_words(text):

&#x20;   """从文本中提取单词（支持中英文）"""

&#x20;   # 英文单词（字母开头）

&#x20;   english\_words = re.findall(r'\[A-Za-z]+', text)

&#x20;   # 中文单词（2-4个中文字符）

&#x20;   chinese\_words = re.findall(r'\[\\u4e00-\\u9fff]{2,4}', text)

&#x20;   return english\_words + chinese\_words



def sort\_words(words, reverse=False, case\_sensitive=False, remove\_duplicates=True):

&#x20;   """排序单词"""

&#x20;   # 去重

&#x20;   if remove\_duplicates:

&#x20;       words = list(dict.fromkeys(words))  # 保持顺序的去重

&#x20;   

&#x20;   # 排序

&#x20;   if case\_sensitive:

&#x20;       words.sort(reverse=reverse)

&#x20;   else:

&#x20;       words.sort(key=str.lower, reverse=reverse)

&#x20;   

&#x20;   return words



def group\_by\_first\_letter(words):

&#x20;   """按首字母分组"""

&#x20;   groups = {}

&#x20;   for word in words:

&#x20;       if word and word\[0]:

&#x20;           first\_char = word\[0].upper() if word\[0].isalpha() else word\[0]

&#x20;           if first\_char not in groups:

&#x20;               groups\[first\_char] = \[]

&#x20;           groups\[first\_char].append(word)

&#x20;   return groups



def main():

&#x20;   print("\\n" + "="\*50)

&#x20;   print("📝 单词按首字母排序工具")

&#x20;   print("="\*50)

&#x20;   

&#x20;   if len(sys.argv) < 2:

&#x20;       print("\\n使用方法:")

&#x20;       print("  1. 直接传入单词: python word\_sorter.py apple banana cat")

&#x20;       print("  2. 从文件读取: python word\_sorter.py --file words.txt")

&#x20;       print("  3. 交互模式: python word\_sorter.py --interactive")

&#x20;       print("\\n选项:")

&#x20;       print("  --reverse     降序排列")

&#x20;       print("  --case-sensitive 区分大小写")

&#x20;       print("  --no-dedupe   保留重复词")

&#x20;       print("  --group       按首字母分组显示")

&#x20;       print("\\n示例:")

&#x20;       print("  python word\_sorter.py apple Cat banana dog cat")

&#x20;       print("  python word\_sorter.py 苹果 香蕉 橙子 葡萄")

&#x20;       print("  python word\_sorter.py --group 北京 上海 广州 深圳")

&#x20;       print()

&#x20;       sys.exit(1)

&#x20;   

&#x20;   # 解析参数

&#x20;   words = \[]

&#x20;   use\_group = False

&#x20;   reverse = False

&#x20;   case\_sensitive = False

&#x20;   remove\_duplicates = True

&#x20;   

&#x20;   args = sys.argv\[1:]

&#x20;   

&#x20;   if '--group' in args:

&#x20;       use\_group = True

&#x20;       args.remove('--group')

&#x20;   if '--reverse' in args:

&#x20;       reverse = True

&#x20;       args.remove('--reverse')

&#x20;   if '--case-sensitive' in args:

&#x20;       case\_sensitive = True

&#x20;       args.remove('--case-sensitive')

&#x20;   if '--no-dedupe' in args:

&#x20;       remove\_duplicates = False

&#x20;       args.remove('--no-dedupe')

&#x20;   

&#x20;   # 获取单词

&#x20;   if '--interactive' in args:

&#x20;       text = input("\\n请输入单词或文本: ")

&#x20;       words = extract\_words(text)

&#x20;   elif '--file' in args:

&#x20;       file\_idx = args.index('--file')

&#x20;       if file\_idx + 1 < len(args):

&#x20;           with open(args\[file\_idx + 1], 'r', encoding='utf-8') as f:

&#x20;               words = extract\_words(f.read())

&#x20;   else:

&#x20;       # 直接传入单词

&#x20;       words = args

&#x20;   

&#x20;   if not words:

&#x20;       print("❌ 未找到有效单词")

&#x20;       sys.exit(1)

&#x20;   

&#x20;   # 排序

&#x20;   sorted\_words = sort\_words(words, reverse, case\_sensitive, remove\_duplicates)

&#x20;   

&#x20;   # 输出结果

&#x20;   print(f"\\n📊 输入单词数: {len(words)}")

&#x20;   if remove\_duplicates and len(sorted\_words) < len(words):

&#x20;       print(f"📊 去重后: {len(sorted\_words)} 个")

&#x20;   

&#x20;   print(f"\\n{'='\*50}")

&#x20;   print("📝 排序结果:")

&#x20;   print('='\*50)

&#x20;   

&#x20;   if use\_group:

&#x20;       groups = group\_by\_first\_letter(sorted\_words)

&#x20;       for letter in sorted(groups.keys()):

&#x20;           print(f"\\n【{letter}】({len(groups\[letter])}个)")

&#x20;           for word in groups\[letter]:

&#x20;               print(f"  • {word}")

&#x20;   else:

&#x20;       for i, word in enumerate(sorted\_words, 1):

&#x20;           print(f"{i:3}. {word}")

&#x20;   

&#x20;   # 统计信息

&#x20;   print(f"\\n{'='\*50}")

&#x20;   print(f"📈 统计:")

&#x20;   print(f"   首字母分布: {len(group\_by\_first\_letter(sorted\_words))} 个字母")

&#x20;   if len(sorted\_words) > 0:

&#x20;       print(f"   最长单词: {max(sorted\_words, key=len)} ({len(max(sorted\_words, key=len))}字符)")

&#x20;   print('='\*50)



if \_\_name\_\_ == "\_\_main\_\_":

&#x20;   main()

EOF



\# 赋予执行权限（Windows 不需要）

\# chmod +x \~/Desktop/word\_sorter.py

