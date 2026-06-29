﻿﻿---
name: openclaw-ui-channel-operator
description: 识别用户UI界面创建/修改意图并按频道在测试目录执行；仅在收到固定发布口令并二次确认后，备份并全量发布到生产。
---

# OpenClaw 频道 UI 助手（测试优先发布版）

## 触发条件
当用户表达以下意图时调用：
- 创建界面 / 新建页面 / 配置 UI
- 在某频道下新增、修改、发布 UI 配置

## 交互规则
1. 当识别到 UI 创建/修改意图时，直接列出全部可选频道及完整菜单结构（含子级）供用户选择，**禁止附带任何目录路径、服务器地址、文件路径等信息**，仅展示频道名称与子菜单层级：
   - 微私域会话管理
   - autotape会话存档
   - 云顶scrm
   - 项目开发
   - 腾讯云（三级菜单）：
     · 云计算网络 → 云服务器 / 数据库 / 云负载均衡 / 存储服务 / 云上网络
     · 云AI智能 → 腾讯乐享知识库 / WorkBuddy / 智能体开发平台 / 腾讯企点智能客服
     · 办公协同SaaS → 腾讯会议 / 腾讯电子签 / iOA 零信任安全管理 / TAPD敏捷项目管理 / 腾讯问卷
   - 火山云（二级菜单）：
     · 云计算
     · 大模型
     · AI智能
2. 用户选定频道后，**必须立即进入该频道测试目录（dev）执行修改**，不得询问或猜测 prod 路径。
3. 只要用户意图是“创建/修改/删除 UI”，都视为“测试修改阶段”，**目标目录只能是 dev**。
4. 用户已给出“频道 + 修改需求”时，直接执行，不再追问“是不是在 dev 创建”。
5. 若用户未提供具体修改需求，再追问：
   - “请输入您想要修改的内容（将默认在该频道 dev 目录执行）。”
6. 在未触发发布前，回复中**禁止出现**“当前在 product 目录”或将 product 作为默认操作目录。
7. 当用户明确说出固定发布触发语（例如“我想发布到生产”）时，不立即发布，先二次确认：
   - “请确认：是否将 <频道> 的测试内容发布到生产？”
8. 仅当用户再次明确确认（如“确认发布”）后，才执行发布流程：
   - 先备份生产目录
   - 再将测试目录全量镜像到生产目录
9. 若未收到固定发布触发语或未完成二次确认，严禁改动生产目录。

## Header Logo 规范（强制）
- 本规范仅适用于页面 `header` 区域的“公司 logo”，不适用于页面内其他业务图标、功能图标、菜单图标。
- `header` 公司 logo 图片路径固定为：`/data/images/gm-logo.png`。
- `header` logo 点击行为固定为：`top.location.href='https://preview.wesiyu.com/'`。
- 整块 `header logo` 区域必须可点击（不仅是图片本身可点击）。
- 禁止将页面内所有图标统一替换为 `gm-logo.png`；仅允许替换 `header` 公司 logo。
- 若页面无 `header` 区域，需先按页面结构新增 `header logo` 区域后再应用以上规则。
- 每次 UI 修改完成后，必须自动执行 `header logo` 合规检查；不得等待用户二次指出问题。

## 交付前自动检查（强制）
- 在返回“操作完成”前，必须先执行以下检查，全部通过才可交付：
  - 检查 `header` 是否存在公司 logo 图片，且图片路径为 `/data/images/gm-logo.png`。
  - 检查 `header logo` 整块区域是否可点击（容器或等效可点击区域）。
  - 检查点击行为是否精确指向：`top.location.href='https://preview.wesiyu.com/'`。
  - 检查是否误改页面其他图标为 `gm-logo.png`（若误改必须回退）。
- 任一检查失败时：
  - 不得输出“操作完成”。
  - 必须先修复后再重新检查，直到全部 PASS。
  - 若仍失败，返回“失败项 + 原因 + 下一步处理”。

## 频道 -> 目录映射（固定）
- 微私域会话管理
  - 测试目录：`/data/dev/manage`
  - 生产目录：`/data/product/manage`
  - 备份根目录：`/data/backup/manage`
  - 测试访问路径（8080）：`/manage-dev/`
- autotape会话存档
  - 测试目录：`/data/dev/autotape`
  - 生产目录：`/data/product/autotape`
  - 备份根目录：`/data/backup/autotape`
  - 测试访问路径（8080）：`/autotape-dev/`
