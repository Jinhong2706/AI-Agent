---
name: python-modern
description: Python 现代编码规范（基于项目 Python 版本自动适配）
compatibility: 需要 Python 项目（pyproject.toml / setup.cfg / Pipfile / .python-version）。
---

# Python 现代编码规范

## 检测到的 Python 版本

!`PY_VER=""; if [ -f pyproject.toml ]; then PY_VER=$(grep -i 'requires-python' pyproject.toml 2>/dev/null | head -1 | sed 's/^[^=]*=[ ]*//' | tr -d "\"' "); elif [ -f setup.cfg ]; then PY_VER=$(grep -i 'python_requires' setup.cfg 2>/dev/null | head -1 | sed 's/^[^=]*=[ ]*//' | tr -d ' '); elif [ -f Pipfile ]; then PY_VER=$(grep -i 'python_version' Pipfile 2>/dev/null | head -1 | sed 's/^[^=]*=[ ]*//' | tr -d "\"' "); fi; if [ -z "$PY_VER" ] && [ -f setup.py ]; then PY_VER=$(grep -oE "python_requires\s*=\s*[\"'][^\"']+[\"']" setup.py 2>/dev/null | head -1 | sed 's/python_requires\s*=\s*//' | tr -d "\"' "); fi; if [ -z "$PY_VER" ] && [ -f .python-version ]; then PY_VER=$(head -1 .python-version 2>/dev/null | tr -d ' '); fi; if [ -z "$PY_VER" ]; then echo "unknown"; elif echo "$PY_VER" | grep -qE '^==[0-9]+\.[0-9]+'; then echo "$PY_VER" | sed 's/^==//'; elif echo "$PY_VER" | grep -qE '<[=]?[0-9]+\.[0-9]+'; then UB=$(echo "$PY_VER" | grep -oE '<[=]?[0-9]+\.[0-9]+' | head -1); if echo "$UB" | grep -q '<='; then echo "$UB" | sed 's/<=//'; else MAJ=$(echo "$UB" | sed 's/<//;s/\..*//' ); MIN=$(echo "$UB" | sed 's/<//;s/[0-9]*\.//' ); echo "${MAJ}.$((MIN - 1))"; fi; elif echo "$PY_VER" | grep -qE '^>=?[0-9]+\.[0-9]+$'; then ENV_PY=""; for cmd in .venv/bin/python venv/bin/python python3 python; do if V=$($cmd --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1) && [ -n "$V" ]; then ENV_PY="$V"; break; fi; done; echo "${ENV_PY:-3.12}"; elif echo "$PY_VER" | grep -qE '^[0-9]+\.[0-9]+'; then echo "$PY_VER" | grep -oE '^[0-9]+\.[0-9]+'; else echo "unknown"; fi`

## 使用说明

不要自行搜索版本配置文件或尝试检测版本，仅使用上方显示的版本。

**如果检测到版本（非 "unknown"）：**
- 回复："当前项目使用 Python X.Y，将严格遵循该版本及之前的现代 Python 最佳实践。如需指定其他目标版本，请告知。"
- 不要逐一列举特性，不要要求确认

**如果版本为 "unknown"：**
- 回复："无法在当前仓库中检测到 Python 版本"
- 使用 AskUserQuestion 询问："应该以哪个 Python 版本为目标？" → [3.8] / [3.9] / [3.10] / [3.11] / [3.12] / [3.13]

**编写 Python 代码时**，使用本文档中目标版本及之前的所有特性：
- 优先使用现代语法和标准库代替旧模式
- 不要使用高于目标版本的特性
- 当存在现代替代方案时，不要使用过时模式

**通用最佳实践（与版本无关）：**
- **所有 import 必须放在文件顶部**，不要在函数或条件分支内延迟导入。顶部导入能确保缺失依赖在启动/部署阶段立即暴露，而非在线上运行到特定代码路径时才触发 `ImportError`。仅在以下情况例外：
  - 可选依赖（`try: import xxx except ImportError: xxx = None`）
  - 解决循环导入（但应优先考虑重构模块结构）
