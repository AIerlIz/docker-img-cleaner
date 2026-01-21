# 使用官方 Python 3.9 Alpine 镜像作为基础镜像，它体积小且包含 Python
FROM python:3.9-alpine

# 安装 cronie (用于调度), curl (Python requests 库可能依赖它，或者用于调试), bash (用于 crontab 环境)
# 添加 tzdata 用于时区设置
RUN apk add --no-cache cronie curl bash tzdata

# 设置工作目录
WORKDIR /app

# 复制你的 Python 脚本到容器中
COPY docker_cleanup_report.py /app/docker_cleanup_report.py

# 安装 Python 依赖：docker (Docker SDK for Python) 和 requests (用于 Telegram API)
RUN pip install --no-cache-dir docker requests

# 赋予 Python 脚本执行权限 (虽然直接通过 python3 运行，但仍是个好习惯)
RUN chmod +x /app/docker_cleanup_report.py

# 设置时区为中国上海
ENV TZ=Asia/Shanghai
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

# 复制 entrypoint 脚本
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 使用 entrypoint 脚本启动 cron 服务
CMD ["/bin/bash", "/app/entrypoint.sh"]
