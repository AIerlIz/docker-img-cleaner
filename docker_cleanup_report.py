import os
import logging
import datetime
import requests
import docker
import sys

# --- 配置 ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
DURATION_STR = os.environ.get("DURATION", "72h")

# --- 常量 ---
BYTE_UNITS = ("B", "KB", "MB", "GB", "TB")

# --- 日志设置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# --- 辅助函数 ---
def format_bytes(bytes_value):
    """将字节数转换为人类可读的格式 (B, KB, MB, GB, TB)。"""
    if bytes_value is None:
        return "N/A"
    bytes_value = int(bytes_value)
    if bytes_value == 0:
        return "0 B"
    
    i = 0
    value = float(bytes_value)
    
    while value >= 1024 and i < len(BYTE_UNITS) - 1:
        value /= 1024
        i += 1
    
    return f"{value:.2f} {BYTE_UNITS[i]}"

def send_telegram_message(message):
    """向配置的 Telegram 机器人发送消息。"""
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("Telegram BOT_TOKEN 或 CHAT_ID 未设置。跳过 Telegram 通知。")
        return

    telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "parse_mode": "Markdown",
        "text": message
    }
    
    try:
        logger.info("正在发送 Telegram 消息...")
        response = requests.post(telegram_api_url, json=payload)
        response.raise_for_status()
        logger.info("Telegram 消息发送成功。")
    except requests.exceptions.RequestException as e:
        logger.error(f"发送 Telegram 消息失败: {e}")

def _connect_docker_client():
    """连接到 Docker Daemon 并返回客户端对象。"""
    try:
        client = docker.from_env()
        client.ping()
        logger.info("成功连接到 Docker Daemon。")
        return client
    except Exception as e:
        logger.error(f"连接 Docker Daemon 失败: {e}")
        send_telegram_message(
            f"*Docker 镜像清理脚本失败 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            f"状态: ❌ 失败\n原因: 无法连接到 Docker Daemon。\n`{e}`"
        )
        sys.exit(1)

def _get_images(client):
    """获取所有 Docker 镜像列表。"""
    images_dict = {} # {image_id: {"tags": [], "size": bytes}}
    try:
        logger.info("正在获取 Docker 镜像列表...")
        for image in client.images.list(all=True):
            image_id = image.short_id.split(':')[-1]
            tags = image.tags if image.tags else [f"<none>:<none> ({image_id[:12]})"]
            images_dict[image_id] = {
                "tags": tags,
                "size": image.attrs.get('Size')
            }
        logger.info(f"发现 {len(images_dict)} 个镜像。")
        return images_dict
    except Exception as e:
        logger.error(f"获取 Docker 镜像列表失败: {e}")
        send_telegram_message(
            f"*Docker 镜像清理脚本失败 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            f"状态: ❌ 失败\n原因: 无法获取 Docker 镜像列表。\n`{e}`"
        )
        sys.exit(1)

def _prune_images(client, duration_str):
    """执行 Docker 镜像清理操作。"""
    prune_filter = {}
    if duration_str and duration_str != "0h":
        prune_filter["until"] = duration_str
        logger.info(f"正在清理创建时间超过 {duration_str} 的镜像 (过滤条件: {prune_filter})...")
    else:
        prune_filter["dangling"] = False
        logger.info("正在清理所有未使用的 Docker 镜像 (无时间过滤，等同于 docker image prune -a)...")

    try:
        prune_result = client.images.prune(filters=prune_filter)
        logger.info(f"Docker 镜像清理完成。回收空间: {format_bytes(prune_result.get('SpaceReclaimed'))}")
        if prune_result.get('ImagesDeleted'):
            logger.info(f"已删除镜像: {prune_result.get('ImagesDeleted')}")
        return prune_result, True
    except Exception as e:
        logger.error(f"Docker 镜像清理过程中发生错误: {e}")
        return {"error": str(e)}, False

def _generate_report_message(prune_success, prune_result, removed_images_list, total_reclaimed_size_bytes):
    """生成 Telegram 报告消息。"""
    telegram_message = f"*Docker 镜像清理报告 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"

    if prune_success:
        telegram_message += "状态: ✅ 清理成功\n"
    else:
        telegram_message += "状态: ❌ 清理失败\n"
        if prune_result and prune_result.get("error"):
            telegram_message += f"错误详情:\n`{prune_result['error']}`\n"
        else:
            telegram_message += "错误详情: 未知错误 (请查看日志获取详情)\n"

    if removed_images_list:
        telegram_message += f"清理的镜像列表 ({len(removed_images_list)} 个):\n"
        removed_images_list.sort()
        telegram_message += "\n".join(removed_images_list)
        telegram_message += f"\n\n*总计回收空间:* {format_bytes(total_reclaimed_size_bytes)}\n"
    else:
        telegram_message += "没有发现需要清理的镜像，或清理命令没有删除任何镜像。\n"
        if prune_result and prune_result.get('SpaceReclaimed', 0) > 0:
            telegram_message += f"Docker 报告: 总计回收空间: {format_bytes(prune_result['SpaceReclaimed'])}"

    return telegram_message

def main():
    logger.info("Docker 镜像清理脚本 (Python) 开始运行...")

    client = _connect_docker_client()

    before_prune_images = _get_images(client)

    prune_result, prune_success = _prune_images(client, DURATION_STR)

    after_prune_image_ids = set()
    if prune_success:
        after_prune_images = _get_images(client)
        after_prune_image_ids = set(after_prune_images.keys())
    else:
        logger.warning("由于之前的清理错误，跳过获取清理后的镜像列表。")

    removed_images_list = []
    total_reclaimed_size_bytes = 0

    if prune_success:
        for image_id, info in before_prune_images.items():
            if image_id not in after_prune_image_ids:
                image_tags = ", ".join(info["tags"])
                image_size = info["size"]
                removed_images_list.append(f"• {image_tags} ({format_bytes(image_size)})")
                if image_size is not None:
                    total_reclaimed_size_bytes += image_size
    
    if prune_result and prune_result.get('SpaceReclaimed') is not None:
        actual_reclaimed_space = prune_result.get('SpaceReclaimed')
        if actual_reclaimed_space > 0 and (total_reclaimed_size_bytes == 0 or abs(actual_reclaimed_space - total_reclaimed_size_bytes) > 100):
             logger.info(f"使用 Docker 报告的回收空间: {format_bytes(actual_reclaimed_space)}")
             total_reclaimed_size_bytes = actual_reclaimed_space
    
    telegram_message = _generate_report_message(prune_success, prune_result, removed_images_list, total_reclaimed_size_bytes)
    send_telegram_message(telegram_message)
    logger.info("Docker 镜像清理脚本 (Python) 运行结束。")

if __name__ == "__main__":
    main()