- **不要使用 `from __future__ import annotations`**。它将注解变为字符串延迟求值，会破坏 Pydantic、FastAPI、dataclasses 等依赖运行时注解解析的库。PEP 563 已被 PEP 649 取代，这是一条废弃路线。需要前向引用时使用引号字符串 `"ClassName"` 代替。
- **变量类型注解强制**：所有模块级和类级变量必须显式声明类型注解，禁止仅靠命名或注释传递类型信息。

```python
# 禁止
count = 0
name = ""
items = []

# 正确
count: int = 0
name: str = ""
items: list[str] = []
```

- **函数/方法签名类型注解强制**：所有参数和返回值均需标注类型，`-> None` 也必须显式写出；多返回值使用 `tuple` 类型。

```python
# 禁止（缺少类型注解）
def process(name, count):
    return name * count

# 正确
def process(name: str, count: int) -> str:
    return name * count

# 显式写 -> None（不可省略）
def setup() -> None:
    ...

# 多返回值（Python 3.9+ 用内置 tuple，低版本用 typing.Tuple）
def fetch_page(page: int) -> tuple[list[str], int]:
    ...
    return items, total
```

- **docstring 格式（sphinx-notypes）**：使用 `:param name: 描述` 和 `:return: 描述` 格式，禁止 `:type` / `:rtype:`（类型已在签名中声明，无需重复）。

```python
# 正确
def process_text(text: str) -> str:
    """处理并返回字符串。

    :param text: 原始输入字符串
    :return: 处理后的字符串
    """
    ...

def fetch_users(page: int, size: int) -> tuple[list[str], int]:
    """分页获取用户列表。

    :param page: 页码，从 1 开始
    :param size: 每页条数
    :return: (items 列表, 总条数)
    """
    ...

# 禁止
def fetch_users(page, size):
    """
    :type page: int        # 禁止：类型已在签名中
    :type size: int        # 禁止
    :rtype: tuple          # 禁止：返回类型已在签名中
    """
    ...
```

- **match-case 规则**：条件分支 **≥ 4 个**时必须使用 `match/case`（Python 3.10+，低版本项目豁免）；3 个及以下可使用 `if/elif`。

```python
# 正确（≥ 4 个分支，Python 3.10+）
match status:
    case "pending":
        handle_pending()
    case "running":
        handle_running()
    case "done":
        handle_done()
    case "failed":
        handle_failed()
    case _:
        handle_unknown()

# 禁止（≥ 4 个分支不用 match-case）
if status == "pending":
    handle_pending()
elif status == "running":
    handle_running()
elif status == "done":
    handle_done()
elif status == "failed":
    handle_failed()
else:
    handle_unknown()

# 允许（3 个及以下分支可用 if/elif）
if role == "admin":
    grant_admin()
elif role == "editor":
    grant_editor()
else:
    grant_viewer()
```

---

## 各版本特性

### Python 3.6+

- **f-string**：使用 `f"Hello {name}"` 代替 `"Hello {}".format(name)` 或 `"Hello %s" % name`

```python
# 不要这样写：
msg = "Hello {}".format(name)
msg = "Hello %s" % name
# 应该这样写：
msg = f"Hello {name}"
```

- **变量注解**：使用 `x: int = 1` 代替仅靠注释说明类型

```python
# 不要这样写：
x = 1  # type: int
# 应该这样写：
x: int = 1
```

- **类型提示（函数签名）**：使用 `typing` 模块中的泛型类型

```python
from typing import List, Dict, Optional

def process(items: List[int]) -> Dict[str, int]:
    ...

def find(name: str) -> Optional[str]:
    ...
```

- **异步生成器**：支持 `async def` 中使用 `yield`

```python
async def async_counter(n: int):
    for i in range(n):
        await asyncio.sleep(0.1)
        yield i
```

### Python 3.7+

- **dataclasses**：使用 `@dataclass` 代替手写 `__init__`、`__repr__`、`__eq__`

```python
# 不要这样写：
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    def __repr__(self):
        return f"Point(x={self.x}, y={self.y})"
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

# 应该这样写：
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float
```

- **dict 保序保证**：从 Python 3.7 起，`dict` 官方保证插入顺序。不需要使用 `collections.OrderedDict` 来维护顺序。

```python
# 不要这样写（除非需要 OrderedDict 的特殊比较语义）：
from collections import OrderedDict
d = OrderedDict()
# 应该这样写：
d = {}
```

