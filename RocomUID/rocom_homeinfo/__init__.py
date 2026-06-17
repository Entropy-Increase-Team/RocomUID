import json
import time
from pathlib import Path
from typing import Any

import msgspec
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..rocom_config.rocom_config import RC_CONFIG
from ..utils.database.model import RocomUser
from ..utils.models import HomeInfo
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from ..utils.to_data import api_to_dict_home_info
from .draw_info_image import draw_home_info

sv_home_info = SV('rc家园事件', priority=5)


def is_config_enabled(config_key: str) -> bool:
    config_value = RC_CONFIG.get_config(config_key).data
    if isinstance(config_value, bool):
        return config_value
    return str(config_value).lower() in ['true', '1', 'yes', 'on', '开启']


def get_config_float(config_key: str, default: float) -> float:
    try:
        value = RC_CONFIG.get_config(config_key).data
        return float(value)
    except (TypeError, ValueError):
        return default


def load_home_cache(uid: str) -> Any:
    home_info_path = PLAYER_PATH / uid / 'home_info.json'
    if not home_info_path.exists():
        return None

    cache_minutes = max(get_config_float('RC_home_cache_minutes', 5), 0)
    with Path.open(home_info_path, encoding='utf-8') as f:
        home_data = json.load(f)

    created_at = float(home_data.get('meta', {}).get('created_at', 0))
    if time.time() - created_at > cache_minutes * 60:
        return None

    local_home_data = home_data['home_info']
    local_home_data['finished_at'] = home_data['meta']['finished_at']
    return msgspec.convert(local_home_data, type=HomeInfo)


async def get_my_home_info(uid: str):
    if is_config_enabled('RC_home_cache_enable'):
        local_home_data = load_home_cache(uid)
        if local_home_data is not None:
            return local_home_data

    return await api_to_dict_home_info(uid, PLAYER_PATH)


@sv_home_info.on_command(('家园', 'home'))
async def get_my_home_info_wegame(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
        if not uid:
            return await bot.send('你还没有绑定RC_UID哦!')
    else:
        uid = args[0]
    if uid and not uid.isdigit():
        return await bot.send('请输入正确的UID格式!')
    await bot.send(f'正在获取[UID]{uid}的家园信息，请稍后')

    home_info = await get_my_home_info(uid)
    if isinstance(home_info, str):
        return await bot.send(home_info)
    im = await draw_home_info(ev, uid, home_info)
    await bot.send(im)
