# Django Maintenance

Django 是 Backend Forge 第一版的维护支持方向，不作为新项目主线。

## 识别

常见文件：

- `manage.py`。
- project settings。
- app 目录。
- `models.py`、`views.py`、`serializers.py`、`urls.py`。
- migrations。
- `pytest.ini` 或 Django test 配置。

## 维护边界

可以做：

- 修 Bug。
- 增加字段和 migration。
- 修改 API。
- 补测试。
- 调整 DRF serializer/viewset/permission。
- 排查配置和数据库问题。

不默认做：

- 从 0 创建 Django 大型项目。
- 重构成复杂 monolith 平台。
- 平台级权限和多租户设计。

## 数据迁移

必须：

- 修改 model 后生成/检查 migration。
- 关注默认值和 nullability。
- 关注历史数据兼容。
- 跑 migration 或说明无法运行原因。

## DRF

关注：

- serializer 输入输出字段。
- viewset/queryset 权限过滤。
- permission classes。
- pagination。
- filter/search/order。
- status code。

## 测试

常见组合：

- Django TestCase。
- pytest-django。
- DRF APIClient。

最低覆盖：

- model/serializer 验证。
- API 正常路径。
- 权限路径。
- migration 或关键查询。

## 常见风险

- serializer 暴露内部字段。
- queryset 未按用户过滤导致越权。
- migration 默认值处理不当。
- view 中业务逻辑过重。
- settings 差异导致本地和生产行为不同。