- 云顶scrm
  - 测试目录：`/data/dev/ydscrm`
  - 生产目录：`/data/product/ydscrm`
  - 备份根目录：`/data/backup/ydscrm`
  - 测试访问路径（8080）：`/ydscrm-dev/`
- 项目开发
  - 测试目录：`/data/dev/project`
  - 生产目录：`/data/product/project`
  - 备份根目录：`/data/backup/project`
  - 测试访问路径（8080）：`/project-dev/`
  - 菜单结构：暂无子菜单（独立一级频道）
- 腾讯云
  - 频道首页
    - 测试目录：`/data/dev/tencent`
    - 生产目录：`/data/product/tencent`
    - 备份根目录：`/data/backup/tencent`
    - 测试访问路径（8080）：`/tencent-dev/`
  - 二级子频道：
    - 云计算网络
      - 测试目录：`/data/dev/tencent-network`
      - 生产目录：`/data/product/tencent-network`
      - 备份根目录：`/data/backup/tencent-network`
      - 测试访问路径（8080）：`/tencent-network-dev/`
      - 三级子频道：
        - 云服务器
          - 测试目录：`/data/dev/tencent-cvm`
          - 生产目录：`/data/product/tencent-cvm`
          - 备份根目录：`/data/backup/tencent-cvm`
          - 测试访问路径（8080）：`/tencent-cvm-dev/`
        - 数据库
          - 测试目录：`/data/dev/tencent-db`
          - 生产目录：`/data/product/tencent-db`
          - 备份根目录：`/data/backup/tencent-db`
          - 测试访问路径（8080）：`/tencent-db-dev/`
        - 云负载均衡
          - 测试目录：`/data/dev/tencent-clb`
          - 生产目录：`/data/product/tencent-clb`
          - 备份根目录：`/data/backup/tencent-clb`
          - 测试访问路径（8080）：`/tencent-clb-dev/`
        - 存储服务
          - 测试目录：`/data/dev/tencent-storage`
          - 生产目录：`/data/product/tencent-storage`
          - 备份根目录：`/data/backup/tencent-storage`
          - 测试访问路径（8080）：`/tencent-storage-dev/`
        - 云上网络
          - 测试目录：`/data/dev/tencent-vpc`
          - 生产目录：`/data/product/tencent-vpc`
          - 备份根目录：`/data/backup/tencent-vpc`
          - 测试访问路径（8080）：`/tencent-vpc-dev/`
    - 云AI智能
      - 测试目录：`/data/dev/tencent-ai`
      - 生产目录：`/data/product/tencent-ai`
      - 备份根目录：`/data/backup/tencent-ai`
      - 测试访问路径（8080）：`/tencent-ai-dev/`
      - 三级子频道：
        - 腾讯乐享知识库
          - 测试目录：`/data/dev/tencent-lexiang`
          - 生产目录：`/data/product/tencent-lexiang`
          - 备份根目录：`/data/backup/tencent-lexiang`
          - 测试访问路径（8080）：`/tencent-lexiang-dev/`
        - WorkBuddy
          - 测试目录：`/data/dev/tencent-workbuddy`
          - 生产目录：`/data/product/tencent-workbuddy`
          - 备份根目录：`/data/backup/tencent-workbuddy`
          - 测试访问路径（8080）：`/tencent-workbuddy-dev/`
        - 智能体开发平台
          - 测试目录：`/data/dev/tencent-agent`
          - 生产目录：`/data/product/tencent-agent`
          - 备份根目录：`/data/backup/tencent-agent`
          - 测试访问路径（8080）：`/tencent-agent-dev/`
        - 腾讯企点智能客服
          - 测试目录：`/data/dev/tencent-qidian`
          - 生产目录：`/data/product/tencent-qidian`
          - 备份根目录：`/data/backup/tencent-qidian`
          - 测试访问路径（8080）：`/tencent-qidian-dev/`
    - 办公协同SaaS
      - 测试目录：`/data/dev/tencent-saas`
      - 生产目录：`/data/product/tencent-saas`
      - 备份根目录：`/data/backup/tencent-saas`
      - 测试访问路径（8080）：`/tencent-saas-dev/`
      - 三级子频道：
        - 腾讯会议
          - 测试目录：`/data/dev/tencent-meeting`
          - 生产目录：`/data/product/tencent-meeting`
          - 备份根目录：`/data/backup/tencent-meeting`
          - 测试访问路径（8080）：`/tencent-meeting-dev/`
        - 腾讯电子签
          - 测试目录：`/data/dev/tencent-esign`
          - 生产目录：`/data/product/tencent-esign`
          - 备份根目录：`/data/backup/tencent-esign`
          - 测试访问路径（8080）：`/tencent-esign-dev/`
        - iOA 零信任安全管理
          - 测试目录：`/data/dev/tencent-ioa`
          - 生产目录：`/data/product/tencent-ioa`
          - 备份根目录：`/data/backup/tencent-ioa`
          - 测试访问路径（8080）：`/tencent-ioa-dev/`
        - TAPD敏捷项目管理
          - 测试目录：`/data/dev/tencent-tapd`
          - 生产目录：`/data/product/tencent-tapd`
          - 备份根目录：`/data/backup/tencent-tapd`
          - 测试访问路径（8080）：`/tencent-tapd-dev/`
        - 腾讯问卷
          - 测试目录：`/data/dev/tencent-survey`
          - 生产目录：`/data/product/tencent-survey`
          - 备份根目录：`/data/backup/tencent-survey`
          - 测试访问路径（8080）：`/tencent-survey-dev/`
