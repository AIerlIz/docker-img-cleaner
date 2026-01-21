#!/bin/bash

# 默认的 cron 调度，如果 CRON_SCHEDULE 环境变量未设置
CRON_SCHEDULE=${CRON_SCHEDULE:-"0 3 * * *"}

echo "Using CRON_SCHEDULE: ${CRON_SCHEDULE}"

# 将 cron 任务添加到 crontab
# 脚本的输出重定向到标准输出，以便通过 `docker logs` 查看
(crontab -l 2>/dev/null; echo "${CRON_SCHEDULE} /usr/bin/python3 /app/docker_cleanup_report.py >> /proc/1/fd/1 2>&1") | crontab -

# 启动 cron 服务，并保持容器在前台运行
crond -f
