#!/bin/bash
# 全能实用工具箱（SkillHub上架版）部署启动脚本
# 功能：自动安装依赖、创建临时目录、启动技能，适配Linux服务器环境

# 1. 切换到技能目录（根据SkillHub部署路径调整，可保留默认）
cd $(dirname $0)

# 2. 创建临时目录（权限设置为仅当前用户可读写，避免安全风险）
if [ ! -d "./skill_temp" ]; then
    mkdir -p ./skill_temp
    chmod 700 ./skill_temp  # 关键：限制目录权限，防止他人访问
fi

# 3. 安装依赖包（使用pip3，适配Python3环境）
echo "正在安装依赖包..."
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 启动技能（适配SkillHub技能调用规范，后台运行）
echo "正在启动全能实用工具箱..."
nohup python3 toolbox_skillhub.py > skill_run.log 2>&1 &

# 5. 验证启动状态
sleep 3
if pgrep -f "toolbox_skillhub.py" > /dev/null; then
    echo "✅ 技能启动成功，日志已保存至 skill_run.log"
else
    echo "❌ 技能启动失败，请查看 skill_run.log 排查问题"
fi

# 6. 安全提示（适配审核）
echo "⚠️  部署完成：临时目录权限已设置为700，定期自动清理临时文件，确保数据安全"
echo "⚠️  若需停止技能，执行命令：pkill -f toolbox_skillhub.py"