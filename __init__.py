"""     江城子 . 程序员之歌

   十年生死两茫茫,写程序，到天亮。
        千行代码,Bug何处藏。
   纵使上线又怎样,朝令改，夕断肠。

   领导每天新想法,天天改，日日忙。
        相顾无言,惟有泪千行。
   每晚灯火阑珊处,夜难寐，加班狂。
"""
from .conf import plugin
from nekro_agent.api.core import logger
from .poll_manager import poll_manager as pm
from .handlers import notice

__all__ = ["plugin"]

@plugin.mount_init_method()
async def init_plugin():
    """插件初始化"""
    logger.info("哔哩哔哩工具开始初始化")
    await pm.start()
    await pm.registerCallback(notice)

@plugin.mount_cleanup_method()
async def cleanup_plugin():
    """插件清理"""
    await pm.stop()
    logger.info("哔哩哔哩工具卸载")


