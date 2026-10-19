import json
import time
import asyncio
from pathlib import Path
from typing import Any

import msgspec
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..rocom_config.rocom_config import RC_CONFIG
from ..utils.database.model import RocomUser, HOME_UID_MAX_COUNT, UID_MIN_LENGTH
from ..utils.error_reply import prefix as P
from ..utils.models import HomeInfo
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from ..utils.to_data import (
    api_to_dict_home_info,
    api_to_dict_pet_info,
    convert_pet_info_map,
)
from ..rocom_petinfo.draw_info_image import draw_pet_home, draw_pet_home_brief
from .egg import api_to_home_egg_text
from .draw_info_image import draw_home_info
from .draw_home_image import draw_home_image
from .draw_garden_image import draw_garden_image

sv_home_info = SV('rc家园事件', priority=5)

HOME_SHORTCUT_START = 2
HOME_SHORTCUT_END = HOME_SHORTCUT_START + HOME_UID_MAX_COUNT - 1


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
        pet_data.get('home_name') or '未命名家园',
        convert_pet_info_map(pet_data.get('pets_list', {})),
    )


async def get_my_pet_info_data(uid: str, include_skills: bool):
    if is_config_enabled('RC_home_cache_enable'):
        local_pet_data = load_pet_cache(uid)
        if local_pet_data is not None:
            return local_pet_data

    return await api_to_dict_pet_info(
        uid,
        PLAYER_PATH if include_skills and is_config_enabled('RC_home_cache_enable') else None,
        include_skills=include_skills,
    )

def get_bind_uid_prompt_msg() -> str:
    return (
        "你还没有绑定RC_UID哦!\n"
        f"请发送：{P}绑定uid123456\n"
    )


async def _resolve_uid(bot: Bot, ev: Event, text=None):
    """解析 UID：消息参数优先（支持 1 / 2..20 快捷编号），否则取默认绑定。"""
    args = (ev.text if text is None else text).split()
    if len(args) < 1:
        uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
        if not uid:
            await bot.send(get_bind_uid_prompt_msg())
            return None
        return str(uid)

    uid = args[0].strip()
    if uid.isdigit() and len(uid) >= UID_MIN_LENGTH:
        return uid
    if not uid.isdigit():
        await bot.send('请输入正确的UID格式!')
        return None

    shortcut_number = int(uid)
    if shortcut_number == 1:
        bind_uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
        if not bind_uid:
            await bot.send(get_bind_uid_prompt_msg())
            return None
        return str(bind_uid)
    if shortcut_number < HOME_SHORTCUT_START or shortcut_number > HOME_SHORTCUT_END:
        await bot.send(
            f'快捷编号范围为 1 ~ {HOME_SHORTCUT_END}，其中 1 为默认绑定UID。'
        )
        return None

    home_uids = await RocomUser.select_home_uids(ev.user_id, ev.bot_self_id)
    index = shortcut_number - HOME_SHORTCUT_START
    home_uid = home_uids[index] if index < len(home_uids) else None
    if not home_uid:
        await bot.send(
            f'你还没有绑定家园{shortcut_number}对应的UID，请先发送：{P}绑定uid123456'
        )
        return None
    return str(home_uid)


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
    is_pet_home_detail = is_pet_home and text.startswith('精灵详细')
    is_garden = '菜园' in ev.command
    info_name = '家园精灵详细' if is_pet_home_detail else '家园精灵' if is_pet_home else '菜园' if is_garden else '家园'

    if is_pet_home_detail:
        uid_text = text.removeprefix('精灵详细').strip()
    elif is_pet_home:
        uid_text = text.removeprefix('精灵').strip()
    else:
        uid_text = None

    uid = await _resolve_uid(bot, ev, uid_text)
    if uid is None:
        return
    await bot.send(f'正在获取[UID]{uid}的{info_name}信息，请稍后')

    if is_pet_home:
        pet_result = await get_my_pet_info_data(uid, is_pet_home_detail)
        if isinstance(pet_result, str):
            return await bot.send(pet_result)
        home_name, pet_data = pet_result
        if isinstance(pet_data, str):
            return await bot.send(pet_data)
        if not pet_data:
            return await bot.send('您的家园中没有可显示的精灵数据。')
        if is_pet_home_detail:
            return await bot.send(await draw_pet_home(uid, pet_data, home_name))
        return await bot.send(await draw_pet_home_brief(uid, pet_data, home_name))

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


@sv_home_info.on_command('生蛋了吗')
async def get_my_home_egg_info(bot: Bot, ev: Event):
    if ev.text.split():
        uid = await _resolve_uid(bot, ev)
        if uid is None:
            return
        await bot.send(f'正在进入[UID]{uid}的家园查找待收取的蛋，请稍后')
        return await bot.send(await api_to_home_egg_text(uid), at_sender=True)

    uids = await RocomUser.select_all_bound_uids(ev.user_id, ev.bot_self_id)
    if not uids:
        return await bot.send(get_bind_uid_prompt_msg())
    if len(uids) == 1:
        await bot.send(f'正在进入[UID]{uids[0]}的家园查找待收取的蛋，请稍后')
        return await bot.send(await api_to_home_egg_text(uids[0]), at_sender=True)

    await bot.send(f'正在查询{len(uids)}个账号的家园待收取的蛋，请稍后')
    results = await asyncio.gather(
        *(api_to_home_egg_text(uid) for uid in uids),
        return_exceptions=True,
    )
    texts = []
    for uid, result in zip(uids, results):
        if isinstance(result, Exception):
            texts.append(f'\nUID {uid} 查询失败：{result}')
        else:
            texts.append(result)
    return await bot.send('\n'.join(texts), at_sender=True)
