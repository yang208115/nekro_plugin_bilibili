from typing import List

from nonebot import get_bot
from nonebot.adapters.onebot.v11 import MessageSegment

from nekro_agent.api.core import logger
from nekro_agent.services.message_service import message_service

from .conf import config
from .models import NotificationType, RoomInfo


async def notice(
    room_info: RoomInfo,
    notification_type: NotificationType = NotificationType.LIVE_START):

    if not config.enable:
        logger.warning("插件未启用，跳过发送通知")
        return

    notification_groups = _get_notification_groups_from_config()
    if not notification_groups:
        logger.warning("未配置通知群号，跳过发送通知")
        return
    streamer_name = _resolve_streamer_name(room_info.room_id)
    if config.is_at_all:
        at = MessageSegment.at("all")

        if notification_type == NotificationType.LIVE_END:
            message = f"{at} {streamer_name}下播啦!\n地址: https://live.bilibili.com/{room_info.room_id}"
        elif notification_type == NotificationType.LIVE_START:
            message = f"{at} {streamer_name}开播啦!\n地址: https://live.bilibili.com/{room_info.room_id} \n标题:{room_info.title}"
    else:
        if notification_type == NotificationType.LIVE_END:
            message = f"{streamer_name}下播啦!\n地址: https://live.bilibili.com/{room_info.room_id}"
        elif notification_type == NotificationType.LIVE_START:
            message = f"{streamer_name}开播啦!\n地址: https://live.bilibili.com/{room_info.room_id} \n标题:{room_info.title}"

    if config.is_push_system:
        for group_id in notification_groups:
            await message_service.push_system_message(
                chat_key=f"onebot_v11-group_{group_id}",
                agent_messages=message,
                trigger_agent=True,
            )

    for group_id in notification_groups:
        await send_message(message, group_id)


async def send_message(msg: str, group_id: str):
    group_id_value = group_id
    if isinstance(group_id, str):
        group_id_value = group_id.strip()
        if group_id_value.isdigit():
            group_id_value = int(group_id_value)
    bot = get_bot()
    await bot.call_api(
        "send_group_msg",
        group_id=group_id_value,
        message=msg,
    )
    logger.info(f"已发送通知到群 {group_id}")


def _resolve_streamer_name(room_id: int) -> str:
    room_ids = _get_room_ids_from_config()
    streamer_names = _get_streamer_names_from_config()
    try:
        index = room_ids.index(int(room_id))
    except (ValueError, TypeError):
        index = -1

    if index >= 0 and index < len(streamer_names):
        name = str(streamer_names[index]).strip()
        if name:
            return name
    return "主播"


def _get_room_ids_from_config() -> List[int]:
    room_ids: List[int] = []
    raw_list = config.room_ids
    if isinstance(raw_list, list):
        for item in raw_list:
            try:
                room_ids.append(int(item))
            except (ValueError, TypeError):
                continue
    elif isinstance(raw_list, str):
        raw = raw_list.strip()
        if raw:
            for part in raw.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    room_ids.append(int(part))
                except (ValueError, TypeError):
                    continue

    seen = set()
    result: List[int] = []
    for value in room_ids:
        if value <= 0 or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _get_notification_groups_from_config() -> List[str]:
    group_ids: List[str] = []
    raw_list = config.notification_group
    if isinstance(raw_list, list):
        for item in raw_list:
            value = str(item).strip()
            if not value:
                continue
            group_ids.append(value)
    elif isinstance(raw_list, str):
        raw = raw_list.strip()
        if raw:
            for part in raw.split(","):
                part = part.strip()
                if not part:
                    continue
                group_ids.append(part)

    seen = set()
    result: List[str] = []
    for value in group_ids:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _get_streamer_names_from_config() -> List[str]:
    raw_list = config.streamer_names
    if isinstance(raw_list, list):
        return [str(item).strip() for item in raw_list if str(item).strip()]
    if isinstance(raw_list, str):
        raw = raw_list.strip()
        if not raw:
            return []
        return [part.strip() for part in raw.split(",") if part.strip()]
    return []
