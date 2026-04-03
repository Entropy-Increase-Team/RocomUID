import json
import httpx
import msgspec
from typing import Dict, Any, Union, Literal, Optional
from .models import UserInfo

class RocomApi():
    BASE_URL = "https://morefun.game.qq.com/gw2/gateway/v1/"

    def __init__(self, act_id: str = "E80EH8LJ"):
        """
        初始化客户端
        :param authorization: QQ 授权 token (Bearer JWT)
        :param act_id: 活动 ID
        """
        self.act_id = act_id
        self.client = httpx.Client(timeout=10.0)  # 同步客户端

    async def _post(self, req_path: str, authorization: str, payload: Dict[str, Any]) -> httpx.Response:
        """
        内部通用 POST 方法
        """
        data = {
            "data": json.dumps({
                **payload,
                "req_path": req_path,
                "req_type": "GET",   # 固定 GET 类型
                "act_id": self.act_id
            })
        }

        response = self.client.post(
            self.BASE_URL,
            params={"X-Mcube-Act-Id": self.act_id},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": authorization
            },
            data=data
        )
        response.raise_for_status()
        return response

    async def get_game_info(
        self,
        token: str,
        openid: str = '',
        area_id: int = 2,
        plat_id: int = 1,
        biz_code: str = "rocom",
        server_type: int = 1,
        app_name: str = "102802421"
    ) -> Union[UserInfo, int]:
        """
        获取游戏信息接口
        """
        payload = {
            "account_type": "qq",
            "openid": openid,
            "area_id": area_id,
            "plat_id": plat_id,
            "biz_code": biz_code,
            "server_type": server_type,
            "app_name": app_name
        }

        result = await self._post("/api/user/gameInfo", token, payload)
        data = result.json()
        if isinstance(data, Dict):
            data = msgspec.convert(data["data"], type=UserInfo)
        return data

rocom_api = RocomApi()