import asyncio
import time
import random
from typing import Optional, Dict, Any
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class RequestType(str, Enum):
    POST = 'post'
    GET = 'get'

class ApiEndpoints:
    """API 端点常量定义"""
    LIVE_ROOM_INFO = "https://api.live.bilibili.com/room/v1/Room/get_info"
    LIVE_ROOM_GUARD_TAB = "https://api.live.bilibili.com/xlive/app-room/v2/guardTab/topListNew"
    LIVE_ROOM_FANS_MEMBERS_RANK = "https://api.live.bilibili.com/xlive/general-interface/v1/rank/getFansMembersRank"
    LIVE_ROOM_ONLINE_GOLD_RANK = "https://api.live.bilibili.com/xlive/general-interface/v1/rank/getOnlineGoldRank"
    LIVE_ROOM_DANMU = "https://api.live.bilibili.com/ajax/msg"

class DefaultHeaders:
    """默认请求头配置"""
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0"
    BASE_HEADERS = {
        "User-Agent": USER_AGENT,
        "Referer": "https://live.bilibili.com/",
    }
    LIVE_HEADERS = {
        **BASE_HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Origin": "https://live.bilibili.com",
    }

class ApiClientError(Exception):
    """API 客户端自定义异常"""
    pass

class ApiClient:
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        初始化 API 客户端

        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建带重试策略的 session
        self.session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置默认 headers
        self.session.headers.update(DefaultHeaders.BASE_HEADERS)

    def _make_request(self,
                      url: str,
                      method: RequestType,
                      params: Optional[Dict[str, Any]] = None,
                      headers: Optional[Dict[str, str]] = None,
                      **kwargs) -> requests.Response:
        """
        发送 HTTP 请求的通用方法

        Args:
            url: 请求 URL
            method: 请求方法
            params: 查询参数
            headers: 请求头
            **kwargs: 其他 requests 参数

        Returns:
            requests.Response 对象

        Raises:
            ApiClientError: 请求失败时抛出
        """
        # 合并 headers
        request_headers = DefaultHeaders.BASE_HEADERS.copy()
        if headers:
            request_headers.update(headers)

        for attempt in range(1, self.max_retries + 1):
            try:
                if method == RequestType.GET:
                    response = self.session.get(
                        url,
                        params=params,
                        headers=request_headers,
                        timeout=self.timeout,
                        **kwargs
                    )
                elif method == RequestType.POST:
                    response = self.session.post(
                        url,
                        params=params,
                        headers=request_headers,
                        timeout=self.timeout,
                        **kwargs
                    )
                else:
                    raise ApiClientError(f"不支持的请求方法: {method}")

                response.raise_for_status()
                return response

            except requests.exceptions.Timeout as e:
                if attempt == self.max_retries:
                    raise ApiClientError(f"请求超时（重试 {self.max_retries} 次后）: {e}")
                time.sleep(random.uniform(1, 2))

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    raise ApiClientError(f"请求失败（重试 {self.max_retries} 次后）: {e}")
                time.sleep(random.uniform(1, 2))

    async def _get_request(self,
                           url: str,
                           method: RequestType,
                           params: Optional[Dict[str, Any]] = None,
                           headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """
        异步包装的请求方法（保持向后兼容）

        Args:
            url: 请求 URL
            method: 请求方法
            params: 查询参数
            headers: 请求头

        Returns:
            requests.Response 对象
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._make_request,
            url, method, params, headers
        )

    async def get_live_room_info(self, room_id: int) -> Dict[str, Any]:
        """
        获取直播间信息

        Args:
            room_id: 直播间 ID

        Returns:
            直播间信息字典

        Raises:
            ApiClientError: API 调用失败时抛出
        """
        params = {'room_id': room_id}
        headers = DefaultHeaders.BASE_HEADERS.copy()

        try:
            response = await self._get_request(
                ApiEndpoints.LIVE_ROOM_INFO,
                RequestType.GET,
                params,
                headers
            )
            data = response.json()
            if data.get("code") != 0:
                raise ApiClientError(data.get("message", "未知 API 错误"))
            return data["data"]
        except Exception as e:
            if isinstance(e, ApiClientError):
                raise
            raise ApiClientError(f"获取直播间信息失败: {e}")
    
    async def get_live_room_guard_tab(self, roomid: int, ruid: int, page: int, page_size: int = 30, sort: int = 0) -> Dict[str, Any]:
        """
        获取直播间大航海成员列表

        Args:
            roomid: 直播间 ID
            ruid: 主播 UID
            page: 页码
            page_size: 每页数量
            sort: 排序方式

        Returns:
            大航海成员信息字典

        Raises:
            ApiClientError: API 调用失败时抛出
        """
        params = {
            "roomid": roomid,
            "ruid": ruid,
            "page": page,
            "page_size": page_size,
            "typ": sort,
        }
        headers = DefaultHeaders.BASE_HEADERS.copy()

        try:
            response = await self._get_request(
                ApiEndpoints.LIVE_ROOM_GUARD_TAB,
                RequestType.GET,
                params,
                headers
            )
            data = response.json()
            if data.get("code") != 0:
                raise ApiClientError(data.get("message", "未知 API 错误"))
            return data["data"]
        except Exception as e:
            if isinstance(e, ApiClientError):
                raise
            raise ApiClientError(f"获取大航海成员失败: {e}")

    
    async def get_live_room_fans_members_rank(self, ruid: int, page: int, page_size: int = 30, rank_type: int = 1) -> Dict[str, Any]:
        """
        获取直播间粉丝团成员排行

        Args:
            ruid: 主播 UID
            page: 页码
            page_size: 每页数量
            rank_type: 排行类型

        Returns:
            粉丝团成员排行信息字典

        Raises:
            ApiClientError: API 调用失败时抛出
        """
        params = {
            "ruid": ruid,
            "page": page,
            "page_size": page_size,
            "rank_type": rank_type,
            "ts": int(time.time() * 1000),  # 13 位时间戳
        }
        headers = DefaultHeaders.BASE_HEADERS.copy()

        try:
            response = await self._get_request(
                ApiEndpoints.LIVE_ROOM_FANS_MEMBERS_RANK,
                RequestType.GET,
                params,
                headers
            )
            data = response.json()
            if data.get("code") != 0:
                raise ApiClientError(data.get("message", "未知 API 错误"))
            return data["data"]
        except Exception as e:
            if isinstance(e, ApiClientError):
                raise
            raise ApiClientError(f"获取粉丝团成员排行失败: {e}")

    async def get_live_room_online_gold_rank(self, room_id: int, ruid: int, page: int, page_size: int = 50) -> Dict[str, Any]:
        """
        获取直播间在线金瓜子排行

        Args:
            room_id: 直播间 ID
            ruid: 主播 UID
            page: 页码
            page_size: 每页数量

        Returns:
            在线金瓜子排行信息字典

        Raises:
            ApiClientError: API 调用失败时抛出
        """
        params = {
            "roomId": room_id,
            "ruid": ruid,
            "page": page,
            "pageSize": page_size,
        }
        headers = DefaultHeaders.BASE_HEADERS.copy()

        try:
            response = await self._get_request(
                ApiEndpoints.LIVE_ROOM_ONLINE_GOLD_RANK,
                RequestType.GET,
                params,
                headers
            )
            data = response.json()
            if data.get("code") != 0:
                raise ApiClientError(data.get("message", "未知 API 错误"))
            return data["data"]
        except Exception as e:
            if isinstance(e, ApiClientError):
                raise
            raise ApiClientError(f"获取在线金瓜子排行失败: {e}")

    async def get_live_room_danmu(self, room_id: int) -> Dict[str, Any]:
        """
        获取直播间弹幕信息

        Args:
            room_id: 直播间 ID

        Returns:
            弹幕信息字典

        Raises:
            ApiClientError: API 调用失败时抛出
        """
        params = {'roomid': room_id}
        headers = DefaultHeaders.LIVE_HEADERS.copy()
        headers["Referer"] = f"https://live.bilibili.com/{room_id}"

        try:
            response = await self._get_request(
                ApiEndpoints.LIVE_ROOM_DANMU,
                RequestType.GET,
                params,
                headers
            )
            data = response.json()
            if data.get("code") != 0:
                raise ApiClientError(data.get("message", "未知 API 错误"))
            return data["data"]
        except Exception as e:
            if isinstance(e, ApiClientError):
                raise
            raise ApiClientError(f"获取弹幕信息失败: {e}")

    def close(self):
        """关闭 Session 连接"""
        if hasattr(self, 'session'):
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

api = ApiClient()

async def main():
    """
    测试 API 客户端功能
    """
    

    try:
        with api:
            # 测试获取直播间信息
            print("=== 获取直播间信息 ===")
            room_info = await api.get_live_room_info(32444461)
            print(f"直播间标题: {room_info.get('title', 'N/A')}")
            print(f"直播状态: {bool(room_info.get('live_status', 'N/A'))}")
            print(f"人气值: {room_info.get('online', 'N/A')}")

            # 获取主播 UID 用于其他 API 调用
            ruid = room_info.get('uid')
            print(ruid)
            if ruid:
                print(f"\n=== 获取大航海成员 ===")
                guard_info = await api.get_live_room_guard_tab(32444461, ruid, 1)
                print(f"大航海成员数量: {sum(1 for item in guard_info['list'] + guard_info['top3'] if item.get('uinfo', {}).get('medal', {}).get('guard_level', 0) == 3)}")

                print(f"\n=== 获取粉丝团排行 ===")
                fans_rank = await api.get_live_room_fans_members_rank(ruid, 1)
                print(f"粉丝团成员数量: {len(fans_rank['item'])}")

            print(f"\n=== 获取弹幕信息 ===")
            danmu_info = await api.get_live_room_danmu(32444461)
            print(f"弹幕数量: {len(danmu_info.get('data', []))}")

    except ApiClientError as e:
        print(f"API 错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())