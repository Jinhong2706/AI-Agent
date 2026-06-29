#!/usr/bin/env bash
set -euo pipefail

USER_INPUT="${1:-}"

python3 - "$USER_INPUT" <<'PY'
import json
import re
import sys

prompt = sys.argv[1]
stripped = prompt.strip()

policy = "标准"
if re.match(r"^bf-a(\s|$)", stripped) or re.match(r"^bf a(\s|$)", stripped) or "全自动" in prompt:
    policy = "全自动"
elif re.match(r"^bf-fast(\s|$)", stripped) or "快速" in prompt:
    policy = "快速"

mode = "API/功能开发"
confidence = "medium"

architecture_terms = ("架构负责人", "系统架构", "模块边界", "ADR", "架构简报", "数据所有权", "权限模型")
new_project_terms = ("从 0 到 1", "新建后端", "新项目", "创建服务", "服务骨架")
migration_terms = ("迁移", "表结构", "字段", "索引", "alembic", "flyway", "liquibase", "migration")
auth_terms = ("登录", "注册", "JWT", "session", "权限", "鉴权", "越权", "认证")
bug_terms = ("报错", "异常", "500", "修复", "排查", "定位", "bug")
test_terms = ("补测试", "测试覆盖", "单元测试", "集成测试")
perf_terms = ("慢查询", "性能", "并发", "锁", "响应慢")
queue_terms = ("Redis", "缓存", "队列", "异步", "Celery", "Kafka", "RabbitMQ")
deploy_terms = ("启动失败", "部署", "配置", "环境变量", "Docker", "容器")
review_terms = ("review", "代码审查", "重构")
pass_terms = ("解释", "说明", "怎么选", "区别")

if any(term in prompt for term in architecture_terms):
    mode = "后端架构负责人"
    confidence = "high"
elif any(term in prompt for term in new_project_terms):
    mode = "新项目共创"
    confidence = "high"
elif any(term in prompt for term in migration_terms):
    mode = "数据模型与迁移"
    confidence = "high"
elif any(term in prompt for term in auth_terms):
    mode = "认证鉴权"
    confidence = "high"
elif any(term in prompt for term in bug_terms):
    mode = "Bug/生产问题排查"
    confidence = "high"
elif any(term in prompt for term in test_terms):
    mode = "测试补强"
    confidence = "high"
elif any(term in prompt for term in perf_terms):
    mode = "性能/并发局部优化"
    confidence = "high"
elif any(term in prompt for term in queue_terms):
    mode = "缓存/异步/队列"
    confidence = "high"
elif any(term in prompt for term in deploy_terms):
    mode = "配置/部署排查"
    confidence = "high"
elif any(term in prompt for term in review_terms):
    mode = "代码审查/重构"
    confidence = "high"
elif any(term in prompt for term in pass_terms):
    mode = "直通咨询"
    confidence = "medium"

print(json.dumps({
    "mode": mode,
    "policy": policy,
    "confidence": confidence,
    "guardrails_check": "required" if mode not in {"直通咨询"} else "skip",
}, ensure_ascii=False))
PY
