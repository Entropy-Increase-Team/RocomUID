"""
HTTP请求客户端
封装公告列表、公告详情、验证码获取等接口调用
"""

import requests
import random
from typing import Dict, Any, Optional


class APIClient:
    """API请求客户端 - 封装所有HTTP接口调用"""

    # 接口URL常量
    ANNOUNCEMENT_LIST_URL = "https://morefun.game.qq.com/rocom/E80EH8LJ/petsetList"
    ANNOUNCEMENT_LIST_URL_LEGACY = "https://morefun.game.qq.com/act/v1/api/v1/gateway"
    ANNOUNCEMENT_DETAIL_URL = "https://morefun.game.qq.com/rocom/E80EH8LJ/threadDetail"
    REDEEM_URL = "https://comm.ams.game.qq.com/ide/"
    CAPTCHA_URL = "https://ssl.captcha.qq.com/getimage"

    def __init__(self, use_miniapp_auth: bool, miniapp_auth: str, miniapp_data: str, web_cookie: str, timeout: int = 5,
                 use_proxy: bool = False, proxy_host: str = "", proxy_port: int = 0):
        """
        初始化API客户端

        Args:
            use_miniapp_auth: 是否使用小程序验证
            miniapp_auth: 小程序Authorization token
            miniapp_data: 小程序请求data参数(JSON字符串)
            web_cookie: 网页端完整Cookie字符串
            timeout: 请求超时时间(秒)
            use_proxy: 是否使用代理(仅用于网页端请求)
            proxy_host: 代理主机地址
            proxy_port: 代理端口
        """
        self.use_miniapp_auth = use_miniapp_auth
        self.miniapp_auth = miniapp_auth
        self.miniapp_data = miniapp_data
        self.web_cookie = web_cookie
        self.timeout = timeout

        # 构建代理配置(仅用于网页端请求)
        self.proxies = None
        if use_proxy and proxy_host and proxy_port:
            proxy_url = f"http://{proxy_host}:{proxy_port}"
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }

        # 生成随机设备指纹(每个Cookie独立,但两个接口共用)
        self.device_fingerprint = self._generate_device_fingerprint()

        # 用于维护Cookie的session对象
        self.session = requests.Session()
        # 将初始Cookie设置到session中
        self._update_session_cookies(web_cookie)

    def _generate_device_fingerprint(self) -> Dict[str, Any]:
        """
        生成随机设备指纹

        Returns:
            设备指纹字典,包含UA、平台、浏览器版本等信息
        """
        # 随机Chrome版本 (120-141之间)
        chrome_major = random.randint(120, 141)
        chrome_minor = random.randint(0, 9)
        chrome_build = random.randint(5000, 6000)
        chrome_patch = random.randint(0, 200)
        chrome_version = f"{chrome_major}.{chrome_minor}.{chrome_build}.{chrome_patch}"

        # 随机平台 (Windows占70%, Mac占20%, Linux占10%)
        platform_choice = random.choices(
            ['Windows', 'macOS', 'Linux'],
            weights=[70, 20, 10],
            k=1
        )[0]

        # 根据平台生成对应的UA字符串
        if platform_choice == 'Windows':
            platform = 'Windows'
            os_version = random.choice(['10.0', '11.0'])
            platform_str = f'Windows NT {os_version}; Win64; x64'
            sec_ch_platform = '"Windows"'
        elif platform_choice == 'macOS':
            platform = 'macOS'
            mac_version = random.choice(['10_15_7', '11_0_0', '12_0_0', '13_0_0'])
            platform_str = f'Macintosh; Intel Mac OS X {mac_version}'
            sec_ch_platform = '"macOS"'
        else:  # Linux
            platform = 'Linux'
            platform_str = 'X11; Linux x86_64'
            sec_ch_platform = '"Linux"'

        # 随机是否移动设备 (99%桌面, 1%移动)
        is_mobile = random.choices([True, False], weights=[1, 99], k=1)[0]
        sec_ch_mobile = '?1' if is_mobile else '?0'

        # 构建User-Agent
        user_agent = f'Mozilla/5.0 ({platform_str}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36'

        # 构建sec-ch-ua (Chromium Client Hints)
        # 格式: "Google Chrome";v="主版本", "Not?A_Brand";v="随机", "Chromium";v="主版本"
        not_brand_version = random.randint(8, 99)
        sec_ch_ua = f'"Google Chrome";v="{chrome_major}", "Not?A_Brand";v="{not_brand_version}", "Chromium";v="{chrome_major}"'

        return {
            'user_agent': user_agent,
            'sec_ch_ua': sec_ch_ua,
            'sec_ch_ua_mobile': sec_ch_mobile,
            'sec_ch_ua_platform': sec_ch_platform,
            'platform': platform,
            'chrome_version': chrome_version,
            'chrome_major': chrome_major
        }

    def _update_session_cookies(self, cookie_string: str):
        """
        更新session的Cookie

        Args:
            cookie_string: Cookie字符串
        """
        # 解析Cookie字符串并添加到session
        if cookie_string:
            for item in cookie_string.split(';'):
                item = item.strip()
                if '=' in item:
                    key, value = item.split('=', 1)
                    self.session.cookies.set(key.strip(), value.strip())

    def _get_current_cookie_string(self) -> str:
        """
        从session中获取当前完整的Cookie字符串

        Returns:
            Cookie字符串
        """
        return '; '.join([f"{key}={value}" for key, value in self.session.cookies.items()])

    def _get_announcement_list_no_auth(self) -> Optional[Dict[str, Any]]:
        """
        获取公告列表（新接口，不需要验证）

        Returns:
            成功返回公告列表数据,失败返回None
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541022) XWEB/16467',
            'Content-Type': 'application/json',
            'xweb_xhr': '1',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://servicewechat.com/wx9a5bc2cdcaff1af1/8/page-frame.html',
            'accept-language': 'zh-CN,zh;q=0.9',
            'priority': 'u=1, i'
        }

        data = {
            "req_param": {
                "order": "vDesc"
            }
        }
        
        # data = {
            # "data": {
                # "account_type": "qq",
                # "openid": "54150F6DC02E03F40E21E9AC4B495CAB",
                # "area_id": 2,
                # "plat_id": 1,
                # "biz_code": "rocom",
                # "server_type": 1,
                # "app_name": "102802421",
                # "req_path": "/api/user/gameInfo",
                # "req_type": "GET",
            # }
        # }
        try:
            response = requests.post(
                f"{self.ANNOUNCEMENT_LIST_URL}?X-Mcube-Act-Id=E80EH8LJ",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            if result.get('code') == 0:
                return result.get('data', {})
            else:
                error_msg = result.get('msg', '')
                print(f"获取公告列表失败: {error_msg}")
                return None

        except requests.RequestException as e:
            print(f"请求公告列表异常: {e}")
            return None
        except Exception as e:
            print(f"获取公告列表发生未知错误: {e}")
            return None

    def get_announcement_detail(self, thread_id: int) -> Optional[Dict[str, Any]]:
        """
        获取公告详情

        Args:
            thread_id: 公告ID

        Returns:
            成功返回公告详情数据,失败返回None
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541022) XWEB/16467',
            'xweb_xhr': '1',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://servicewechat.com/wx9a5bc2cdcaff1af1/7/page-frame.html',
            'accept-language': 'zh-CN,zh;q=0.9',
            'priority': 'u=1, i',
            'Content-Type': 'application/json'
        }

        data = {
            "req_param": {
                "threadId": thread_id
            }
        }

        try:
            response = requests.post(
                f"{self.ANNOUNCEMENT_DETAIL_URL}?X-Mcube-Act-Id=E80EH8LJ",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            if result.get('code') == 0:
                return result.get('data', {})
            else:
                print(f"获取公告详情失败: {result.get('msg')}")
                return None

        except requests.RequestException as e:
            print(f"请求公告详情异常: {e}")
            return None
        except Exception as e:
            print(f"获取公告详情发生未知错误: {e}")
            return None

    def get_captcha_image(self, aid: str = "210001040.2833479040128887") -> Optional[bytes]:
        """
        获取验证码图片,并自动更新Cookie中的verifysession

        Args:
            aid: 验证码aid参数

        Returns:
            成功返回图片二进制数据,失败返回None
        """
        # 使用随机设备指纹
        fp = self.device_fingerprint
        headers = {
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://rocom.qq.com/',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': fp['user_agent']
        }

        try:
            # 清除旧的verifysession,避免多个同名Cookie冲突
            if 'verifysession' in self.session.cookies:
                # 删除所有verifysession Cookie
                for cookie in list(self.session.cookies):
                    if cookie.name == 'verifysession':
                        self.session.cookies.clear(cookie.domain, cookie.path, cookie.name)
                print("清除旧的verifysession")

            # 使用session发送请求,自动维护Cookie
            response = self.session.get(
                f"{self.CAPTCHA_URL}?aid={aid}",
                headers=headers,
                timeout=self.timeout,
                proxies=self.proxies  # 使用代理(如果配置了)
            )
            response.raise_for_status()

            # 检查是否收到了新的verifysession
            if 'verifysession' in self.session.cookies:
                verify_session = self.session.cookies.get('verifysession')
                print(f"✓ 获取新verifysession: {verify_session[:20]}...")

            return response.content

        except requests.RequestException as e:
            print(f"请求验证码图片异常: {e}")
            return None
        except Exception as e:
            print(f"获取验证码图片发生未知错误: {e}")
            return None

    