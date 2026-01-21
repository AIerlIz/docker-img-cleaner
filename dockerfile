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

# 设置一个 cron 任务来定期运行 Python 脚本
# 每天凌晨 3 点运行脚本
# 将脚本的输出（包括日志）重定向到标准输出，以便通过 `docker logs` 查看
# 默认每天凌晨 3 点运行，可以通过 CRON_SCHEDULE 环境变量覆盖
ARG CRON_SCHEDULE="0 3 * * *"
RUN (crontab -l 2>/dev/null; echo "${CRON_SCHEDULE} /usr/bin/python3 /app/docker_cleanup_report.py >> /dev/stdout 2>&1") | crontab -

# 启动 cron 服务，并保持容器在前台运行
CMD ["crond", "-f"]
