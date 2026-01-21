# Docker Image Cleaner

这个项目提供了一个 Docker 容器，用于定期清理旧的 Docker 镜像，并通过 Telegram 发送清理报告。

## 功能特点

- 定期清理未使用的 Docker 镜像。
- 可配置清理时长（例如：保留最近 72 小时内的镜像）。
- 通过 Telegram Bot 发送清理结果报告。
- 支持自定义 Cron 调度。
- 默认时区设置为 `Asia/Shanghai`。

## 设置与运行

### 前提条件

- Docker 和 Docker Compose 已安装在您的系统上。
- 一个 Telegram Bot Token 和 Chat ID，用于接收通知。

### 1. 克隆仓库

```bash
git clone https://github.com/AIerlIz/docker-img-cleaner.git
cd docker-img-cleaner
```

### 2. 配置 Telegram 通知

打开 `compose.yml` 文件，并替换 `BOT_TOKEN` 和 `CHAT_ID` 环境变量为您的 Telegram Bot 信息：

```yaml
    environment:
      - BOT_TOKEN=xxxxx:AAHHiKVCk-xxxxxxxxx  # ⚠️ 替换为你的 Telegram Bot Token
      - CHAT_ID=xxxxxxxx                 # ⚠️ 替换为你的 Telegram Chat ID
```

### 3. 配置清理时长 (可选)

在 `compose.yml` 文件中，您可以通过 `DURATION` 环境变量配置保留镜像的时长。例如，`24h` 表示保留 24 小时内的镜像，更旧的将被清理。如果设置为 `0h`，将清理所有未使用的镜像（等同于 `docker image prune -a`）。

```yaml
      - DURATION=0h # 默认清理所有未使用的镜像，设置为例如 "72h" 以保留最近 72 小时内的镜像
```

### 4. 配置 Cron 调度 (可选)

默认情况下，清理脚本每天凌晨 3 点运行。您可以通过在 `compose.yml` 中取消注释并修改 `CRON_SCHEDULE` 环境变量来更改调度。

```yaml
      # - CRON_SCHEDULE="0 0 * * *" # 例如，每天午夜运行
```

### 5. 时区设置

容器的时区已默认设置为 `Asia/Shanghai`。这在 `dockerfile` 和 `compose.yml` 中都有体现，确保日志和报告的时间戳正确。

### 6. 构建并运行容器

在项目根目录下执行以下命令来构建 Docker 镜像并启动服务：

```bash
docker-compose up -d --build
```

这将会在后台运行 `docker-image-cleaner` 服务。

## 验证

您可以使用以下命令查看容器日志，确认脚本是否正常运行并发送报告：

```bash
docker logs docker-cleanup-scheduler
```

您应该会在 Telegram 上收到清理报告。

## 停止和移除服务

如果您想停止并移除所有相关的容器、网络和卷，请在项目根目录下执行：

```bash
docker-compose down
```
