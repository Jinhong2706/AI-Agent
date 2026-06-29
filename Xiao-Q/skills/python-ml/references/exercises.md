# Python 练习题题库

> 按主题分类，每题包含：题目描述、难度、提示、答案和解析。
> 代码保持英文，讲解用中文。

---

## 一、变量与数据类型

### 题目 1（初级）
**题目：** 创建三个变量：`name`（字符串，值为你的名字）、`age`（整数，值为你的年龄）、`is_student`（布尔值，表示是否为学生）。然后打印一句介绍自己的话，格式为：`"My name is ___, I am ___ years old."`

<details>
<summary>💡 提示</summary>

用 f-string 可以方便地把变量嵌入字符串。

</details>

<details>
<summary>✅ 答案</summary>

```python
name = "Alice"
age = 25
is_student = True

print(f"My name is {name}, I am {age} years old.")
```
**解析：** f-string 是在字符串前加 `f`，然后用 `{变量名}` 嵌入变量的值。

</details>

---

### 题目 2（初级）
**题目：** 下面代码的输出是什么？
```python
a = 10
b = 3
print(a // b)
print(a % b)
```

<details>
<summary>✅ 答案</summary>

```
3
1
```
**解析：** `//` 是整除（取商），`%` 是取余（取余数）。10 除以 3，商是 3，余数是 1。

</details>

---

## 二、字符串操作

### 题目 3（初级）
**题目：** 给定一个字符串 `text = "  Hello Python World  "`，编写代码完成以下操作：
1. 去掉首尾空格
2. 全部转为小写
3. 把 "python" 替换成 "Java"

<details>
<summary>✅ 答案</summary>

```python
text = "  Hello Python World  "
print(text.strip())        # "Hello Python World"
print(text.strip().lower()) # "hello python world"
print(text.strip().replace("Python", "Java")) # "Hello Java World"
```

</details>

---

### 题目 4（中级）
**题目：** 写一个函数 `count_vowels(s)`，统计字符串中有多少个元音字母（a, e, i, o, u，不区分大小写）。

**示例：**
```python
count_vowels("Hello World")  # 返回 3（e, o, o）
```

<details>
<summary>💡 提示</summary>

可以遍历字符串的每个字符，检查它是否在元音字母列表中。

</details>

<details>
<summary>✅ 答案</summary>

```python
def count_vowels(s):
    vowels = "aeiou"
    count = 0
    for char in s.lower():
        if char in vowels:
            count += 1
    return count

print(count_vowels("Hello World"))  # 3
```
**解析：** 
- `s.lower()` 把字符串全部转为小写，这样不用分别检查大小写
- `char in vowels` 检查字符是否是元音字母

</details>

---

## 三、列表操作

### 题目 5（初级）
**题目：** 有一个数字列表 `numbers = [1, 2, 3, 4, 5]`，编写代码：
1. 在列表末尾添加数字 6
2. 删除数字 3
3. 打印列表中的第二个元素和倒数第一个元素

<details>
<summary>✅ 答案</summary>

```python
numbers = [1, 2, 3, 4, 5]
numbers.append(6)
numbers.remove(3)
print(numbers[1])    # 2（第二个元素，索引为1）
print(numbers[-1])   # 6（倒数第一个）
print(numbers)        # [1, 2, 4, 5, 6]
```

</details>

---

### 题目 6（中级）
**题目：** 写一个函数 `find_max(numbers)`，不接受内置的 `max()` 函数，自己找出列表中的最大值。

<details>
<summary>✅ 答案</summary>

```python
def find_max(numbers):
    if len(numbers) == 0:
        return None
    max_num = numbers[0]
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num

print(find_max([3, 7, 2, 9, 4]))  # 9
```
**解析：** 先假设第一个元素是最大的，然后遍历列表，遇到更大的就更新。

</details>

---

### 题目 7（中级）
**题目：** 写一个函数 `reverse_list(lst)`，反转一个列表（不使用内置的 `reverse()` 或切片 `[::-1]`）。

<details>
<summary>✅ 答案</summary>

```python
def reverse_list(lst):
    reversed_lst = []
    for i in range(len(lst) - 1, -1, -1):
        reversed_lst.append(lst[i])
    return reversed_lst

print(reverse_list([1, 2, 3, 4]))  # [4, 3, 2, 1]
```
**解析：** `range(len(lst) - 1, -1, -1)` 从最后一个索引倒数到 0。

</details>

---

## 四、字典操作

### 题目 8（初级）
**题目：** 有一个字典记录学生的成绩：
```python
scores = {"Alice": 85, "Bob": 92, "Charlie": 78}
```
编写代码：
1. 添加新学生 David，成绩 88
2. 把 Alice 的成绩改成 90
3. 打印所有及格的学生（成绩 >= 60）

<details>
<summary>✅ 答案</summary>

```python
scores = {"Alice": 85, "Bob": 92, "Charlie": 78}
scores["David"] = 88
scores["Alice"] = 90

for name, score in scores.items():
    if score >= 60:
        print(f"{name}: {score}")
```

