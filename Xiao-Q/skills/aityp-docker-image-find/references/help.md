## 命令行帮助
usage: docker-search [-h] {search,detail,pull} ...

从 docker.aityp.com 搜索 Docker 镜像并获取拉取地址

positional arguments:
  {search,detail,pull}  可用命令
    search              搜索镜像
    detail              获取镜像详情（拉取地址）
    pull                搜索镜像并输出 docker pull 命令

options:
  -h, --help            show this help message and exit

示例:
  docker-search search nginx                    # 搜索 nginx 镜像
  docker-search search redis --limit 5          # 只显示前 5 条
  docker-search search mysql --format json      # JSON 格式输出
  docker-search detail /i/library/nginx         # 获取镜像拉取地址
  docker-search pull nginx                      # 搜索并获取第一个结果的拉取地址