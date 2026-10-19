import asyncio
from typing import Any, Dict, List, Optional, Tuple

from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.sv import SV

from ..rocom_config.rocom_config import RC_CONFIG
from ..utils.database.model import (
    HOME_UID_MAX_COUNT,
    UID_MIN_LENGTH,
    RocomUser,
)
from ..utils.error_reply import prefix as P
from ..utils.rocom_api import wegame_api
from .draw_rank_image import draw_pet_rank

sv_rank = SV('rc收集排行', priority=5)

HOME_SHORTCUT_START = 2
HOME_SHORTCUT_END = HOME_SHORTCUT_START + HOME_UID_MAX_COUNT - 1

RANK_LABEL = {
    'glass': '炫彩',
    'shining': '异色',
}
RANK_LIMIT_MAX = 100


def get_rank_default_limit() -> int:
    try:
        limit = int(RC_CONFIG.get_config('RC_rank_top_limit').data)
    except (TypeError, ValueError):
        limit = 10
    return max(1, min(limit, RANK_LIMIT_MAX))


def get_bind_uid_prompt_msg() -> str:
    return f'你还没有绑定RC_UID哦!\n请发送：{P}绑定uid123456\n'


async def _resolve_shortcut_uid(bot: Bot, ev: Event, number: int) -> Optional[str]:
    """把 1 / 2..20 的快捷编号换成 UID"""
    if number == 1:
        bind_uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
        if not bind_uid:
            await bot.send(get_bind_uid_prompt_msg())
            return None
        return str(bind_uid)

    if number < HOME_SHORTCUT_START or number > HOME_SHORTCUT_END:
        await bot.send(
            f'快捷编号范围为 1 ~ {HOME_SHORTCUT_END}，其中 1 为默认绑定UID。'
        )
        return None

    home_uids = await RocomUser.select_home_uids(ev.user_id, ev.bot_self_id)
    index = number - HOME_SHORTCUT_START
    home_uid = home_uids[index] if index < len(home_uids) else None
    if not home_uid:
        await bot.send(
            f'你还没有绑定家园{number}对应的UID，请先发送：{P}绑定uid123456'
        )
        return None
    return str(home_uid)


async def _parse_args(
    bot: Bot, ev: Event, command: str
) -> Tuple[Optional[int], List[str]]:
    """解析参数"""
    limit = get_rank_default_limit()
    uids: List[str] = []
    args = ev.text.split()

    for arg in args:
        if arg.startswith('前') and arg[1:].isdigit():
            limit = max(1, min(int(arg[1:]), RANK_LIMIT_MAX))
            continue
        if arg.isdigit() and len(arg) >= UID_MIN_LENGTH:
            uids = [arg]
            continue
        if arg.isdigit():
            shortcut_uid = await _resolve_shortcut_uid(bot, ev, int(arg))
            if shortcut_uid is None:
                return None, []
            uids = [shortcut_uid]
            continue

        await bot.send(
            f'无法识别的参数「{arg}」\n'
            f'用法：{P}{command} [前20] [UID/编号]\n'
            f'例：{P}{command} 前20、{P}{command} 123456'
        )
        return None, []

    if not uids:
        uids = await RocomUser.select_all_bound_uids(ev.user_id, ev.bot_self_id)

    return limit, [str(uid) for uid in uids if uid]


def _has_rank(row: Any) -> bool:
    if not isinstance(row, dict):
        return False
    try:
        return int(row.get('rank') or 0) > 0
    except (TypeError, ValueError):
        return False


async def _collect_my_ranks(
    rank_type: str,
    uids: List[str],
    main_data: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """收集自己全部绑定 UID 的排名，返回 (上榜数据, 未上榜 UID)"""
    currents: List[Dict[str, Any]] = []
    missing: List[str] = []
    if not uids:
        return currents, missing

    main_current = main_data.get('current')
    if _has_rank(main_current):
        currents.append(main_current)
    else:
        missing.append(uids[0])

    rest = uids[1:]
    if not rest:
        return currents, missing

    sem = asyncio.Semaphore(5)

    async def fetch(uid: str):
        async with sem:
            return await wegame_api.get_pet_collection_ranking(
                rank_type=rank_type,
                limit=1,
                uid=uid,
                resolve_names=False,
            )

    results = await asyncio.gather(*(fetch(uid) for uid in rest), return_exceptions=True)
    for uid, result in zip(rest, results):
        current = result.get('current') if isinstance(result, dict) else None
        if _has_rank(current):
            currents.append(current)
        elif isinstance(result, dict):
            missing.append(uid)

    return currents, missing


async def _send_rank(bot: Bot, ev: Event, rank_type: str) -> None:
    command = ev.command or f'{RANK_LABEL[rank_type]}排行'
    limit, uids = await _parse_args(bot, ev, command)
    if limit is None:
        return None

    label = RANK_LABEL[rank_type]
    await bot.send(f'正在获取{label}收集排行（前{limit}名），请稍后')

    data = await wegame_api.get_pet_collection_ranking(
        rank_type=rank_type,
        limit=limit,
        uid=uids[0] if uids else '',
    )
    if not isinstance(data, dict):
        err = wegame_api.last_error_message or '未知错误'
        return await bot.send(f'获取{label}排行失败，请稍后再试\n{err}')

    items = data.get('items') or []
    total = data.get('total') or 0
    currents, missing = await _collect_my_ranks(rank_type, uids, data)

    try:
        im = await draw_pet_rank(
            rank_type=rank_type,
            items=items,
            currents=currents,
            total=int(total),
            missing_uids=missing,
        )
    except Exception as e:
        logger.exception(f'[RocomUID] {label}排行出图失败: {e}')
        return await bot.send(f'{label}排行出图失败，请稍后再试')

    await bot.send(im, at_sender=True)
    return None


@sv_rank.on_command('炫彩排行')
async def get_glass_rank(bot: Bot, ev: Event):
    await _send_rank(bot, ev, 'glass')


@sv_rank.on_command('异色排行')
async def get_shining_rank(bot: Bot, ev: Event):
    await _send_rank(bot, ev, 'shining')
