from typing import List

from pydantic import Field

from nekro_agent.api.plugin import ConfigBase, NekroPlugin

plugin = NekroPlugin(
    name="BiliBili直播监控",
    module_name="nekro_plugin_bilibili",
    description="监控B站主播开播状态并通过QQ发送通知",
    author="yang208115",
    version="0.1.1",
    url="https://github.com/yang208115/nekro-plugin-bilibili",
)

@plugin.mount_config()
class BasicConfig(ConfigBase):
    """基础配置"""

    enable: bool = Field(
        default=True,
        title="是否启用",
    )
    
    check_interval: int = Field(
        default=10,
        title="轮询间隔（秒）",
        description="检查直播状态的间隔时间，建议不要设置太短避免被限制",
    )

    notification_group: List[str] = Field(
        default=[],
        title="通知群号列表",
        description="需要发送通知的QQ群号列表",
    )

    room_ids: List[int] = Field(
        default=[],
        title="房间号列表",
        description="多个房间号列表",
    )

    streamer_names: List[str] = Field(
        default=[],
        title="主播名字列表",
        description="与房间号列表一一对应的主播名字",
    )

    is_at_all: bool = Field(
        default=False,
        title="是否@全体成员",
        description="是否@全体成员",
    )

    is_push_system: bool = Field(
        default=True,
        title="是否唤醒AI",
        description="是否唤醒AI",
    )



# 获取配置
config: BasicConfig = plugin.get_config(BasicConfig)