- **`breakpoint()`**：使用内置的 `breakpoint()` 代替手动导入 pdb

```python
# 不要这样写：
import pdb; pdb.set_trace()
# 应该这样写：
breakpoint()
```

### Python 3.8+

- **walrus 运算符 `:=`**：在表达式中赋值，减少重复计算

```python
# 不要这样写：
line = fp.readline()
while line:
    process(line)
    line = fp.readline()

# 应该这样写：
while (line := fp.readline()):
    process(line)
```

```python
# 不要这样写：
match = pattern.search(text)
if match:
    handle(match)
# 应该这样写：
if (match := pattern.search(text)):
    handle(match)
```

- **`typing.Protocol`**：定义结构化子类型（鸭子类型的类型化版本）

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...

def render(obj: Drawable) -> None:
    obj.draw()
```

- **`typing.TypedDict`**：为字典定义精确的键值类型

```python
from typing import TypedDict

class Movie(TypedDict):
    name: str
    year: int
```

- **仅位置参数 `/`**：使用 `/` 标记仅位置参数，防止调用者使用关键字

```python
def div(a: float, b: float, /) -> float:
    return a / b

# div(1, 2)    ✓
# div(a=1, b=2)  ✗ TypeError
```

- **`typing.final` / `@final`**：标记不可被子类覆写的方法或不可被继承的类

```python
from typing import final

class Base:
    @final
    def process(self) -> None:
        ...
```

- **`typing.Literal`**：将参数限定为特定的字面值

```python
from typing import Literal

def open_file(mode: Literal["r", "w", "a"]) -> None:
    ...
```

- **f-string `=` 调试输出**：`f"{expr=}"` 自动显示表达式和其值，调试时非常实用

```python
# 不要这样写：
print(f"user={user}, count={count}")
# 应该这样写：
print(f"{user=}, {count=}")  # 输出: user='alice', count=42
```

### Python 3.9+

- **内置泛型类型**：使用 `list[int]`、`dict[str, int]`、`tuple[int, ...]` 代替 `typing.List`、`typing.Dict`、`typing.Tuple`

```python
# 不要这样写：
from typing import List, Dict, Tuple, Set

def process(items: List[int]) -> Dict[str, int]:
    ...

# 应该这样写：
def process(items: list[int]) -> dict[str, int]:
    ...
```

- **`str.removeprefix()` / `str.removesuffix()`**：安全地移除前缀/后缀

```python
# 不要这样写：
if s.startswith("prefix_"):
    s = s[len("prefix_"):]
# 应该这样写：
s = s.removeprefix("prefix_")

# 不要这样写：
if s.endswith("_suffix"):
    s = s[:-len("_suffix")]
# 应该这样写：
s = s.removesuffix("_suffix")
```

- **`dict` 合并运算符 `|`**：使用 `d1 | d2` 合并字典

```python
# 不要这样写：
merged = {**d1, **d2}
# 应该这样写：
merged = d1 | d2

# 就地更新：
d1 |= d2  # 代替 d1.update(d2)
```

- **`zoneinfo` 模块**：使用标准库的时区支持代替第三方库 `pytz`

```python
# 不要这样写：
import pytz
tz = pytz.timezone("Asia/Shanghai")
# 应该这样写：
from zoneinfo import ZoneInfo
tz = ZoneInfo("Asia/Shanghai")
```

### Python 3.10+

- **`match/case` 结构化模式匹配**：代替冗长的 if/elif 链

```python
# 不要这样写：
if command == "quit":
    quit_game()
elif command == "go" and direction:
    go(direction)
elif command == "get" and item:
    get(item)
else:
    unknown(command)

# 应该这样写：
match command.split():
    case ["quit"]:
        quit_game()
    case ["go", direction]:
        go(direction)
    case ["get", item]:
        get(item)
    case _:
        unknown(command)
```

- **`X | Y` 联合类型语法**：使用 `X | Y` 代替 `Union[X, Y]`，使用 `X | None` 代替 `Optional[X]`

```python
# 不要这样写：
from typing import Union, Optional

def process(value: Union[int, str]) -> Optional[str]:
    ...

# 应该这样写：
def process(value: int | str) -> str | None:
    ...
