import json
import httpx
import msgspec
import time
from typing import Dict, Any, Union, Literal, Optional
from .models import UserInfo, PetList
from ..rocom_config.rocom_config import RC_CONFIG
import uuid

app_info_list = {
    "qq": ["102802421", 2, 1],
    "qqmini": ["1112470186", 2, 1],
    "wx": ["wx9a5bc2cdcaff1af1", 1, 0],
    "wxmini": ["wx9a5bc2cdcaff1af1", 1, 0]
}

class WegameApi():
    BASE_URL = "https://wegame.shallow.ink/api/v1/games/rocom/"
    
    def __init__(self):
        """
        初始化客户端
        :param authorization: QQ 授权 token (Bearer JWT)
        :param act_id: 活动 ID
        """
        self.client = httpx.Client(timeout=10.0)  # 同步客户端
    
    async def _post(self, req_path: str, params: Dict[str, Any]) -> httpx.Response:
        wegame_api_key: str = RC_CONFIG.get_config("RC_wegame_key").data
        response = self.client.get(
            f"{self.BASE_URL}{req_path}",
            params=params,
            headers = {
                'X-API-Key': wegame_api_key,
            }
        )
        response.raise_for_status()
        return response
    
    async def get_merchant_info(self, refresh: bool = False):
        """
        获取游戏信息接口
        """
        params = {"refresh": "true" if refresh else "false"}
        nowtime = time.time() * 1000
        result = await self._post("merchant/info", params)
        data = result.json()
        activities = data['data'].get("merchantActivities")
        if activities is None:
            activities = data['data'].get("merchant_activities")
        activity = activities[0] if activities else {}
        props = activity.get("get_props", [])
        products = []
        
        async def is_active(item: Dict[str, Any]) -> bool:
            start_time = item.get("start_time")
            end_time = item.get("end_time")
            if start_time is None or end_time is None:
                return True
            try:
                return int(start_time) <= nowtime < int(end_time)
            except (TypeError, ValueError):
                return True
        
        for item in props:
            if not await is_active(item):
                continue
            products.append(
                {
                    "name": item.get("name", "未知商品"),
                    "image": item.get("icon_url", None),
                    "endtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(item['end_time'])/1000))
                }
            )
        
        return products

class Rocom_co_Api():
    BASE_URL = "https://env-00jxhb62nv6n.api-hz.cloudbasefunction.cn/functions/invokeFunction"
    
    def __init__(self, wegame_api_key: str = ""):
        #self.wegame_api_key = wegame_api_key
        self.client = httpx.Client(timeout=15.0)  # 同步客户端
    
    async def _post(self) -> httpx.Response:
        request_id = str(uuid.uuid4())
        raw_body = '''{"method":"getInitInfo","params":[null],"clientInfo":{"PLATFORM":"mp-weixin","OS":"windows","APPID":"__UNI__A807A48","DEVICEID":"17765814025078152981","scene":1256,"appName":"rcgd-m","appId":"__UNI__A807A48","appVersion":"1.0.25","appVersionCode":"1025","appLanguage":"zh-Hans","hostVersion":"4.1.8.104","hostName":"WeChat","uniPlatform":"mp-weixin","uniCompilerVersion":"4.87","uniRuntimeVersion":"4.87","deviceId":"17765814025078152981","deviceType":"phone","deviceBrand":"microsoft","deviceModel":"microsoft","osName":"windows","osVersion":"10","locale":"zh-Hans","LOCALE":"zh-Hans"}}'''
        response = self.client.post(
            f"{self.BASE_URL}",
            data=raw_body,
            headers = {
                "Host": "env-00jxhb62nv6n.api-hz.cloudbasefunction.cn",
                "Connection": "keep-alive",
                "Content-Length": "587",
                "x-to-function-name": "m-common-co",
                "x-request-id": request_id,
                "x-client-timestamp": "1776661512620",
                "Authorization": "HMAC-SHA256 Credential=Y8OQpKSpRYnjPAYB, SignedHeaders=x-client-timestamp;x-from-app-id;x-from-env-id;x-from-function-name;x-from-instance-id;x-to-env-id;x-to-function-name, Signature=0eab0e05fbad8ea2bb39570fea88e1fb87f26c4eb89ea736eb03e498d5823a2f",
                "x-from-env-id": "env-00jxhb62nv6n",
                "x-to-env-id": "env-00jxhb62nv6n",
                "xweb_xhr": "1",
                "x-from-app-id": "2021004147646503",
                "x-trace-id": request_id,
                "x-alipay-source": "client",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541868) XWEB/19459",
                "x-from-instance-id": "1776661512620",
                "x-from-function-name": "m-common-co",
                "Content-Type": "application/json",
                "x-alipay-callid": request_id,
                "Accept": "*/*",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://servicewechat.com/wxece8d6735c1455ce/61/page-frame.html",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9"
            }
        )
        response.raise_for_status()
        return response
    
    async def get_merchant_info(self):
        """
        获取游戏信息接口
        """
        nowtime = time.time() * 1000
        result = await self._post()
        data = result.json()
        #print(str(data))
        activities = data.get("merchantActivities")
        if activities is None:
            activities = data.get("merchant_activities")
        activity = activities[0] if activities else {}
        props = activity.get("get_props", [])
        products = []
        
        async def is_active(item: Dict[str, Any]) -> bool:
            start_time = item.get("start_time")
            end_time = item.get("end_time")
            if start_time is None or end_time is None:
                return True
            try:
                return int(start_time) <= nowtime < int(end_time)
            except (TypeError, ValueError):
                return True
        
        for item in props:
            if not await is_active(item):
                continue
            products.append(
                {
                    "name": item.get("name", "未知商品"),
                    "image": item.get("icon_url", None),
                    "endtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(item['end_time'])/1000))
                }
            )
        
        return products

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
                "biz_code": "rocom",
                "server_type": 1
            })
        }
        #print(str(data))
        response = self.client.post(
            self.BASE_URL,
            params={"X-Mcube-Act-Id": self.act_id},
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781 NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF XWEB/14181',
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": authorization,
                'xweb_xhr': '1',
                'sec-fetch-site': 'cross-site',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': 'https://servicewechat.com/wx9a5bc2cdcaff1af1/8/page-frame.html',
                'accept-language': 'zh-CN,zh;q=0.9',
                'priority': 'u=1, i'
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
            "app_name": app_info_list[account_type][0],
            "area_id": app_info_list[account_type][1],
            "plat_id": app_info_list[account_type][2],
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
            "app_name": app_info_list[account_type][0],
            "area_id": app_info_list[account_type][1],
            "plat_id": app_info_list[account_type][2],
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
                "mutationFilter":[1,8,9],
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
            "app_name": app_info_list[account_type][0],
            "area_id": app_info_list[account_type][1],
            "plat_id": app_info_list[account_type][2],
            "openid": openid,
        }

        result = await self._post("/api/user/gameInfo", 'GET', token, payload)
        data = result.json()
        if isinstance(data["data"], Dict):
            data = msgspec.convert(data["data"], type=UserInfo)
        else:
            data = int(data['code'])
        return data
    
    
cocom_co_api = Rocom_co_Api()
rocom_api = RocomApi()
wegame_api = WegameApi()