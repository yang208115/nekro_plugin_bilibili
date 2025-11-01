from nonebot import get_bot
from nonebot.adapters.onebot.v11 import MessageSegment

from .conf import config
from .models import RoomInfo ,NotificationType

from nekro_agent.api.core import logger



async def notice(room_info: RoomInfo, notification_type: NotificationType = NotificationType.LIVE_START):
    if not config.notification_group:
        logger.warning("未配置通知群号，跳过发送通知")
        return

    at = MessageSegment.at('all')

    if notification_type == NotificationType.LIVE_END:
        message = f"{at} {config.streamer_name}下播啦!"
    elif notification_type == NotificationType.LIVE_START:
        message = f"{at} {config.streamer_name}开播啦!\n房间号:{room_info.room_id}\n标题:{room_info.title}"

    await send_message(message)

async def send_message(msg: str):
    bot = get_bot()
    await bot.call_api("send_group_msg", group_id=int(config.notification_group), message=msg)
    logger.info(f"已发送通知到群 {config.notification_group}")