```

- **`typing.ParamSpec`**：捕获可调用对象的参数类型，用于装饰器

```python
from typing import ParamSpec, TypeVar, Callable

P = ParamSpec("P")
R = TypeVar("R")

def log_calls(func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper
```

- **`typing.TypeAlias`**：显式声明类型别名

```python
# 不要这样写（模糊，可能被误认为是普通赋值）：
Vector = list[float]

# 应该这样写：
from typing import TypeAlias
Vector: TypeAlias = list[float]
```

- **`zip(strict=True)`**：要求所有可迭代对象长度相同，不同时抛出 `ValueError`

```python
# 不要这样写（静默截断）：
for name, score in zip(names, scores):
    ...
# 应该这样写（长度不匹配时立即报错）：
for name, score in zip(names, scores, strict=True):
    ...
```

### Python 3.11+

- **`ExceptionGroup` 和 `except*`**：并发任务中同时处理多个异常

```python
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(task_a())
        tg.create_task(task_b())
except* ValueError as eg:
    for exc in eg.exceptions:
        handle_value_error(exc)
except* TypeError as eg:
    for exc in eg.exceptions:
        handle_type_error(exc)
```

- **`typing.Self`**：在方法中引用当前类的类型

```python
# 不要这样写：
from typing import TypeVar
T = TypeVar("T", bound="Builder")

class Builder:
    def set_name(self: T, name: str) -> T:
        self.name = name
        return self

# 应该这样写：
from typing import Self

class Builder:
    def set_name(self, name: str) -> Self:
        self.name = name
        return self
```

- **`tomllib`**：标准库内置 TOML 解析，无需第三方库

```python
# 不要这样写：
import toml  # 第三方
config = toml.load("config.toml")

# 应该这样写：
import tomllib
with open("config.toml", "rb") as f:
    config = tomllib.load(f)
```

- **`enum.StrEnum`**：字符串枚举，自动使用成员名作为值

```python
# 不要这样写：
from enum import Enum

class Color(str, Enum):
    RED = "RED"
    GREEN = "GREEN"

# 应该这样写：
from enum import StrEnum

class Color(StrEnum):
    RED = "RED"
    GREEN = "GREEN"
```

- **`asyncio.TaskGroup`**：结构化并发，代替手动管理 `create_task` + `gather`

```python
# 不要这样写：
tasks = [asyncio.create_task(fetch(url)) for url in urls]
results = await asyncio.gather(*tasks)

# 应该这样写：
async with asyncio.TaskGroup() as tg:
    tasks = [tg.create_task(fetch(url)) for url in urls]
results = [t.result() for t in tasks]
```

### Python 3.12+

- **`type` 语句**：简洁的类型别名声明

```python
# 不要这样写：
from typing import TypeAlias
Vector: TypeAlias = list[float]

# 应该这样写：
type Vector = list[float]
```

- **泛型语法 `[T]`**：函数和类直接使用泛型参数，无需 `TypeVar`

```python
# 不要这样写：
from typing import TypeVar
T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]

class Stack(Generic[T]):
    def push(self, item: T) -> None: ...

# 应该这样写：
def first[T](items: list[T]) -> T:
    return items[0]

class Stack[T]:
    def push(self, item: T) -> None: ...
```

- **f-string 嵌套引号**：f-string 内部可使用与外部相同的引号

```python
# 不要这样写（Python 3.11 及之前）：
msg = f"Hello {d['name']}"   # 必须用不同引号
# 应该这样写（Python 3.12+）：
msg = f"Hello {d["name"]}"   # 可以用相同引号
```

- **`@typing.override`**：显式标记方法覆写父类方法，拼写错误时类型检查器会报错

```python
from typing import override

class Child(Parent):
    @override
    def process(self) -> None:
        ...
```

### Python 3.13+

- **`warnings.deprecated`**：标准的弃用装饰器，统一弃用警告

```python
from warnings import deprecated

@deprecated("Use new_function() instead")
def old_function():
    ...
```

- **改进的错误信息**：Python 3.13 对 `NameError`、`ImportError` 等提供更精确的错误建议。这不影响编码方式，但有助于调试。

- **新的 REPL**：支持多行编辑、彩色输出。这不影响编码方式。
