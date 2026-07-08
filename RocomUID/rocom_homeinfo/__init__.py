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
from ..utils.to_data import (
    api_to_dict_home_info,
    api_to_dict_pet_info,
    convert_pet_info_map,
)
from ..rocom_petinfo.draw_info_image import draw_pet_home
from .draw_info_image import draw_home_info
from .draw_home_image import draw_home_image
from .draw_garden_image import draw_garden_image

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
    local_home_data['finished_at'] = int(home_data['meta']['finished_at'])
    return msgspec.convert(local_home_data, type=HomeInfo)


async def get_my_home_info(uid: str):
    if is_config_enabled('RC_home_cache_enable'):
        local_home_data = load_home_cache(uid)
        if local_home_data is not None:
            return local_home_data

    return await api_to_dict_home_info(uid, PLAYER_PATH)


def load_pet_cache(uid: str):
    pet_info_path = PLAYER_PATH / uid / 'pet_info.json'
    if not pet_info_path.exists():
        return None

    cache_minutes = max(get_config_float('RC_home_cache_minutes', 5), 0)
    if time.time() - pet_info_path.stat().st_mtime > cache_minutes * 60:
        return None

    with Path.open(pet_info_path, encoding='utf-8') as f:
        pet_data = json.load(f)

    return (
        convert_pet_info_map(pet_data['pets_list']),
        pet_data.get('home_name') or '未命名家园',
    )


async def get_my_pet_info_data(uid: str):
    if is_config_enabled('RC_home_cache_enable'):
        local_pet_data = load_pet_cache(uid)
        if local_pet_data is not None:
            return local_pet_data

    return await api_to_dict_pet_info(uid, PLAYER_PATH, include_home_name=True)


async def _resolve_uid(bot: Bot, ev: Event, text=None):
    """解析 UID：消息参数优先，否则取绑定。失败已回错误消息并返回 None。"""
    args = (ev.text if text is None else text).split()
    if len(args) < 1:
        uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
        if not uid:
            await bot.send('你还没有绑定RC_UID哦!')
            return None
    else:
        uid = args[0]
    if uid and not uid.isdigit():
        await bot.send('请输入正确的UID格式!')
        return None
    return uid


def is_new_home_render_style() -> bool:
    return RC_CONFIG.get_config('RC_garden_render_style').data == '新版'


async def _draw_garden(ev: Event, uid: str, home_info) -> bytes:
    """菜园(种植)出图：按家园/菜园渲染样式选择渲染样式。"""
    if is_new_home_render_style():
        return await draw_garden_image(ev, uid, home_info, False, True)
    return await draw_home_info(ev, uid, home_info, False, True)


@sv_home_info.on_command(('家园', '菜园'))
async def get_my_home_info_wegame(bot: Bot, ev: Event):
    text = ev.text.strip()
    is_pet_home = ev.command == '家园' and text.startswith('精灵')
    is_garden = '菜园' in ev.command
    info_name = '家园精灵' if is_pet_home else '菜园' if is_garden else '家园'

    uid = await _resolve_uid(bot, ev, text[2:].strip() if is_pet_home else None)
    if uid is None:
        return
    await bot.send(f'正在获取[UID]{uid}的{info_name}信息，请稍后')

    if is_pet_home:
        pet_result = await get_my_pet_info_data(uid)
        if isinstance(pet_result, str):
            return await bot.send(pet_result)
        pet_data, home_name = pet_result
        if isinstance(pet_data, str):
            return await bot.send(pet_data)
        if len(pet_data.keys()) == 0:
            return await bot.send('您的家园中没有可显示的精灵数据。')
        return await bot.send(await draw_pet_home(uid, pet_data, home_name))

    home_info = await get_my_home_info(uid)   # 单次获取，两张图共用
    if isinstance(home_info, str):
        return await bot.send(home_info)

    if is_garden:                              # 菜园 → 一张种植图
        return await bot.send(await _draw_garden(ev, uid, home_info))

    if is_new_home_render_style():
        # 家园 → 精灵图；未开「家园隐藏菜园」时再追发一张菜园图
        await bot.send(await draw_home_image(ev, uid, home_info, True, False))
        if not is_config_enabled('RC_home_separate_garden'):
            await bot.send(await _draw_garden(ev, uid, home_info))
        return

    # 旧版家园模板：按「家园隐藏菜园」决定是否合并显示菜园信息
    await bot.send(
        await draw_home_info(
            ev,
            uid,
            home_info,
            True,
            not is_config_enabled('RC_home_separate_garden'),
        )
    )
