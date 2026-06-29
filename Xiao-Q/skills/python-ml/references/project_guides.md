# Python 入门项目分步教程

> 面向零基础用户，每个项目分解为小步骤，跟着做就能完成。

---

## 项目一：待办事项 CLI（命令行小工具）

**适合阶段：** 学完函数之后
**学到什么：** 列表操作、函数、循环、用户输入

### 最终效果
```
=== Todo List ===
1. Add task
2. View tasks
3. Remove task
4. Quit
Choose an option: 1
Enter task: Learn Python
Task added!
```

### 步骤 1：搭建基本框架

```python
def show_menu():
    print("=== Todo List ===")
    print("1. Add task")
    print("2. View tasks")
    print("3. Remove task")
    print("4. Quit")

# 主程序
while True:
    show_menu()
    choice = input("Choose an option: ")
    if choice == "4":
        break
```

### 步骤 2：添加任务

```python
tasks = []  # 用列表存储所有任务

def add_task():
    task = input("Enter task: ")
    tasks.append(task)
    print("Task added!")

# 在主循环中：
if choice == "1":
    add_task()
```

### 步骤 3：查看任务

```python
def view_tasks():
    if len(tasks) == 0:
        print("No tasks yet!")
    else:
        for i in range(len(tasks)):
            print(f"{i + 1}. {tasks[i]}")

# 在主循环中：
if choice == "2":
    view_tasks()
```

### 步骤 4：删除任务

```python
def remove_task():
    view_tasks()
    task_num = int(input("Enter task number to remove: "))
    index = task_num - 1
    if 0 <= index < len(tasks):
        removed = tasks.pop(index)
        print(f"Removed: {removed}")
    else:
        print("Invalid task number!")

# 在主循环中：
if choice == "3":
    remove_task()
```

### 完整代码
参考 `assets/todo_cli_example.py`

---

## 项目二：密码生成器

**适合阶段：** 学完基础语法
**学到什么：** 随机数、字符串操作、函数

### 最终效果
```
How many passwords? 3
How many characters? 12
1. xK9#mP2@nQ_
2. aB7!cD3$eF*
3. 8@nM#pQ2$kL
```

### 核心步骤

**步骤 1：** 导入 `random` 和 `string` 模块
```python
import random
import string
```

**步骤 2：** 定义字符集（大小写字母 + 数字 + 特殊符号）
```python
chars = string.ascii_letters + string.digits + string.punctuation
```

**步骤 3：** 用 `random.choice()` 随机选字符，循环生成指定长度
```python
def generate_password(length):
    password = ""
    for _ in range(length):
        password += random.choice(chars)
    return password
```

### 完整代码
参考 `assets/password_generator.py`

---

## 项目三：天气查询工具（爬虫入门）

**适合阶段：** 学完基础 + 了解 requests 库
**学到什么：** HTTP 请求、API 使用、JSON 解析

### 前提：安装 requests
```bash
pip install requests
```

### 使用免费天气 API
推荐使用 [wttr.in](https://wttr.in) — 不需要 API key！

```python
import requests

def get_weather(city):
    url = f"https://wttr.in/{city}?format=3"
    response = requests.get(url)
    print(response.text)

get_weather("Beijing")
# 输出：Beijing: ⛅️ +22°C
```

### 更详细的版本
```python
import requests
import json

def get_weather_detail(city):
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url)
    data = response.json()
    
    current = data["current_condition"][0]
    temp = current["temp_C"]
    desc = current["weatherDesc"][0]["value"]
    
    print(f"城市：{city}")
    print(f"温度：{temp}°C")
    print(f"天气：{desc}")

get_weather_detail("Beijing")
```

### 完整代码
参考 `assets/weather_scraper.py`

---

## 项目四：简单计算器

**适合阶段：** 学完函数和条件语句
**学到什么：** 函数、条件判断、循环、异常处理

### 功能
```
=== Calculator ===
1. Add
2. Subtract
3. Multiply
4. Divide
5. Quit
Choose: 1
Enter first number: 10
Enter second number: 5
Result: 15
```

### 核心代码框架

```python
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "Error: Cannot divide by zero!"
    return a / b

# 主程序
while True:
    print("=== Calculator ===")
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")
    print("5. Quit")
    
    choice = input("Choose: ")
    if choice == "5":
        break
    
    a = float(input("Enter first number: "))
    b = float(input("Enter second number: "))
    
    if choice == "1":
        print(f"Result: {add(a, b)}")
    elif choice == "2":
        print(f"Result: {subtract(a, b)}")
    elif choice == "3":
        print(f"Result: {multiply(a, b)}")
    elif choice == "4":
        print(f"Result: {divide(a, b)}")
```

---

## 项目五：文件整理工具

**适合阶段：** 学完文件操作和 `os` 模块
**学到什么：** `os` 模块、文件操作、字典统计

### 功能
统计指定文件夹中各类文件的数量：
```
Files in C:\Users\username\Downloads:
  .pdf  : 5 files
  .jpg  : 12 files
  .py   : 8 files
  other : 3 files
```

### 核心代码

```python
import os

def count_file_types(folder_path):
    counts = {}
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)):
            ext = os.path.splitext(filename)[1].lower()
            if ext == "":
                ext = "no extension"
            counts[ext] = counts.get(ext, 0) + 1
    
    for ext, count in counts.items():
        print(f"  {ext} : {count} files")

count_file_types(r"C:\Users\wangheran\Downloads")
```

---

## 学习路线建议

```
第1-2周：项目一（待办 CLI）+ 项目四（计算器）
          → 巩固基础语法和函数

第3-4周：项目二（密码生成器）
          → 学习模块使用

第5-6周：项目三（天气查询）
          → 入门网络请求和 API

第7-8周：项目五（文件整理工具）
          → 学习文件操作和 os 模块

之后：   根据兴趣选择方向
         - Web 开发：学 Flask / Django
         - 数据分析：学 pandas / matplotlib
         - 爬虫：学 requests / BeautifulSoup / scrapy
```