- 火山云
  - 频道首页
    - 测试目录：`/data/dev/volc`
    - 生产目录：`/data/product/volc`
    - 备份根目录：`/data/backup/volc`
    - 测试访问路径（8080）：`/volc-dev/`
  - 二级子频道：
    - 云计算
      - 测试目录：`/data/dev/volc-cloud`
      - 生产目录：`/data/product/volc-cloud`
      - 备份根目录：`/data/backup/volc-cloud`
      - 测试访问路径（8080）：`/volc-cloud-dev/`
    - 大模型
      - 测试目录：`/data/dev/volc-llm`
      - 生产目录：`/data/product/volc-llm`
      - 备份根目录：`/data/backup/volc-llm`
      - 测试访问路径（8080）：`/volc-llm-dev/`
    - AI智能
      - 测试目录：`/data/dev/volc-ai`
      - 生产目录：`/data/product/volc-ai`
      - 备份根目录：`/data/backup/volc-ai`
      - 测试访问路径（8080）：`/volc-ai-dev/`

## 多级菜单链接配置规范（强制：腾讯云、火山云）
- 腾讯云 和 火山云 频道必须构建多级菜单导航，**每一级菜单均需配置独立可点击链接**，各自对应一个子频道页面。
- 菜单链接不得为空、不得为占位符（如 `#`、`javascript:void(0)`），必须指向实际可访问的子频道页面 URL。
- 腾讯云（三级菜单）：
  - 一级菜单（腾讯云）：链接指向频道首页。
  - 二级菜单（云计算网络 / 云AI智能 / 办公协同SaaS）：链接指向对应分类汇总页面。
  - 三级菜单（各具体服务项）：链接指向对应服务详情页面。
- 火山云（二级菜单）：
  - 一级菜单（火山云）：链接指向频道首页。
  - 二级菜单（云计算 / 大模型 / AI智能）：链接指向对应分类汇总页面。
- 创建或修改腾讯云/火山云 UI 时，必须同步确认菜单层级完整性，不得缺少或跳级。
- 菜单结构应保持与频道映射表中「频道 -> 目录映射」描述一致；若用户自定义菜单项名称或链接，必须先更新频道映射记录后再执行 UI 修改。

## 8080 测试访问规则（固定）
- 测试预览统一走 `8080` 端口，访问路径按频道固定，不动态生成。
- 若需要配置 Nginx，仅允许在 `listen 8080;` 对应的 `server` 块内追加频道 `location`，不得改动其他端口配置。
- Nginx 配置文件名固定为：`/etc/nginx/conf.d/aipage.conf`。
- 严禁重命名、替换、删除该文件（包括但不限于 `mv` 改名、另存为新文件后替换、删除重建）。
- 仅允许在现有 `aipage.conf` 文件内追加或更新对应频道 `location` 块，且不得修改其他 `location` 的语义。
- 执行顺序必须是“先检查，后变更”：
  - 先检查 `aipage.conf` 是否已存在目标频道 `location`。
  - 若已存在，则先做可访问性校验（HTTP `200` / `301` / `302`）。
  - 若已存在且可访问，则禁止重复追加，直接复用并返回测试链接。
  - 仅当“location 不存在”或“存在但不可访问”时，才允许追加/修正该频道 `location`。
