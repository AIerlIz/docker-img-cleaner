
#!/bin/bash

# 如果 CRON_SCHEDULE 环境变量存在，则使用它来设置 cron 任务
if [ -n "$CRON_SCHEDULE" ]; then
  echo "Setting cron schedule to: $CRON_SCHEDULE"
  # 清除现有 crontab 并添加新的任务
  (crontab -l 2>/dev/null; echo "${CRON_SCHEDULE} /usr/bin/python3 /app/docker_cleanup_report.py >> /dev/stdout 2>&1") | crontab -
else
  echo "CRON_SCHEDULE not set, using default schedule (0 3 * * *)."
  # 使用默认调度
  (crontab -l 2>/dev/null; echo "0 3 * * * /usr/bin/python3 /app/docker_cleanup_report.py >> /dev/stdout 2>&1") | crontab -
fi

# 启动 cron 服务，并保持容器在前台运行
crond -f
