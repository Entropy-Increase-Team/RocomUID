import json
import httpx
import msgspec
from typing import Dict, Any, Union, Literal, Optional
from .models import UserInfo, PetList

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

    async def _post(self, req_path: str, req_type: str, authorization: str, payload: Dict[str, Any]) -> httpx.Response:
        """
        内部通用 POST 方法
        """
        data = {
            "data": json.dumps({
                **payload,
                "req_path": req_path,
                "req_type": req_type,
                "act_id": self.act_id,
                "area_id": 2,
                "plat_id": 1,
                "biz_code": "rocom",
                "server_type": 1,
                "app_name": "102802421"
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
    
    async def get_rocom_pet_list(
        self,
        token: str,
        baseid: str = '',
        openid: str = '',
        account_type: str = 'qq',
    ):
        """
        获取游戏信息接口
        """
        payload = {
            "account_type": account_type,
            "openid": openid,
            "req_param":
            {
                "page":1,
                "pageSize":40,
                "searchKeyword":"",
                "manual":False,
                "sort":[
                    {
                        "field":"Count",
                        "order":"desc"
                    }
                ],
                "baseid":int(baseid) if baseid != "" else ""
            }
        }

        result = await self._post("/api/pet/list", 'POST', token, payload)
        data = result.json()
        # if isinstance(data, Dict):
            # data = msgspec.convert(data["data"], type=UserInfo)
        return data
    
    async def get_rocom_pet_list_star(
        self,
        token: str,
        baseid: str = '',
        openid: str = '',
        account_type: str = 'qq',
    ) -> Union[PetList, int]:
        """
        获取游戏信息接口
        """
        payload = {
            "account_type": account_type,
            "openid": openid,
            "req_param":
            {
                "page":1,
                "pageSize":80,
                "searchKeyword":"",
                "manual":False,
                "sort":[
                    {
                        "field":"Count",
                        "order":"desc"
                    }
                ],
                "mutationFilter":[8,1,9],
                "baseid":""
            }
        }

        result = await self._post("/api/pet/list", 'POST', token, payload)
        data = result.json()
        if isinstance(data["data"], Dict):
            data_9 = []
            data_8 = []
            data_1 = []
            for item in data["data"]["list"]:
                if item["PetMutation"] == 9:
                    data_9.append(item)
                if item["PetMutation"] == 8:
                    data_8.append(item)
                if item["PetMutation"] == 1:
                    data_1.append(item)
            pet_list = []
            if len(data_9) > 0:
                for item9 in data_9:
                    pet_list.append(item9)
            if len(data_1) > 0:
                for item1 in data_1:
                    pet_list.append(item1)
            if len(data_8) > 0:
                for item8 in data_8:
                    pet_list.append(item8)
            data["data"]["list"] = pet_list
            data = msgspec.convert(data["data"], type=PetList)
        else:
            data = 0
        return data
    
    async def get_user_info(
        self,
        token: str,
        openid: str = '',
        account_type: str = 'qq',
    ) -> Union[UserInfo, int]:
        """
        获取游戏信息接口
        """
        payload = {
            "account_type": account_type,
            "openid": openid,
        }

        result = await self._post("/api/user/gameInfo", 'GET', token, payload)
        data = result.json()
        if isinstance(data["data"], Dict):
            data = msgspec.convert(data["data"], type=UserInfo)
        else:
            data = 0
        return data

rocom_api = RocomApi()