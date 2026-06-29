# Python 基础概念速查表

> 面向零基础用户的中文速查表，代码保持英文。

---

## 1. 变量与赋值

```python
# 变量是存储数据的容器，用 = 赋值
age = 25
name = "Alice"
price = 9.99
is_student = True
```

**命名规则：**
- 只能包含字母、数字、下划线（`_`）
- 不能以数字开头
- 区分大小写（`age` 和 `Age` 不同）
- 推荐使用小写字母 + 下划线（`my_name`）

---

## 2. 数据类型

| 类型 | 英文 | 示例 | 说明 |
|------|------|------|------|
| 整数 | `int` | `42`, `-3` | 没有小数点的数字 |
| 浮点数 | `float` | `3.14`, `-0.5` | 有小数点的数字 |
| 字符串 | `str` | `"hello"`, `'Python'` | 用引号包裹的文本 |
| 布尔值 | `bool` | `True`, `False` | 只有两个值 |
| 空值 | `NoneType` | `None` | 表示"没有值" |

**查看类型：**
```python
print(type(42))        # <class 'int'>
print(type("hello"))   # <class 'str'>
```

---

## 3. 运算符

**算术运算符：**

```python
a = 10
b = 3
print(a + b)   # 13  加法
print(a - b)   # 7   减法
print(a * b)   # 30  乘法
print(a / b)   # 3.333...  除法（结果是浮点数）
print(a // b)  # 3   整除
print(a % b)   # 1   取余
print(a ** b)  # 1000  幂运算（10的3次方）
```

**比较运算符：**（结果永远是 `True` 或 `False`）

```python
print(5 > 3)    # True
print(5 == 3)   # False  注意：两个等号是比较
print(5 != 3)   # True   不等于
```

**逻辑运算符：**

```python
print(True and False)  # False  与（两边都要 True）
print(True or False)   # True   或（一边 True 就行）
print(not True)        # False  非（取反）
```

---

## 4. 字符串常用操作

```python
s = "Hello Python"

# 字符串拼接
greeting = "Hello" + " " + "World"   # "Hello World"

# f-string 格式化（推荐）
name = "Alice"
age = 25
print(f"My name is {name}, I am {age} years old.")
# 输出：My name is Alice, I am 25 years old.

# 常用方法
print(s.lower())      # "hello python"
print(s.upper())      # "HELLO PYTHON"
print(len(s))         # 12  （字符串长度）
print(s.replace("Python", "World"))  # "Hello World"
```

---

## 5. 列表 (list)

```python
# 创建列表
shopping_list = ["apple", "banana", "milk"]

# 访问元素（索引从 0 开始！）
print(shopping_list[0])   # "apple"
print(shopping_list[-1])  # "milk"（倒数第一个）

# 修改元素
shopping_list[1] = "orange"

# 常用方法
shopping_list.append("bread")     # 末尾添加
shopping_list.remove("apple")     # 删除指定元素
print(len(shopping_list))         # 列表长度
```

**切片：**
```python
numbers = [0, 1, 2, 3, 4, 5]
print(numbers[1:4])   # [1, 2, 3]  从索引1到3（不包括4）
print(numbers[:3])    # [0, 1, 2]  从头开始
print(numbers[3:])    # [3, 4, 5]  到末尾
```

---

## 6. 字典 (dict)

```python
# 创建字典：键值对
student = {
    "name": "Alice",
    "age": 25,
    "is_student": True
}

# 访问值
print(student["name"])        # "Alice"
print(student.get("age"))    # 25（推荐用 get，键不存在不会报错）

# 修改和添加
student["age"] = 26
student["city"] = "Beijing"  # 不存在的键会自动添加

# 遍历字典
for key, value in student.items():
    print(f"{key}: {value}")
```

---

## 7. 条件语句

```python
age = 18

if age >= 18:
    print("You are an adult.")
elif age >= 13:
    print("You are a teenager.")
else:
    print("You are a child.")
```

**注意缩进！** Python 用缩进（通常是 4 个空格）来表示代码块，这很重要！

---

## 8. 循环

**for 循环（遍历序列）：**
```python
fruits = ["apple", "banana", "orange"]
for fruit in fruits:
    print(f"I like {fruit}")

# 使用 range()
for i in range(5):       # 0, 1, 2, 3, 4
    print(i)
for i in range(1, 6):    # 1, 2, 3, 4, 5
    print(i)
```

**while 循环（条件满足时重复）：**
```python
count = 0
while count < 5:
    print(count)
    count += 1   # 别忘了改变条件，否则会无限循环！
```

**break 和 continue：**
```python
for i in range(10):
    if i == 3:
        continue   # 跳过本次，继续下一次
    if i == 7:
        break      # 跳出整个循环
    print(i)
```

---

## 9. 函数

```python
# 定义函数
def greet(name):
    """向用户打招呼（这是文档字符串，解释函数功能）"""
    message = f"Hello, {name}!"
    return message

# 调用函数
result = greet("Alice")
print(result)   # "Hello, Alice!"

# 带默认参数的函数
def power(base, exponent=2):
    return base ** exponent

print(power(3))     # 9（默认平方）
print(power(3, 3))  # 27（三次方）
```

---

## 10. 文件操作

```python
# 写入文件
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("今天学习了 Python 基础！\n")
    f.write("明天继续！\n")

# 读取文件
with open("notes.txt", "r", encoding="utf-8") as f:
    content = f.read()
    print(content)
```

**为什么用 `with`？** 它会自动关闭文件，不用担心忘记！

---

## 11. 异常处理

```python
try:
    age = int(input("请输入年龄："))
    print(f"明年你就 {age + 1} 岁了！")
except ValueError:
    print("请输入一个数字！")
finally:
    print("程序结束。")
```

---

## 12. 类与对象（入门）

```python
class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def bark(self):
        print(f"{self.name} says: Woof!")

# 创建对象
my_dog = Dog("Buddy", 3)
my_dog.bark()   # Buddy says: Woof!
```