- 完成变更后必须执行 Nginx 配置检查（如 `nginx -t`）；检查失败则回滚本次 `aipage.conf` 变更并返回错误。
- 禁止输出或使用错误路径（如 `/ydscrn-dev/`）；云顶scrm固定为 `/ydscrm-dev/`。
- 禁止在结果中返回占位符链接（如 `http://<host>:8080/...`）；必须返回可直接点击的完整 URL。
- 测试链接主机必须是“用户可访问地址”（域名或 IP）；不要默认使用 `localhost` 或 `127.0.0.1` 给用户。
- 默认采用“外网优先”策略：首次返回必须给外网可访问链接，不能先给内网链接再让用户追问。
- 禁止将内网地址作为主测试链接：`10.*`、`172.16.*`-`172.31.*`、`192.168.*`、`169.254.*`、`localhost`、`127.0.0.1`。
- 微私域会话管理 `location` 固定为：
  ```nginx
  # 微私域会话管理频道首页
  location /manage-dev/ {
      alias /data/dev/manage/;
      index index.html;
      try_files $uri $uri/ /manage-dev/index.html;
  }
  ```
- autotape会话存档 `location` 固定为：
  ```nginx
  # autotape会话存档频道首页
  location /autotape-dev/ {
      alias /data/dev/autotape/;
      index index.html;
      try_files $uri $uri/ /autotape-dev/index.html;
  }
  ```
- 云顶scrm `location` 固定为：
  ```nginx
  # 云顶scrm频道首页
  location /ydscrm-dev/ {
      alias /data/dev/ydscrm/;
      index index.html;
      try_files $uri $uri/ /ydscrm-dev/index.html;
  }
  ```
- 项目开发 `location` 固定为：
  ```nginx
  # 项目开发频道首页
  location /project-dev/ {
      alias /data/dev/project/;
      index index.html;
      try_files $uri $uri/ /project-dev/index.html;
  }
  ```
- 腾讯云 `location` 固定为：
  ```nginx
  # 腾讯云频道首页
  location /tencent-dev/ {
      alias /data/dev/tencent/;
      index index.html;
      try_files $uri $uri/ /tencent-dev/index.html;
  }
  ```
- 腾讯云-子频道 `location` 固定为：
  ```nginx
  # 腾讯云 - 二级：云计算网络
  location /tencent-network-dev/ {
      alias /data/dev/tencent-network/;
      index index.html;
      try_files $uri $uri/ /tencent-network-dev/index.html;
  }
  # 腾讯云 - 二级：云AI智能
  location /tencent-ai-dev/ {
      alias /data/dev/tencent-ai/;
      index index.html;
      try_files $uri $uri/ /tencent-ai-dev/index.html;
  }
  # 腾讯云 - 二级：办公协同SaaS
  location /tencent-saas-dev/ {
      alias /data/dev/tencent-saas/;
      index index.html;
      try_files $uri $uri/ /tencent-saas-dev/index.html;
  }
  # 腾讯云 - 三级：云服务器
  location /tencent-cvm-dev/ {
      alias /data/dev/tencent-cvm/;
      index index.html;
      try_files $uri $uri/ /tencent-cvm-dev/index.html;
  }
  # 腾讯云 - 三级：数据库
  location /tencent-db-dev/ {
      alias /data/dev/tencent-db/;
      index index.html;
      try_files $uri $uri/ /tencent-db-dev/index.html;
  }
  # 腾讯云 - 三级：云负载均衡
  location /tencent-clb-dev/ {
      alias /data/dev/tencent-clb/;
      index index.html;
      try_files $uri $uri/ /tencent-clb-dev/index.html;
  }
  # 腾讯云 - 三级：存储服务
  location /tencent-storage-dev/ {
      alias /data/dev/tencent-storage/;
      index index.html;
      try_files $uri $uri/ /tencent-storage-dev/index.html;
  }
  # 腾讯云 - 三级：云上网络
  location /tencent-vpc-dev/ {
      alias /data/dev/tencent-vpc/;
      index index.html;
      try_files $uri $uri/ /tencent-vpc-dev/index.html;
  }
  # 腾讯云 - 三级：腾讯乐享知识库
  location /tencent-lexiang-dev/ {
      alias /data/dev/tencent-lexiang/;
      index index.html;
      try_files $uri $uri/ /tencent-lexiang-dev/index.html;
  }
  # 腾讯云 - 三级：WorkBuddy
  location /tencent-workbuddy-dev/ {
      alias /data/dev/tencent-workbuddy/;
      index index.html;
      try_files $uri $uri/ /tencent-workbuddy-dev/index.html;
  }
  # 腾讯云 - 三级：智能体开发平台
  location /tencent-agent-dev/ {
      alias /data/dev/tencent-agent/;
      index index.html;
      try_files $uri $uri/ /tencent-agent-dev/index.html;
  }
  # 腾讯云 - 三级：腾讯企点智能客服
  location /tencent-qidian-dev/ {
      alias /data/dev/tencent-qidian/;
      index index.html;
      try_files $uri $uri/ /tencent-qidian-dev/index.html;
  }
  # 腾讯云 - 三级：腾讯会议
  location /tencent-meeting-dev/ {
      alias /data/dev/tencent-meeting/;
      index index.html;
      try_files $uri $uri/ /tencent-meeting-dev/index.html;
  }
  # 腾讯云 - 三级：腾讯电子签
  location /tencent-esign-dev/ {
      alias /data/dev/tencent-esign/;
      index index.html;
      try_files $uri $uri/ /tencent-esign-dev/index.html;
  }
  # 腾讯云 - 三级：iOA 零信任安全管理
  location /tencent-ioa-dev/ {
      alias /data/dev/tencent-ioa/;
      index index.html;
      try_files $uri $uri/ /tencent-ioa-dev/index.html;
  }
  # 腾讯云 - 三级：TAPD敏捷项目管理
  location /tencent-tapd-dev/ {
      alias /data/dev/tencent-tapd/;
      index index.html;
      try_files $uri $uri/ /tencent-tapd-dev/index.html;
  }
  # 腾讯云 - 三级：腾讯问卷
  location /tencent-survey-dev/ {
      alias /data/dev/tencent-survey/;
      index index.html;
      try_files $uri $uri/ /tencent-survey-dev/index.html;
  }
  ```
