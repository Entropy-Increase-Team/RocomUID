import json
import httpx
import msgspec
import time
from gsuid_core.logger import logger
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
    base_url = "https://wegame.shallow.ink"
    
    def __init__(self, wegame_api_key: str = RC_CONFIG.get_config("RC_wegame_key").data, timeout: float = 15.0):
        """
        初始化客户端
        :param authorization: QQ 授权 token (Bearer JWT)
        :param act_id: 活动 ID
        """
        self.wegame_api_key = wegame_api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self.last_error_message: str = ""
    
    def _clear_last_error(self) -> None:
        self.last_error_message = ""
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    def _rocom_headers(self, fw_token: str) -> Dict[str, str]:
        """游戏数据查询接口的请求头 (scope=game:rocom)"""
        headers = {
            "X-Framework-Token": fw_token
        }
        if self.wegame_api_key:
            headers["X-API-Key"] = self.wegame_api_key
        return headers
    
    def _wegame_headers(
        self, fw_token: str = "", user_identifier: str = ""
    ) -> Dict[str, str]:
        """登录/账号管理接口的请求头 (scope=wegame)"""
        headers = {}
        if self.wegame_api_key:
            headers["X-API-Key"] = self.wegame_api_key
        
        if fw_token:
            headers["X-Framework-Token"] = fw_token
        if user_identifier:
            headers["X-User-Identifier"] = self._sanitize_uid(user_identifier)
        return headers
    
    async def _get(
        self, path: str, headers: Dict[str, str], params: Optional[Dict] = None
    ) -> Optional[Dict]:
        try:
            self._clear_last_error()
            client = await self._get_client()
            resp = await client.get(
                f"{self.base_url}{path}", headers=headers, params=params
            )
            # 检查响应状态码
            if resp.status_code != 200:
                logger.warning(f"[Rocom API] {path} HTTP 错误: {resp.status_code}")
                return None
            
            # 检查响应内容是否为空
            if not resp.text or not resp.text.strip():
                logger.warning(f"[Rocom API] {path} 响应为空")
                return None
            
            # 安全解析 JSON
            try:
                data = resp.json()
            except Exception as json_err:
                logger.warning(f"[Rocom API] {path} JSON 解析失败: {json_err}, 响应内容: {resp.text[:200]}")
                return None
            
            if data.get("code") != 0:
                logger.warning(f"[Rocom API] {path} 错误: {data.get('message', '未知')}")
                return None
            return data.get("data", {})
        except httpx.TimeoutException:
            logger.error(f"[Rocom API] GET {path} 请求超时")
            return None
        except httpx.RequestError as e:
            logger.error(f"[Rocom API] GET {path} 请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"[Rocom API] GET {path} 异常: {e}")
            return None
    
    async def _post(
        self,
        path: str,
        headers: Dict[str, str],
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Optional[Dict]:
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.base_url}{path}",
                headers=headers,
                json=json_data,
                params=params,
            )
            print(resp)
            # 检查响应状态码
            if resp.status_code != 200:
                logger.warning(f"[Rocom API] {path} HTTP 错误: {resp.status_code}")
                return None
            
            # 检查响应内容是否为空
            if not resp.text or not resp.text.strip():
                logger.warning(f"[Rocom API] {path} 响应为空")
                return None
            
            # 安全解析 JSON
            try:
                data = resp.json()
            except Exception as json_err:
                logger.warning(f"[Rocom API] {path} JSON 解析失败: {json_err}, 响应内容: {resp.text[:200]}")
                return None
            
            if data.get("code") != 0:
                logger.warning(f"[Rocom API] {path} 错误: {data.get('message', '未知')}")
                return None
            return data.get("data", {})
        except httpx.TimeoutException:
            logger.error(f"[Rocom API] POST {path} 请求超时")
            return None
        except httpx.RequestError as e:
            logger.error(f"[Rocom API] POST {path} 请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"[Rocom API] POST {path} 异常: {e}")
            return None
    
    def _sanitize_uid(self, uid: str) -> str:
        """参考 Go 端的 SanitizeStrictInput 逻辑"""
        import re
        if not uid: return ""
        uid = str(uid).strip()
        # 注意：服务器端 Go 逻辑允许字母、数字以及中日韩字符。
        cleaned = re.sub(r'[^a-zA-Z0-9_\- \u4e00-\u9fa5]', '', uid)
        return cleaned.strip()
    
    # ─── 登录相关 ───
    
    async def wechat_qr_login(
        self, user_identifier: str = ""
    ) -> Optional[Dict]:
        """发起微信扫码登录，返回 frameworkToken + qr_image (URL)"""
        params = {"client_type": "bot", "client_id": "gscore"}
        if user_identifier:
            params["user_identifier"] = self._sanitize_uid(user_identifier)
        return await self._get(
            "/api/v1/login/wegame/wechat/qr",
            self._wegame_headers(user_identifier=user_identifier),
            params=params,
        )
    
    async def wechat_qr_status(
        self, fw_token: str, user_identifier: str = ""
    ) -> Optional[Dict]:
        """轮询微信扫码状态"""
        params = {}
        if user_identifier:
            params["user_identifier"] = self._sanitize_uid(user_identifier)
        return await self._get(
            "/api/v1/login/wegame/wechat/status",
            self._wegame_headers(
                fw_token, user_identifier=user_identifier
            ),
            params=params,
        )
    
    async def get_qq_token(
        self, fw_token: str, user_identifier: str = ""
    ) -> Optional[Dict]:
        """查询 QQ 扫码凭证"""
        user_identifier = self._sanitize_uid(user_identifier)
        params = {}
        if user_identifier:
            params["user_identifier"] = user_identifier
        return await self._get(
            "/api/v1/login/wegame/token",
            self._wegame_headers(fw_token, user_identifier),
            params=params,
        )

    async def get_wechat_token(
        self, fw_token: str, user_identifier: str = ""
    ) -> Optional[Dict]:
        """查询微信扫码凭证"""
        user_identifier = self._sanitize_uid(user_identifier)
        params = {}
        if user_identifier:
            params["user_identifier"] = user_identifier
        return await self._get(
            "/api/v1/login/wegame/wechat/token",
            self._wegame_headers(fw_token, user_identifier),
            params=params,
        )
    
    async def qq_qr_login(self, user_identifier: str = "") -> Optional[Dict]:
        """发起 QQ 扫码登录，返回 frameworkToken + qr_image (base64)"""
        params = {"client_type": "bot", "client_id": "gscore"}
        if user_identifier:
            params["user_identifier"] = self._sanitize_uid(user_identifier)
        return await self._get(
            "/api/v1/login/wegame/qr",
            self._wegame_headers(user_identifier=user_identifier),
            params=params,
        )
    
    async def qq_qr_status(
        self, fw_token: str, user_identifier: str = ""
    ) -> Optional[Dict]:
        """轮询 QQ 扫码状态"""
        params = {}
        if user_identifier:
            params["user_identifier"] = self._sanitize_uid(user_identifier)
        return await self._get(
            "/api/v1/login/wegame/status",
            self._wegame_headers(
                fw_token, user_identifier=user_identifier
            ),
            params=params,
        )
    
    async def create_binding(
        self, fw_token: str, user_identifier: str
    ) -> Optional[Dict]:
        """将匿名创建的 frameworkToken 通过 API Key 绑定给用户，从而获得持久授权"""
        user_identifier = self._sanitize_uid(user_identifier)
        payload = {
            "framework_token": fw_token,
            "user_identifier": user_identifier,
            "client_type": "bot",
            "client_id": "gscore",
        }
        return await self._post(
            "/api/v1/user/bindings",
            # 这里必须带 API Key
            self._wegame_headers(user_identifier=user_identifier),
            json_data=payload,
        )
    
    # ─── 洛克王国游戏数据 ───

    async def get_role(
        self, fw_token: str, account_type: int | None = None
    ) -> Optional[Dict]:
        """角色资料"""
        params = {}
        if account_type:
            params["account_type"] = account_type
        return await self._get(
            "/api/v1/games/rocom/profile/role",
            self._rocom_headers(fw_token),
            params=params,
        )

    async def get_evaluation(
        self, fw_token: str, account_type: int | None = None
    ) -> Optional[Dict]:
        """AI 维度评价"""
        params = {}
        if account_type:
            params["account_type"] = account_type
        return await self._get(
            "/api/v1/games/rocom/profile/evaluation",
            self._rocom_headers(fw_token),
            params=params,
        )

    async def get_pet_summary(
        self, fw_token: str, account_type: int | None = None
    ) -> Optional[Dict]:
        """精灵摘要"""
        params = {}
        if account_type:
            params["account_type"] = account_type
        return await self._get(
            "/api/v1/games/rocom/profile/pet-summary",
            self._rocom_headers(fw_token),
            params=params,
        )

    async def get_collection(
        self, fw_token: str, account_type: int | None = None
    ) -> Optional[Dict]:
        """收藏数据"""
        params = {}
        if account_type:
            params["account_type"] = account_type
        return await self._get(
            "/api/v1/games/rocom/profile/collection",
            self._rocom_headers(fw_token),
            params=params,
        )

    async def get_battle_overview(
        self, fw_token: str, account_type: int | None = None
    ) -> Optional[Dict]:
        """对战总览"""
        params = {}
        if account_type:
            params["account_type"] = account_type
        return await self._get(
            "/api/v1/games/rocom/profile/battle-overview",
            self._rocom_headers(fw_token),
            params=params,
        )

    async def get_battle_list(
        self,
        fw_token: str,
        page_size: int = 4,
        after_time: str = "",
        zone: int | None = None,
    ) -> Optional[Dict]:
        """对战记录列表"""
        params: Dict[str, Any] = {"page_size": page_size}
        if after_time:
            params["after_time"] = after_time
        if zone is not None:
            params["zone"] = zone
        return await self._get(
            "/api/v1/games/rocom/battle/list",
            self._rocom_headers(fw_token),
            params=params,
        )
    
    async def get_pets(
        self,
        fw_token: str,
        pet_subset: int = 0,
        page_no: int = 1,
        page_size: int = 10,
        zone: int | None = None,
    ) -> Optional[Dict]:
        """精灵列表"""
        params = {
            "pet_subset": pet_subset,
            "page_no": page_no,
            "page_size": page_size,
        }
        if zone is not None:
            params["zone"] = zone
        return await self._get(
            "/api/v1/games/rocom/battle/pets",
            self._rocom_headers(fw_token),
            params,
        )
    
    async def get_merchant_info_cs(self):
        params = {"shop_id": 3019}
        nowtime = time.time() * 1000
        data = await self._post(
            "/api/v1/games/rocom/ingame/merchant/info",
            self._wegame_headers(),
            json_data=params,
        )
        print(data)
        return data
    
    async def get_merchant_info(self, refresh: bool = False):
        """
        获取游戏信息接口
        """
        params = {"refresh": "true" if refresh else "false"}
        nowtime = time.time() * 1000
        data = await self._get(
            "/api/v1/games/rocom/merchant/info",
            self._wegame_headers(),
            params=params,
        )
        if data is not None:
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
            # print(props)
            for item in props:
                if not await is_active(item):
                    continue
                if item.get('start_time') is not None:
                    start_time = time.strftime("%m月%d日 %H:%M", time.localtime(int(item['start_time'])/1000))
                else:
                    start_time = time.strftime("%m月%d日", time.localtime(int(nowtime/1000)))
                    start_time = f"{start_time} 08:00"
                if item.get('end_time') is not None:
                    end_time = time.strftime("%H:%M", time.localtime(int(item['end_time'])/1000))
                else:
                    end_time = "23:59"
                products.append(
                    {
                        "name": item.get("name", "未知商品"),
                        "image": item.get("icon_url", None),
                        "starttime": start_time,
                        "endtime": end_time,
                    }
                )
            
            return products
        else:
            return []

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
    
rocom_api = RocomApi()
wegame_api = WegameApi()