from nonebot import get_bot
from nonebot.adapters.onebot.v11 import MessageSegment

from .conf import config
from .models import RoomInfo ,NotificationType

from nekro_agent.api.core import logger
from nekro_agent.services.message_service import message_service



async def notice(room_info: RoomInfo, notification_type: NotificationType = NotificationType.LIVE_START):
    if not config.notification_group:
        logger.warning("未配置通知群号，跳过发送通知")
        return
    if config.is_at_all:
        at = MessageSegment.at('all')

        if notification_type == NotificationType.LIVE_END:
            message = f"{at} {config.streamer_name}下播啦!"
        elif notification_type == NotificationType.LIVE_START:
            message = f"{at} {config.streamer_name}开播啦!\n地址: https://live.bilibili.com/{room_info.room_id} \n标题:{room_info.title}"
    else:
        if notification_type == NotificationType.LIVE_END:
            message = f"{config.streamer_name}下播啦!"
        elif notification_type == NotificationType.LIVE_START:
            message = f"{config.streamer_name}开播啦!\n地址: https://live.bilibili.com/{room_info.room_id} \n标题:{room_info.title}"

    await message_service.push_system_message(chat_key=f'onebot_v11-group_{config.notification_group}', agent_messages=message,  trigger_agent=True)

    await send_message(message)

async def send_message(msg: str):
    bot = get_bot()
    await bot.call_api("send_group_msg", group_id=int(config.notification_group), message=msg)
    logger.info(f"已发送通知到群 {config.notification_group}")