- 火山云 `location` 固定为：
  ```nginx
  # 火山云频道首页
  location /volc-dev/ {
      alias /data/dev/volc/;
      index index.html;
      try_files $uri $uri/ /volc-dev/index.html;
  }
  ```
- 火山云-子频道 `location` 固定为：
  ```nginx
  # 火山云 - 二级：云计算
  location /volc-cloud-dev/ {
      alias /data/dev/volc-cloud/;
      index index.html;
      try_files $uri $uri/ /volc-cloud-dev/index.html;
  }
  # 火山云 - 二级：大模型
  location /volc-llm-dev/ {
      alias /data/dev/volc-llm/;
      index index.html;
      try_files $uri $uri/ /volc-llm-dev/index.html;
  }
  # 火山云 - 二级：AI智能
  location /volc-ai-dev/ {
      alias /data/dev/volc-ai/;
      index index.html;
      try_files $uri $uri/ /volc-ai-dev/index.html;
  }
  ```

## 生产 Nginx 配置（固定，同一台 8080 服务器）
- 规则：去掉 `-dev` 后缀，`alias` 指向 `/data/product/<name>/`。
- 生产域名通过另一台服务器 `proxy_pass` 转发到 8080 对应路径。

- 微私域会话管理 `location`（生产）：
  ```nginx
  # 微私域会话管理频道首页
  location /manage/ {
      alias /data/product/manage/;
      index index.html;
      try_files $uri $uri/ /manage/index.html;
  }
  ```
- autotape会话存档 `location`（生产）：
  ```nginx
  # autotape会话存档频道首页
  location /autotape/ {
      alias /data/product/autotape/;
      index index.html;
      try_files $uri $uri/ /autotape/index.html;
  }
  ```
- 云顶scrm `location`（生产）：
  ```nginx
  # 云顶scrm频道首页
  location /ydscrm/ {
      alias /data/product/ydscrm/;
      index index.html;
      try_files $uri $uri/ /ydscrm/index.html;
  }
  ```
- 项目开发 `location`（生产）：
  ```nginx
  # 项目开发频道首页
  location /project/ {
      alias /data/product/project/;
      index index.html;
      try_files $uri $uri/ /project/index.html;
  }
  ```
- 腾讯云 `location`（生产）：
  ```nginx
  # 腾讯云频道首页
  location /tencent/ {
      alias /data/product/tencent/;
      index index.html;
      try_files $uri $uri/ /tencent/index.html;
  }
  ```
