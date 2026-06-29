# Python 常见错误及解决方法

> 零基础用户最常遇到的错误，附带中文解释和正确写法。

---

## 1. SyntaxError（语法错误）

### 忘记冒号 `:`
```python
# ❌ 错误
if age > 18
    print("Adult")

# ✅ 正确
if age > 18:
    print("Adult")
```
**解释：** `if`、`for`、`while`、`def`、`class` 后面必须加冒号 `:`。

---

### 括号、引号没有闭合
```python
# ❌ 错误
print("Hello World)
msg = "Hello

# ✅ 正确
print("Hello World")
msg = "Hello"
```
**解释：** 每个 opening 的引号或括号，都要有对应的 closing。

---

## 2. IndentationError（缩进错误）

```python
# ❌ 错误：缩进不一致
if age > 18:
print("Adult")   # 没有缩进！

# ❌ 错误：混用空格和 Tab
if age > 18:
    print("Adult")   # 用空格
	if age > 60:     # 用 Tab（不一致！）
	    print("Senior")

# ✅ 正确：统一用 4 个空格
if age > 18:
    print("Adult")
    if age > 60:
        print("Senior")
```
**解释：** Python 用缩进来表示代码块，同一代码块必须对齐。推荐使用 4 个空格，不要混用 Tab 和空格。

---

## 3. NameError（变量未定义）

```python
# ❌ 错误
print(message)   # message 还没有定义

# ✅ 正确
message = "Hello"
print(message)
```
**常见原因：**
- 变量名拼错了
- 变量在使用前没有赋值
- 变量定义在函数内部，外部无法访问

---

## 4. TypeError（类型错误）

```python
# ❌ 错误：字符串和数字不能直接相加
age = 25
print("I am " + age + " years old")

# ✅ 正确方法1：转成字符串
print("I am " + str(age) + " years old")

# ✅ 正确方法2：用 f-string（推荐）
print(f"I am {age} years old")
```
**解释：** 不同类型的数据不能直接用 `+` 连接，需要先用 `str()` 转换，或者用 f-string。

---

## 5. IndexError（索引越界）

```python
# ❌ 错误
fruits = ["apple", "banana"]
print(fruits[5])   # 列表只有2个元素，索引5不存在

# ✅ 正确：先检查长度
fruits = ["apple", "banana"]
if len(fruits) > 5:
    print(fruits[5])
else:
    print("Index out of range!")
```
**解释：** 列表索引从 `0` 开始，最大索引是 `len(list) - 1`。

---

## 6. KeyError（键不存在）

```python
# ❌ 错误
student = {"name": "Alice"}
print(student["age"])   # "age" 这个键不存在

# ✅ 正确方法1：用 get()
print(student.get("age"))        # None（不会报错）
print(student.get("age", 18))   # 18（默认值）

# ✅ 正确方法2：先检查
if "age" in student:
    print(student["age"])
```

---

## 7. AttributeError（属性错误）

```python
# ❌ 错误
numbers = [1, 2, 3]
numbers.append(4)    # 正确
numbers.push(5)      # 错误！列表没有 push 方法

# ✅ 正确：查看正确的方法名
# 列表用 append()，不是 push()
numbers.append(5)
```
**解释：** 每个数据类型有自己支持的方法，用错方法名会报这个错。可以查文档或用 `dir()` 查看支持的方法。

---

## 8. 无限循环

```python
# ❌ 危险！永远不会停止
while True:
    print("Hello")

# ❌ 危险！条件永远为 True
count = 0
while count < 5:
    print(count)
    # 忘记 count += 1 了！

# ✅ 正确
count = 0
while count < 5:
    print(count)
    count += 1   # 一定要改变循环条件！
```
**如何停止无限循环：** 在终端按 `Ctrl + C`。

---

## 9. 变量作用域问题

```python
# ❌ 错误：在函数内修改全局变量
total = 0

def add(x):
    total = total + x   # UnboundLocalError!
    return total

# ✅ 正确方法1：用参数和返回值
def add(total, x):
    return total + x

# ✅ 正确方法2：用 global（不推荐，尽量不用）
total = 0
def add(x):
    global total
    total = total + x
```

---

## 10. 编码问题（中文乱码）

```python
# ❌ 可能出错（Python 3 通常没问题，但读文件时要注意）
with open("notes.txt", "r") as f:
    print(f.read())

# ✅ 正确：指定编码
with open("notes.txt", "r", encoding="utf-8") as f:
    print(f.read())
```

---

## 调试技巧

### 用 `print()` 调试（最简单的方法）
```python
def calculate(x, y):
    print(f"DEBUG: x={x}, y={y}")  # 看看变量的值对不对
    result = x + y
    print(f"DEBUG: result={result}") # 看看计算结果对不对
    return result
```

### 用 `type()` 检查类型
```python
age = input("Enter age: ")   # input() 返回的是字符串！
print(type(age))              # <class 'str'>
age = int(age)               # 需要转换成整数
```

### 读错误信息的技巧
```
Traceback (most recent call last):
  File "main.py", line 3, in <module>
    print(message)
NameError: name 'message' is not defined
```
- **Traceback** 告诉你错误发生在哪里
- **最后一行** 告诉你错误类型（`NameError`）和原因（`message` 未定义）
- **line 3** 告诉你错误在第几行，去那一行附近找问题
