---
name: python-script-generator
description: 快速生成专业的 Python 脚本和应用代码。一键创建完整项目结构，支持CLI、API、爬虫、Bot、Django等多种项目类型，包含完整的项目结构、配置文件、依赖管理、测试、README和文档。
version: 1.0.0
tags: [python, cli, api, fastapi, flask, django, scraper, bot]
trigger:
  - 创建.*Python.*项目
  - 生成.*Python.*项目
  - Python.*CLI.*工具
  - FastAPI.*项目
  - Flask.*API
  - Django.*项目
  - Python.*爬虫
  - Telegram.*Bot
  - Discord.*Bot
  - Python.*脚本.*生成
---

# Python Script Generator

## 适用场景

1.快速生成专业的 Python 脚本和应用代码。

2.构建CLI、API、爬虫、Bot、Django相关项目python代码。

3.为项目生成完整配置：requirements、setup、测试、README、文档。

## 主要功能

一键创建完整项目结构，快速生成专业的 Python 脚本和应用代码。支持CLI 工具、Flask API、FastAPI、Django 命令、网络爬虫、机器人等多种项目类型，包含完整的项目结构、配置文件、依赖管理、测试、README和文档。代码遵循Python社区规范。

## 工作流程

### 识别项目类型

首先根据下表，识别项目类型，准备需要使用到的工具和用法。

| 类型          | 说明           | 适用场景                |
| ------------- | -------------- | ----------------------- |
| cli           | 命令行工具     | 自动化脚本、命令行应用  |
| flask         | Flask API      | 轻量级Web服务、REST API |
| fastapi       | FastAPI        | 高性能API、异步服务     |
| fastapi-crud  | FastAPI CRUD   | 数据管理API             |
| django-cmd    | Django Command | Django管理命令          |
| django-app    | Django App     | Django应用模块          |
| scraper       | 网页爬虫       | 数据采集、监控          |
| scraper-async | 异步爬虫       | 高性能数据采集          |
| bot           | Telegram Bot   | Telegram机器人          |
| discord-bot   | Discord Bot    | Discord机器人           |
| data-analysis | 数据分析       | 数据处理、分析脚本      |
| ml-model      | 机器学习       | ML模型训练部署          |
| automation    | 自动化任务     | 定时任务、工作流        |

### 挑选项目功能并执行

根据需求，选出需要用到的功能并加载。

```bash
# 生成CLI工具
python-script-generator mycli --type cli

# 生成FastAPI项目
python-script-generator myapi --type fastapi

# 带描述生成项目
python-script-generator backup-tool --type cli --description "Backup important files"

# 指定项目名称和输出目录
python-script-generator myproject --type flask --output ./projects/myproject

# 生成带CRUD的FastAPI
python-script-generator myapi --type fastapi --crud

# 生成异步爬虫
python-script-generator async-scraper --type scraper-async

# 生成Discord Bot
python-script-generator discord-bot --type discord-bot

# 生成数据分析项目
python-script-analysis --type data-analysis --requirements pandas,numpy,matplotlib

#生成机器学习项目
python-script-generator ml-model --type ml-model --framework tensorflow
```

### 项目文件生成参数说明

- `--name` / `-n`: 项目名称（必需）
- `--type` / `-t`: 项目类型（必需）
- `--description` / `-d`: 项目描述
- `--output` / `-o`: 输出目录（默认当前目录）
- `--requirements` / `-r`: 依赖包列表，逗号分隔
- `--author`: 作者信息
- `--license`: 许可证类型
- `--version`: 项目版本
- `--template`: 自定义模板路径
- `--force`: 强制覆盖已存在目录

## 生成的项目结构

### CLI 工具项目结构

```
mycli/
├── mycli/
│   ├── __init__.py
│   ├── __main__.py
│   └── cli.py
├── tests/
│   ├── __init__.py
│   └── test_cli.py
├── docs/
│   └── README.md
├── mycli.egg-info/
├── requirements.txt
├── setup.py
├── pyproject.toml
├── .gitignore
└── README.md
```

### FastAPI 项目结构

```
myapi/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── scripts/
│   ├── migrate.py
│   └── seed.py
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

## 高级功能

### 环境变量管理

```bash
# .env.example
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### Docker 支持

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```



### GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: Run tests
      run: |
        pytest tests/ --cov=app --cov-report=xml
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

### 预提交钩子

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 22.12.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-aiohttp]
```

## 可参考文档

- [Python 官方文档](https://docs.python.org/3/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Flask 官方文档](https://flask.palletsprojects.com/)
- [aiohttp 文档](https://docs.aiohttp.org/)
- [pytest 文档](https://docs.pytest.org/)