- 腾讯云-子频道 `location`（生产）：
  ```nginx
  # 腾讯云 - 二级：云计算网络
  location /tencent-network/ {
      alias /data/product/tencent-network/;
      index index.html;
      try_files $uri $uri/ /tencent-network/index.html;
  }
  # 腾讯云 - 二级：云AI智能
  location /tencent-ai/ {
      alias /data/product/tencent-ai/;
      index index.html;
      try_files $uri $uri/ /tencent-ai/index.html;
  }
  # 腾讯云 - 二级：办公协同SaaS
  location /tencent-saas/ {
      alias /data/product/tencent-saas/;
      index index.html;
      try_files $uri $uri/ /tencent-saas/index.html;
  }
  # 腾讯云 - 三级：云服务器
  location /tencent-cvm/ {
      alias /data/product/tencent-cvm/;
      index index.html;
      try_files $uri $uri/ /tencent-cvm/index.html;
  }
  # 腾讯云 - 三级：数据库
  location /tencent-db/ {
      alias /data/product/tencent-db/;
      index index.html;
      try_files $uri $uri/ /tencent-db/index.html;
  }
  # 腾讯云 - 三级：云负载均衡
  location /tencent-clb/ {
      alias /data/product/tencent-clb/;
      index index.html;
      try_files $uri $uri/ /tencent-clb/index.html;
  }
  # 腾讯云 - 三级：存储服务
  location /tencent-storage/ {
      alias /data/product/tencent-storage/;
      index index.html;
      try_files $uri $uri/ /tencent-storage/index.html;
  }
  # 腾讯云 - 三级：云上网络
  location /tencent-vpc/ {
      alias /data/product/tencent-vpc/;
      index index.html;
      try_files $uri $uri/ /tencent-vpc/index.html;
  }
  # 腾讯云 - 三级：腾讯乐享知识库
  location /tencent-lexiang/ {
      alias /data/product/tencent-lexiang/;
      index index.html;
      try_files $uri $uri/ /tencent-lexiang/index.html;
  }
  # 腾讯云 - 三级：WorkBuddy
  location /tencent-workbuddy/ {
      alias /data/product/tencent-workbuddy/;
      index index.html;
      try_files $uri $uri/ /tencent-workbuddy/index.html;
  }
  # 腾讯云 - 三级：智能体开发平台
  location /tencent-agent/ {
      alias /data/product/tencent-agent/;
      index index.html;
      try_files $uri $uri/ /tencent-agent/index.html;
  }
  # 腾讯云 - 三级：腾讯企点智能客服
  location /tencent-qidian/ {
      alias /data/product/tencent-qidian/;
      index index.html;
      try_files $uri $uri/ /tencent-qidian/index.html;
  }
  # 腾讯云 - 三级：腾讯会议
  location /tencent-meeting/ {
      alias /data/product/tencent-meeting/;
      index index.html;
      try_files $uri $uri/ /tencent-meeting/index.html;
  }
  # 腾讯云 - 三级：腾讯电子签
  location /tencent-esign/ {
      alias /data/product/tencent-esign/;
      index index.html;
      try_files $uri $uri/ /tencent-esign/index.html;
  }
  # 腾讯云 - 三级：iOA 零信任安全管理
  location /tencent-ioa/ {
      alias /data/product/tencent-ioa/;
      index index.html;
      try_files $uri $uri/ /tencent-ioa/index.html;
  }
  # 腾讯云 - 三级：TAPD敏捷项目管理
  location /tencent-tapd/ {
      alias /data/product/tencent-tapd/;
      index index.html;
      try_files $uri $uri/ /tencent-tapd/index.html;
  }
  # 腾讯云 - 三级：腾讯问卷
  location /tencent-survey/ {
      alias /data/product/tencent-survey/;
      index index.html;
      try_files $uri $uri/ /tencent-survey/index.html;
  }
  ```
- 火山云 `location`（生产）：
  ```nginx
  # 火山云频道首页
  location /volc/ {
      alias /data/product/volc/;
      index index.html;
      try_files $uri $uri/ /volc/index.html;
  }
  ```
- 火山云-子频道 `location`（生产）：
  ```nginx
  # 火山云 - 二级：云计算
  location /volc-cloud/ {
      alias /data/product/volc-cloud/;
      index index.html;
      try_files $uri $uri/ /volc-cloud/index.html;
  }
  # 火山云 - 二级：大模型
  location /volc-llm/ {
      alias /data/product/volc-llm/;
      index index.html;
      try_files $uri $uri/ /volc-llm/index.html;
  }
  # 火山云 - 二级：AI智能
  location /volc-ai/ {
      alias /data/product/volc-ai/;
      index index.html;
      try_files $uri $uri/ /volc-ai/index.html;
  }
  ```

