import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class NotificationType(Enum):
    LIVE_START = "live_start"
    LIVE_END = "live_end"


@dataclass
class RoomInfo:
    """直播间信息"""

    room_id: int
    title: str
    live_status: bool
    live_time: str
    area_name: str
    tags: List[str]
    hot_words: List[str]
    online: int
    attention: int
    user_cover: Optional[str] = None
    keyframe: Optional[str] = None
    is_strict_room: bool = False
    room_silent_type: str = ""
    room_silent_level: int = 0
    room_silent_second: int = 0
    background: Optional[str] = None
    verify: str = ""
    new_pendants: dict = field(default_factory=dict)
    up_session: Optional[str] = None
    pk_status: int = 0
    pk_id: int = 0
    battle_id: int = 0
    allow_change_area_time: int = 0
    allow_upload_cover_time: int = 0
    studio_info: dict = field(default_factory=dict)


class RoomStatus(BaseModel):
    """开播信息存储"""

    room_id: int = Field(..., description="房间号")
    live_status: bool = Field(..., description="是否开播")

    def save_to_json(self, file_path: str) -> bool:
        """
        保存直播状态到JSON文件

        Args:
            file_path: JSON文件路径，如果为None则使用默认路径

        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # 转换为字典并保存
            data = self.model_dump()

            with Path(file_path).open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存直播状态到JSON文件失败: {e}")
            return False
        else:
            return True

    @classmethod
    def load_from_json(cls, file_path: Optional[str] = None) -> Optional["RoomStatus"]:
        """
        从JSON文件加载直播状态

        Args:
            file_path: JSON文件路径，如果为None则使用默认路径

        Returns:
            RoomStatus: 直播状态对象，如果加载失败返回None
        """
        try:
            if file_path is None:
                # 使用默认路径：当前目录下的room_status.json
                file_path = str(Path(__file__).parent / "room_status.json")

            if not Path(file_path).exists():
                return None

            with Path(file_path).open("r", encoding="utf-8") as f:
                data = json.load(f)

            if "room_id" in data and "live_status" in data:
                return cls(**data)
            return None
        except Exception as e:
            print(f"从JSON文件加载直播状态失败: {e}")
            return None

    @classmethod
    def load_status_map(cls, file_path: Optional[str] = None) -> Dict[int, bool]:
        try:
            if file_path is None:
                file_path = str(Path(__file__).parent / "room_status.json")

            if not Path(file_path).exists():
                return {}

            with Path(file_path).open("r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                if "room_id" in data and "live_status" in data:
                    room_id = int(data.get("room_id", 0))
                    live_status = bool(data.get("live_status", False))
                    return {room_id: live_status} if room_id else {}
                if "rooms" in data and isinstance(data["rooms"], dict):
                    result: Dict[int, bool] = {}
                    for key, value in data["rooms"].items():
                        try:
                            room_id = int(key)
                        except (ValueError, TypeError):
                            continue
                        result[room_id] = bool(value)
                    return result
            if isinstance(data, list):
                result: Dict[int, bool] = {}
                for item in data:
                    if (
                        isinstance(item, dict)
                        and "room_id" in item
                        and "live_status" in item
                    ):
                        try:
                            room_id = int(item.get("room_id", 0))
                        except (ValueError, TypeError):
                            continue
                        result[room_id] = bool(item.get("live_status", False))
                return result
            return {}
        except Exception as e:
            print(f"从JSON文件加载直播状态失败: {e}")
            return {}

    @classmethod
    def save_status_map(cls, file_path: str, status_map: Dict[int, bool]) -> bool:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            payload = {"rooms": {str(k): bool(v) for k, v in status_map.items()}}
            with Path(file_path).open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存直播状态到JSON文件失败: {e}")
            return False
        else:
            return True