</details>

---

## 五、条件语句与循环

### 题目 9（初级）
**题目：** 写一个程序，判断一个数字是奇数还是偶数。如果是偶数，打印 `"Even"`，否则打印 `"Odd"`。

<details>
<summary>💡 提示</summary>

偶数能被 2 整除，即余数为 0。`%` 运算符可以求余数。

</details>

<details>
<summary>✅ 答案</summary>

```python
num = int(input("Enter a number: "))
if num % 2 == 0:
    print("Even")
else:
    print("Odd")
```

</details>

---

### 题目 10（中级）
**题目：** 打印九九乘法表（格式整齐，每句如 `"3 x 4 = 12"`）。

<details>
<summary>✅ 答案</summary>

```python
for i in range(1, 10):
    for j in range(1, i + 1):
        print(f"{j} x {i} = {i * j}", end="\t")
    print()  # 换行
```
**解析：** 
- 外层循环控制行（`i`），内层循环控制列（`j`）
- `end="\t"` 让打印不换行，用制表符分隔
- `print()` 不带参数就是打印一个换行

</details>

---

### 题目 11（中级）
**题目：** 写一个函数 `fizz_buzz(n)`，打印从 1 到 n 的 FizzBuzz：
- 能被 3 整除的打印 `"Fizz"`
- 能被 5 整除的打印 `"Buzz"`
- 能同时被 3 和 5 整除的打印 `"FizzBuzz"`
- 其他情况打印数字本身

<details>
<summary>✅ 答案</summary>

```python
def fizz_buzz(n):
    for i in range(1, n + 1):
        if i % 3 == 0 and i % 5 == 0:
            print("FizzBuzz")
        elif i % 3 == 0:
            print("Fizz")
        elif i % 5 == 0:
            print("Buzz")
        else:
            print(i)

fizz_buzz(15)
```
**注意：** 先检查同时被 3 和 5 整除的情况，顺序不能反！

</details>

---

## 六、函数

### 题目 12（初级）
**题目：** 写一个函数 `greet(name, greeting="Hello")`，接受一个名字和一个可选的问候语，返回完整的问候语。

**示例：**
```python
greet("Alice")              # "Hello, Alice!"
greet("Alice", "Hi")       # "Hi, Alice!"
```

<details>
<summary>✅ 答案</summary>

```python
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

print(greet("Alice"))
print(greet("Alice", "Hi"))
```

</details>

---

### 题目 13（中级）
**题目：** 写一个函数 `fibonacci(n)`，返回斐波那契数列的第 n 项（从 0 开始：`fibonacci(0) = 0`, `fibonacci(1) = 1`）。

<details>
<summary>💡 提示</summary>

斐波那契数列：每一项等于前两项之和。0, 1, 1, 2, 3, 5, 8...

</details>

<details>
<summary>✅ 答案（方法1：循环，推荐）</summary>

```python
def fibonacci(n):
    if n == 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

print(fibonacci(10))  # 55
```

</details>

---

## 七、综合题

### 题目 14（中级）
**题目：** 写一个程序，模拟一个简单的购物车：
1. 用字典存储商品名称和价格，如 `{"apple": 3, "banana": 2, "milk": 5}`
2. 让用户输入商品名称和数量（用 `input()`）
3. 计算总价并打印购物清单

<details>
<summary>✅ 答案</summary>

```python
products = {"apple": 3, "banana": 2, "milk": 5}
cart = {}

print("Available products:", list(products.keys()))
print("Enter 'done' when finished.")

while True:
    name = input("Enter product name: ")
    if name == "done":
        break
    if name not in products:
        print("Product not found!")
        continue
    quantity = int(input("Enter quantity: "))
    cart[name] = cart.get(name, 0) + quantity

# 计算总价
total = 0
print("\n=== Your Cart ===")
for name, qty in cart.items():
    subtotal = products[name] * qty
    total += subtotal
    print(f"{name} x {qty} = {subtotal}")
print(f"Total: {total}")
```

</details>

---

### 题目 15（高级）
**题目：** 写一个函数 `word_frequency(text)`，统计一段英文文本中每个单词出现的频率（不区分大小写，忽略标点符号），返回字典。

**示例：**
```python
word_frequency("Hello hello world!")  
# 返回 {"hello": 2, "world": 1}
```

<details>
<summary>✅ 答案</summary>

```python
import string

def word_frequency(text):
    # 转小写并去掉标点符号
    text = text.lower()
    for p in string.punctuation:
        text = text.replace(p, "")
    
    words = text.split()
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    return freq

print(word_frequency("Hello hello world!"))
# {'hello': 2, 'world': 1}
```
**解析：**
- `string.punctuation` 包含所有标点符号：`!"#$%&'()*+,-./:;<=>?@[\]^_{|}~`
- `freq.get(word, 0)` 如果键不存在返回 0，存在则返回当前值

</details>