## 外网链接策略（强制）
- 外网访问主机必须为公网IP（IPv4），不使用域名作为交付主机。
- 公网IP获取顺序：
  - 优先读取预置配置：`PUBLIC_IP`。
  - 其次从环境/网络信息中自动探测本机公网 IPv4。
  - 若仍不可得，向用户询问公网IP后再输出测试链接。
- 首次输出测试链接前，必须先完成公网IP获取，不等待用户二次追问。
- 外网测试链接格式：
  - 微私域会话管理：`http://<公网IP>:8080/manage-dev/`
  - autotape会话存档：`http://<公网IP>:8080/autotape-dev/`
  - 云顶scrm：`http://<公网IP>:8080/ydscrm-dev/`
  - 项目开发：`http://<公网IP>:8080/project-dev/`
  - 腾讯云（首页）：`http://<公网IP>:8080/tencent-dev/`
    - 云计算网络：`http://<公网IP>:8080/tencent-network-dev/`
    - 云AI智能：`http://<公网IP>:8080/tencent-ai-dev/`
    - 办公协同SaaS：`http://<公网IP>:8080/tencent-saas-dev/`
    - 云服务器：`http://<公网IP>:8080/tencent-cvm-dev/`
    - 数据库：`http://<公网IP>:8080/tencent-db-dev/`
    - 云负载均衡：`http://<公网IP>:8080/tencent-clb-dev/`
    - 存储服务：`http://<公网IP>:8080/tencent-storage-dev/`
    - 云上网络：`http://<公网IP>:8080/tencent-vpc-dev/`
    - 腾讯乐享知识库：`http://<公网IP>:8080/tencent-lexiang-dev/`
    - WorkBuddy：`http://<公网IP>:8080/tencent-workbuddy-dev/`
    - 智能体开发平台：`http://<公网IP>:8080/tencent-agent-dev/`
    - 腾讯企点智能客服：`http://<公网IP>:8080/tencent-qidian-dev/`
    - 腾讯会议：`http://<公网IP>:8080/tencent-meeting-dev/`
    - 腾讯电子签：`http://<公网IP>:8080/tencent-esign-dev/`
    - iOA 零信任安全管理：`http://<公网IP>:8080/tencent-ioa-dev/`
    - TAPD敏捷项目管理：`http://<公网IP>:8080/tencent-tapd-dev/`
    - 腾讯问卷：`http://<公网IP>:8080/tencent-survey-dev/`
  - 火山云（首页）：`http://<公网IP>:8080/volc-dev/`
    - 云计算：`http://<公网IP>:8080/volc-cloud-dev/`
    - 大模型：`http://<公网IP>:8080/volc-llm-dev/`
    - AI智能：`http://<公网IP>:8080/volc-ai-dev/`
- 若外网链接校验失败：
  - 不得降级仅返回内网链接充当结果。
  - 必须返回“外网不可达原因 + 修复建议 + 当前外网链接”。
  - 可附带内网排障链接，但必须明确标注“仅排障，不作为交付链接”。
- 若公网IP自动获取失败：
  - 不得返回占位符链接。
  - 必须明确提示“未获取到公网IP”，并向用户询问公网IP后再输出链接。

## 测试链接生成与校验（强制）
- 频道与路径必须一一对应，不得自由拼写：
  - 微私域会话管理 -> `/manage-dev/`
  - autotape会话存档 -> `/autotape-dev/`
  - 云顶scrm -> `/ydscrm-dev/`
  - 项目开发 -> `/project-dev/`
  - 腾讯云（首页） -> `/tencent-dev/`
    - 云计算网络 -> `/tencent-network-dev/`
    - 云AI智能 -> `/tencent-ai-dev/`
    - 办公协同SaaS -> `/tencent-saas-dev/`
    - 云服务器 -> `/tencent-cvm-dev/`
    - 数据库 -> `/tencent-db-dev/`
    - 云负载均衡 -> `/tencent-clb-dev/`
    - 存储服务 -> `/tencent-storage-dev/`
    - 云上网络 -> `/tencent-vpc-dev/`
    - 腾讯乐享知识库 -> `/tencent-lexiang-dev/`
    - WorkBuddy -> `/tencent-workbuddy-dev/`
    - 智能体开发平台 -> `/tencent-agent-dev/`
    - 腾讯企点智能客服 -> `/tencent-qidian-dev/`
    - 腾讯会议 -> `/tencent-meeting-dev/`
    - 腾讯电子签 -> `/tencent-esign-dev/`
    - iOA 零信任安全管理 -> `/tencent-ioa-dev/`
    - TAPD敏捷项目管理 -> `/tencent-tapd-dev/`
    - 腾讯问卷 -> `/tencent-survey-dev/`
  - 火山云（首页） -> `/volc-dev/`
    - 云计算 -> `/volc-cloud-dev/`
    - 大模型 -> `/volc-llm-dev/`
    - AI智能 -> `/volc-ai-dev/`
