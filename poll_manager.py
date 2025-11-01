import asyncio
from typing import Optional, Callable

from .conf import config, plugin
from .api_client import api
from .models import RoomInfo, RoomStatus, NotificationType

from nekro_agent.api.core import logger

class PollManager:
    def __init__(self):
        self._running = False
        self._task = None
        self.call_back = None

    async def start(self):
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_tasks())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("轮询系统已停止")

    async def _run_tasks(self):
        """轮询主循环"""
        while True:
            try:
                await self._poll_once()
                await asyncio.sleep(config.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"轮询循环错误: {e}")
                await asyncio.sleep(min(config.check_interval, 30))

    async def _poll_once(self):
        try:
            res = await api.get_live_room_info(config.room_id)
            if not res:
                logger.error("获取直播间信息失败：API返回空数据")
                return

            room_info = self._convert_to_room_info(res)
            logger.debug(f"直播间状态解析: live_status={room_info.live_status}, title={room_info.title}")

            # 获取插件路径用于保存JSON文件
            path = str(plugin.get_plugin_path()) + "/RoomStatus.json"

            # 检查之前的开播记录
            previous_status = RoomStatus.load_from_json(path)

            if room_info.live_status:
                # 当前开播状态
                if previous_status and previous_status.live_status:
                    # 之前已经有开播记录，不通知
                    logger.debug(f"直播间 {room_info.room_id} 已在开播状态，跳过通知")
                else:
                    # 检测到新的开播，保存记录并通知
                    current_status = RoomStatus(room_id=room_info.room_id, live_status=True)
                    current_status.save_to_json(path)
                    logger.debug(f"检测到新开播: 房间 {room_info.room_id}, 标题: {room_info.title}")

                    if self.call_back:
                        await self.call_back(room_info, NotificationType.LIVE_START)
                    else:
                        logger.warning("回调函数未设置")
            else:
                # 当前未开播状态，更新记录
                if previous_status and previous_status.live_status:
                    # 从开播状态变为未开播，更新记录
                    current_status = RoomStatus(room_id=room_info.room_id, live_status=False)
                    current_status.save_to_json(path)
                    if self.call_back:
                        await self.call_back(room_info, NotificationType.LIVE_END)
                else:
                    logger.debug("主播未开播")
        except Exception as e:
            logger.error(f"轮询直播间信息时发生错误: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")

    def _convert_to_room_info(self, api_data: dict) -> RoomInfo:
        """
        将API响应数据转换为RoomInfo对象

        Args:
            api_data: Bilibili API返回的原始数据

        Returns:
            RoomInfo: 转换后的房间信息对象

        Raises:
            ValueError: 当API数据格式不正确时抛出
        """
        if not isinstance(api_data, dict):
            raise ValueError("API数据必须是字典格式")

        # 验证必要字段
        room_id = api_data.get('room_id')
        if not room_id:
            logger.warning(f"API返回的room_id为空，使用配置中的room_id: {config.room_id}")
            room_id = config.room_id
        elif not isinstance(room_id, int):
            try:
                room_id = int(room_id)
            except (ValueError, TypeError):
                logger.warning(f"API返回的room_id格式无效: {room_id}，使用配置中的room_id: {config.room_id}")
                room_id = config.room_id

        # 处理标题，确保是字符串
        title = api_data.get('title', '')
        if not isinstance(title, str):
            title = str(title) if title is not None else ''

        # 处理标签数据，API可能返回字符串或列表
        tags = api_data.get('tags', '')
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
        elif isinstance(tags, list):
            # 确保列表中的所有元素都是字符串
            tags = [str(tag).strip() for tag in tags if tag is not None]
        else:
            tags = []

        # 处理热词数据
        hot_words = api_data.get('hot_words', [])
        if isinstance(hot_words, list):
            # 确保列表中的所有元素都是字符串
            hot_words = [str(word).strip() for word in hot_words if word is not None]
        else:
            hot_words = []

        # 转换直播状态
        live_status = bool(api_data.get('live_status', 0))

        # 处理直播时间
        live_time = api_data.get('live_time', '')
        if not isinstance(live_time, str):
            live_time = str(live_time) if live_time is not None else ''

        # 处理区域名称
        area_name = api_data.get('area_name', '')
        if not isinstance(area_name, str):
            area_name = str(area_name) if area_name is not None else ''

        # 处理数值字段，确保类型正确
        online = self._safe_int_convert(api_data.get('online', 0))
        attention = self._safe_int_convert(api_data.get('attention', 0))
        room_silent_level = self._safe_int_convert(api_data.get('room_silent_level', 0))
        room_silent_second = self._safe_int_convert(api_data.get('room_silent_second', 0))
        pk_status = self._safe_int_convert(api_data.get('pk_status', 0))
        pk_id = self._safe_int_convert(api_data.get('pk_id', 0))
        battle_id = self._safe_int_convert(api_data.get('battle_id', 0))
        allow_change_area_time = self._safe_int_convert(api_data.get('allow_change_area_time', 0))
        allow_upload_cover_time = self._safe_int_convert(api_data.get('allow_upload_cover_time', 0))

        # 处理布尔字段
        is_strict_room = bool(api_data.get('is_strict_room', False))

        # 处理字符串字段，确保类型安全
        room_silent_type = api_data.get('room_silent_type', '')
        verify = api_data.get('verify', '')
        user_cover = api_data.get('user_cover')
        keyframe = api_data.get('keyframe')
        background = api_data.get('background')
        up_session = api_data.get('up_session')

        # 确保字符串字段类型
        room_silent_type = str(room_silent_type) if room_silent_type is not None else ''
        verify = str(verify) if verify is not None else ''

        # 确保URL字段类型
        user_cover = str(user_cover) if user_cover is not None else None
        keyframe = str(keyframe) if keyframe is not None else None
        background = str(background) if background is not None else None
        up_session = str(up_session) if up_session is not None else None

        # 处理字典字段，确保类型安全
        new_pendants = api_data.get('new_pendants', {})
        if not isinstance(new_pendants, dict):
            new_pendants = {}

        studio_info = api_data.get('studio_info', {})
        if not isinstance(studio_info, dict):
            studio_info = {}

        try:
            return RoomInfo(
                room_id=room_id,
                title=title,
                live_status=live_status,
                live_time=live_time,
                area_name=area_name,
                tags=tags,
                hot_words=hot_words,
                online=online,
                attention=attention,
                user_cover=user_cover,
                keyframe=keyframe,
                is_strict_room=is_strict_room,
                room_silent_type=room_silent_type,
                room_silent_level=room_silent_level,
                room_silent_second=room_silent_second,
                background=background,
                verify=verify,
                new_pendants=new_pendants,
                up_session=up_session,
                pk_status=pk_status,
                pk_id=pk_id,
                battle_id=battle_id,
                allow_change_area_time=allow_change_area_time,
                allow_upload_cover_time=allow_upload_cover_time,
                studio_info=studio_info,
            )
        except Exception as e:
            logger.error(f"创建RoomInfo对象时发生错误: {e}")
            # 返回一个基本的RoomInfo对象作为备用
            return RoomInfo(
                room_id=room_id,
                title=title or '未知直播间',
                live_status=False,
                live_time='',
                area_name='',
                tags=[],
                hot_words=[],
                online=0,
                attention=0,
            )

    def _safe_int_convert(self, value, default=0):
        """
        安全地将值转换为整数

        Args:
            value: 要转换的值
            default: 默认值

        Returns:
            int: 转换后的整数值
        """
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    async def registerCallback(self, callback: Optional[Callable[[RoomInfo, NotificationType], None]] = None):
        self.call_back = callback

poll_manager = PollManager()