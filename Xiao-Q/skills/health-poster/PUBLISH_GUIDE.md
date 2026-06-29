# 技能发布指南 - skillhub.cn

## 📋 发布前检查清单

### 1. 技能完整性检查
- [x] `SKILL.md` - 技能详细说明文档
- [x] `README.md` - GitHub/技能市场展示文档
- [x] `manifest.json` - 技能清单文件
- [x] `package.json` - npm风格元数据文件
- [x] 主脚本文件：`scripts/generate_health_poster_pro.py`
- [x] 测试脚本：`test_skill_pro.py`
- [x] 示例脚本：`example_usage.py`
- [x] 知识库文件：`references/` 目录下的所有JSON文件
- [x] 发布指南：`PUBLISH_GUIDE.md`（本文件）

### 2. 功能测试
- [x] 配置功能测试通过
- [x] 知识库加载测试通过
- [x] 依赖检查测试通过
- [x] 主题列表测试通过
- [x] 错误处理逻辑完整

### 3. 代码质量
- [x] 无硬编码的API key或敏感信息
- [x] 代码注释完整
- [x] 错误处理完善
- [x] 配置管理清晰
- [x] 依赖关系明确

## 🚀 发布到 skillhub.cn

### 方法一：通过GitHub仓库发布（推荐）

#### 步骤1：创建GitHub仓库
```bash
# 初始化Git仓库
cd /tmp/health-poster-generator-pro
git init
git add .
git commit -m "初始提交: 健康科普海报生成器专业版 v1.0.0"

# 创建GitHub仓库（需要在GitHub网站操作）
# 1. 登录 GitHub
# 2. 点击右上角 "+" → "New repository"
# 3. 仓库名: health-poster-generator-pro
# 4. 描述: 专业版健康科普海报生成器
# 5. 选择公开(Public)
# 6. 不初始化README（我们已经有了）
# 7. 点击 "Create repository"

# 添加远程仓库并推送
git remote add origin https://github.com/<你的用户名>/health-poster-generator-pro.git
git branch -M main
git push -u origin main
```

#### 步骤2：在skillhub.cn提交
1. 访问 https://skillhub.cn
2. 登录账户
3. 进入「发布技能」页面
4. 填写技能信息：
   - **技能名称**: health-poster-generator-pro
   - **显示名称**: 健康科普海报生成器（专业版）
   - **版本**: 1.0.0
   - **描述**: 专业版的健康科普海报生成技能，可配置组织名称，不包含定时任务和固定通道配置
   - **GitHub仓库URL**: https://github.com/<你的用户名>/health-poster-generator-pro
   - **分类**: 图片生成
   - **标签**: health, education, poster, generator, seedream
   - **依赖**: seedream-image-generation
   - **许可证**: MIT
5. 提交审核

### 方法二：直接上传技能包

#### 步骤1：准备技能包
```bash
# 已经创建好的压缩包
/tmp/health-poster-generator-pro-v1.0.0.tar.gz
```

#### 步骤2：在skillhub.cn上传
1. 访问 https://skillhub.cn
2. 登录账户
3. 进入「发布技能」页面
4. 选择「上传技能包」选项
5. 上传 `health-poster-generator-pro-v1.0.0.tar.gz`
6. 系统会自动提取元数据
7. 补充必要信息后提交审核

### 方法三：通过API发布（高级）

如果需要通过API发布，可以使用以下示例：

```bash
# 获取API token（需要在skillhub.cn个人设置中生成）
API_TOKEN="your_api_token_here"

# 发布技能
curl -X POST https://skillhub.cn/api/v1/skills \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "name=health-poster-generator-pro" \
  -F "version=1.0.0" \
  -F "description=专业版健康科普海报生成器" \
  -F "category=image-generation" \
  -F "file=@/tmp/health-poster-generator-pro-v1.0.0.tar.gz"
```

## 📝 技能信息填写指南

### 基本信息
- **技能ID**: `health-poster-generator-pro`（必须唯一）
- **显示名称**: 健康科普海报生成器（专业版）
- **版本**: `1.0.0`（遵循语义化版本规范）
- **描述**: 简洁明了地描述技能功能

### 详细描述
在技能详情页可以添加更详细的描述，建议包括：
1. **功能特性**：列出核心功能
2. **使用示例**：提供代码示例
3. **配置说明**：如何配置技能
4. **依赖要求**：必需的依赖和配置
5. **常见问题**：故障排除指南

### 分类和标签
- **主分类**: `image-generation`（图片生成）
- **次分类**: `education`（教育）
- **标签**: `health`, `poster`, `generator`, `seedream`, `volcengine`

### 依赖关系
- **必需依赖**: `seedream-image-generation`
- **API要求**: 火山引擎API key
- **系统要求**: OpenClaw >= 2026.3.0

### 许可证
- **许可证类型**: MIT
- **版权声明**: OpenClaw Community

## 🔍 审核注意事项

skillhub.cn审核团队会检查以下内容：

### 1. 安全性
- [x] 无硬编码的API key或密码
- [x] 无恶意代码
- [x] 依赖关系安全

### 2. 功能性
- [x] 技能能正常运行
- [x] 文档完整准确
- [x] 错误处理完善

### 3. 代码质量
- [x] 代码结构清晰
- [x] 注释充分
- [x] 遵循最佳实践

### 4. 用户体验
- [x] 安装流程简单
- [x] 配置清晰
- [x] 错误提示友好

## 📊 发布后维护

### 版本更新
1. 更新版本号（遵循语义化版本）
2. 更新CHANGELOG
3. 推送新版本到GitHub
4. 在skillhub.cn更新技能版本

### 问题反馈
1. 监控GitHub Issues
2. 回复skillhub.cn用户评论
3. 及时修复bug

### 功能改进
1. 收集用户反馈
2. 规划新功能
3. 定期更新维护

## 🆘 常见问题

### Q1: 审核需要多长时间？
A: 通常需要1-3个工作日，具体时间取决于审核队列长度。

### Q2: 审核不通过怎么办？
A: 查看审核反馈，修改问题后重新提交。

### Q3: 如何更新已发布的技能？
A: 在skillhub.cn技能管理页面可以上传新版本。

### Q4: 技能可以收费吗？
A: skillhub.cn支持免费和付费技能，需要在发布时选择。

### Q5: 如何推广我的技能？
A: 可以在OpenClaw社区、社交媒体等渠道分享。

## 📞 支持与帮助

- **skillhub.cn帮助中心**: https://skillhub.cn/help
- **OpenClaw社区论坛**: https://community.openclaw.ai
- **GitHub Issues**: 用于bug报告和功能请求

---

**祝您发布顺利！** 🎉

如果有任何问题，请参考上述指南或联系skillhub.cn支持团队。