- 对用户交付的测试链接格式固定：`http://<公网IP>:8080<频道测试路径>`
- 返回结果前必须做可达性校验（至少一次）：
  - 校验 URL 与频道映射一致（端口必须为 `8080`）。
  - 校验 HTTP 响应为 `200` / `301` / `302` 之一。
  - 若返回 HTML 内容，首页应可加载（`index.html` 可访问）。
- 任一校验失败时：
  - 不得声称“操作完成”。
  - 必须返回“失败原因 + 修复建议 + 下一步动作”。
  - 仍需给出当前尝试的测试链接，方便用户复核。

## 发布与备份规则（强制）
- 固定发布触发语：`我想发布到生产`（可包含同义近似表达，但语义必须明确）。
- 二次确认成功后才能发布，未确认即终止。
- 发布前必须完整备份当前生产目录到：
  - `/data/backup/<channel>/<YYYYMMDD>_v<version>/`
- 版本号规则：同一天内按顺序递增（`v1`、`v2`...）。
- 发布方式为全量镜像：以测试目录为准覆盖生产目录，并删除生产中测试不存在的冗余文件。
- 备份失败或镜像失败时，必须停止并返回错误，不得继续后续步骤。

## 安全约束（强制）
- 仅允许在以下白名单目录操作：`/data/dev/*`、`/data/product/*`、`/data/backup/*`（且仅限映射频道子目录）。
- 禁止访问白名单外路径。
- 禁止路径穿越（如 ../）。
- 频道不在映射表中时，提示用户从可选频道中重新选择（完整列表含子频道）：
  - 微私域会话管理
  - autotape会话存档
  - 云顶scrm
  - 项目开发
  - 腾讯云（子频道：云计算网络 / 云AI智能 / 办公协同SaaS 及各三级服务项）
  - 火山云（子频道：云计算 / 大模型 / AI智能）
- 未满足发布触发语与二次确认时，禁止任何生产目录写操作。

## 执行输出（每次必须）
- 操作类型（UI）
- 频道
- 执行阶段（测试修改 / 生产发布）
- 目标目录（dev 或 prod）
- 修改文件清单
- 变更摘要
- 若为测试修改，必须额外输出：
  - 测试访问路径（固定频道路径）
  - 外网测试链接（可点击完整 URL，主机必须为公网IP，不允许占位符、不得为内网地址）
  - 链接校验结果（PASS / FAIL）
  - HTTP状态码（如 `200` / `301` / `302`）
  - Nginx处理结果（复用已有location / 新增location / 修正location）
  - 配置文件（固定为`/etc/nginx/conf.d/aipage.conf`，文件名未变更）
  - Header Logo自检结果（路径/点击跳转/整块可点击/非header图标误改）
  - 若附带内网链接，必须标注“仅排障”
- 若为生产发布，额外输出：
  - 发布触发语命中结果
  - 二次确认结果
  - 备份目录（含日期+版本）
  - 全量镜像结果（成功/失败）

## 默认行为示例（防跑偏）
- 用户说："我想建界面" -> 直接列出全部频道及子菜单结构（含腾讯云三级、火山云二级）供用户选择；频道确定后，直接在对应 `dev` 目录创建。
- 用户说：“微私域会话管理下新增一个页面” -> 直接在 `/data/dev/manage` 执行，不询问 prod。
- 完成用户测试修改后 -> 首次必须返回外网可访问链接：`http://<公网IP>:8080/manage-dev/`（按频道替换路径）。
- 用户说：“我想发布到生产” -> 不执行发布，先做二次确认。
- 用户仅说“发布一下”且语义不明确 -> 视为未命中固定触发语，不得改动 prod。
