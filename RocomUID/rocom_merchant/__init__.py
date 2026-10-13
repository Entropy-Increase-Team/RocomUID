import re
import json
import time
import asyncio
import pytz
from typing import Any, Dict
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger
from gsuid_core.segment import MessageSegment
from datetime import datetime
from ..utils.rocom_api import wegame_api
from gsuid_core.subscribe import Subscribe, gs_subscribe
from gsuid_core.aps import scheduler
from ..utils.error_reply import prefix as P
from ..utils.convert import merchant_goods_names
from ..rocom_config.rocom_config import RC_CONFIG
from .draw_info_image import draw_merchant_info, draw_today_merchant_info
from ..utils.resource.RESOURCE_PATH import MAIN_PATH

wegame_api_key: str = RC_CONFIG.get_config("RC_wegame_key").data

sv_merchant = SV('rc远行商人事件', priority=5)

_MERCHANT_ROUND_HOURS = [8, 12, 16, 20]
_MERCHANT_DATA_PATH = MAIN_PATH / 'merchant'
_MERCHANT_TODAY_CACHE_PATH = _MERCHANT_DATA_PATH / 'merchant_today_cache.json'
_MERCHANT_FALLBACK_PUSH_DELAY_SECONDS = 60
_MERCHANT_TASK_NAME = '[洛克王国] 远行商人'
_MERCHANT_AT_ALL_KEY = 'rocom_merchant_at_all'
# 今日四轮商品的内存缓存
_MERCHANT_TODAY_MEMORY_CACHE: Dict[str, Any] = {
    'date': '',
    'rounds': {},
}


def _get_config_int(config_name: str, default: int) -> int:
    try:
        return int(RC_CONFIG.get_config(config_name).data)
    except Exception as e:
        logger.warning(
            f'[洛克王国服务] 配置读取失败，使用默认值: '
            f'config={config_name}, default={default}, error={e!r}'
        )
        return default


def _get_today_str(now: datetime | None = None) -> str:
    now = now or datetime.now(pytz.timezone('Asia/Shanghai'))
    return now.strftime('%Y-%m-%d')


def _get_current_merchant_round_index(now: datetime | None = None) -> int | None:
    now = now or datetime.now(pytz.timezone('Asia/Shanghai'))
    for index, hour in reversed(list(enumerate(_MERCHANT_ROUND_HOURS, start=1))):
        if now.hour >= hour:
            return index
    return None


def _is_valid_merchant_info(merchant_info: Any) -> bool:
    if not isinstance(merchant_info, list) or not merchant_info:
        return False

    for item in merchant_info:
        if not isinstance(item, dict):
            return False
        if not item.get('name') or not item.get('image'):
            return False
        if not item.get('starttime') or not item.get('endtime'):
            return False

    return True


async def _fetch_merchant_info(refresh: bool = False) -> list[Dict[str, Any]]:
    """拉取远行商人数据：优先 Ingame 接口，拉取失败降级旧接口。"""
    merchant_info = await wegame_api.get_ingame_merchant_info(
        wait_ms=8000 if refresh else 5000
    )
    if _is_valid_merchant_info(merchant_info):
        wegame_api.last_merchant_source = 'ingame'
        return merchant_info

    logger.warning(
        f'[洛克王国服务] Ingame 远行商人接口拉取失败，降级旧接口: '
        f'{wegame_api.last_error_message or "无有效商品数据"}'
    )

    legacy_info = await wegame_api.get_merchant_info(refresh=refresh)
    if _is_valid_merchant_info(legacy_info):
        wegame_api.last_merchant_source = 'legacy'
        return legacy_info

    logger.warning(
        f'[洛克王国服务] 远行商人旧接口同样拉取失败: '
        f'{wegame_api.last_error_message or "无有效商品数据"}'
    )
    wegame_api.last_merchant_source = ''
    return []


def _build_merchant_round_data(
    merchant_info: list[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        'starttime': merchant_info[0].get('starttime', ''),
        'endtime': merchant_info[0].get('endtime', ''),
        'products': merchant_info,
        'updated_at': int(time.time()),
    }


def _get_today_merchant_cache() -> Dict[str, Any]:
    """当日内存缓存；跨天或重启后自动从今日缓存文件回填。"""
    today = _get_today_str()
    if _MERCHANT_TODAY_MEMORY_CACHE.get('date') != today:
        loaded_rounds = {
            round_key: round_data
            for round_key, round_data in _load_today_merchant_cache_file().items()
            if _is_valid_merchant_info(
                round_data.get('products') if isinstance(round_data, dict) else None
            )
        }
        _MERCHANT_TODAY_MEMORY_CACHE['date'] = today
        _MERCHANT_TODAY_MEMORY_CACHE['rounds'] = loaded_rounds
        if loaded_rounds:
            logger.info(
                f'[洛克王国服务] 已载入今日远行商人缓存: '
                f'轮次={sorted(loaded_rounds.keys())}'
            )

    rounds = _MERCHANT_TODAY_MEMORY_CACHE.get('rounds')
    if not isinstance(rounds, dict):
        _MERCHANT_TODAY_MEMORY_CACHE['rounds'] = {}

    return _MERCHANT_TODAY_MEMORY_CACHE


def _update_today_merchant_memory_cache(
    round_index: int,
    merchant_info: list[Dict[str, Any]],
) -> bool:
    if not _is_valid_merchant_info(merchant_info):
        logger.warning('[洛克王国服务] 今日远行商人数据无效，跳过内存缓存更新')
        return False

    cache = _get_today_merchant_cache()
    cache['rounds'][str(round_index)] = _build_merchant_round_data(merchant_info)
    return True


def _load_today_merchant_cache_file() -> Dict[str, Any]:
    """读取今日缓存文件，非当天内容直接丢弃。"""
    _MERCHANT_DATA_PATH.mkdir(parents=True, exist_ok=True)
    if not _MERCHANT_TODAY_CACHE_PATH.exists():
        return {}

    try:
        with _MERCHANT_TODAY_CACHE_PATH.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.warning(f'[洛克王国服务] 今日远行商人缓存读取失败: {e!r}')
        return {}

    if not isinstance(data, dict) or data.get('date') != _get_today_str():
        return {}

    rounds = data.get('rounds')
    return rounds if isinstance(rounds, dict) else {}


def _save_today_merchant_cache_file(
    round_index: int,
    merchant_info: list[Dict[str, Any]],
    now: datetime | None = None,
) -> bool:
    """把某一轮商品写入今日缓存文件（只保留当天，跨天自动重置）。"""
    now = now or datetime.now(pytz.timezone('Asia/Shanghai'))
    if not _is_valid_merchant_info(merchant_info):
        logger.warning('[洛克王国服务] 今日远行商人数据无效，跳过缓存写入')
        return False

    _MERCHANT_DATA_PATH.mkdir(parents=True, exist_ok=True)
    today = _get_today_str(now)

    rounds = _load_today_merchant_cache_file()
    rounds[str(round_index)] = _build_merchant_round_data(merchant_info)

    try:
        with _MERCHANT_TODAY_CACHE_PATH.open('w', encoding='utf-8') as f:
            json.dump(
                {'date': today, 'rounds': rounds},
                f,
                ensure_ascii=False,
                indent=2,
            )
        return True
    except Exception as e:
        logger.warning(f'[洛克王国服务] 今日远行商人缓存写入失败: {e!r}')
        return False


def _record_merchant_info(
    merchant_info: list[Dict[str, Any]],
    now: datetime | None = None,
) -> None:
    """拉到数据后统一更新当日内存缓存与今日缓存文件。"""
    if not _is_valid_merchant_info(merchant_info):
        return

    now = now or datetime.now(pytz.timezone('Asia/Shanghai'))
    round_index = _get_current_merchant_round_index(now)
    if round_index is None:
        return

    _update_today_merchant_memory_cache(round_index, merchant_info)
    _save_today_merchant_cache_file(round_index, merchant_info, now)


def _get_today_merchant_rounds() -> Dict[str, Any]:
    """今日四轮数据：内存缓存优先，缺失的用今日缓存文件兜底。"""
    cache = _get_today_merchant_cache()
    memory_rounds = cache.get('rounds')
    if not isinstance(memory_rounds, dict):
        memory_rounds = {}
        cache['rounds'] = memory_rounds

    merged_rounds = dict(memory_rounds)

    cached_rounds = _load_today_merchant_cache_file()
    for round_key, round_data in cached_rounds.items():
        if round_key in merged_rounds:
            continue

        products = round_data.get('products') if isinstance(round_data, dict) else None
        if not _is_valid_merchant_info(products):
            continue

        merged_rounds[round_key] = round_data
        memory_rounds[round_key] = round_data

    return merged_rounds


@sv_merchant.on_command(('今日远行商人'))
async def get_today_merchant_info(bot: Bot, ev: Event):
    rounds = _get_today_merchant_rounds()
    if not rounds:
        return await bot.send(
            f"今日远行商人暂无数据\n可输入[{P}开启远行商人]订阅远行商人商品信息推送",
            at_sender=True,
        )

    im = await draw_today_merchant_info(rounds)
    await bot.send(im)


@sv_merchant.on_fullmatch(('远行商人'))
async def get_merchant_info_list(bot: Bot, ev: Event):
    if wegame_api_key == '':
        return await bot.send("未设置wegame_api_key，请联系机器人管理员设置后再次查询", at_sender=True)

    merchant_info = await _fetch_merchant_info()
    if not _is_valid_merchant_info(merchant_info):
        return await bot.send(f"远行商人商品未刷新\n可输入[{P}开启远行商人]订阅远行商人商品信息推送", at_sender=True)

    _record_merchant_info(merchant_info)

    im = await draw_merchant_info(merchant_info)
    await bot.send(im)


# 每日定点执行远行商人推送（整点立即拉取，未刷新再按间隔重试）
@scheduler.scheduled_job('cron', hour='8,12,16,20', minute='0')
async def refresh_merchant_info():
    if wegame_api_key == '':
        logger.warning("您未设置wegame_api_key，请设置后再次查询")
        return

    merchant_retry_count = max(_get_config_int("RC_merchant_retry_count", 20), 1)
    merchant_cd = _get_config_int("RC_merchant_cd", 30)
    fallback_delay = _get_config_int(
        "RC_merchant_fallback_delay", _MERCHANT_FALLBACK_PUSH_DELAY_SECONDS
    )
    merchant_info = []

    for jishu in range(1, merchant_retry_count + 1):
        logger.info(f"[洛克王国服务] 远行商人正在进行第{jishu}次数据获取")
        fetched_info = await _fetch_merchant_info(refresh=True)
        if _is_valid_merchant_info(fetched_info):
            if wegame_api.last_merchant_source == 'ingame':
                merchant_info = fetched_info
                break

            logger.warning(
                f'[洛克王国服务] Ingame 远行商人接口拉取失败'
                f'等待 {fallback_delay} 秒后重新拉取本轮数据'
            )
            await asyncio.sleep(fallback_delay)
            fetched_info = await _fetch_merchant_info(refresh=True)
            if _is_valid_merchant_info(fetched_info):
                merchant_info = fetched_info
                break

        if jishu < merchant_retry_count:
            await asyncio.sleep(merchant_cd)

    if not _is_valid_merchant_info(merchant_info):
        logger.warning("[洛克王国服务] 远行商人商品未刷新，本轮跳过推送")
        return

    _record_merchant_info(merchant_info)

    im = await draw_merchant_info(merchant_info)
    datas = await gs_subscribe.get_subscribe(_MERCHANT_TASK_NAME)
    for data in datas:
        names = _load_merchant_filter(data)
        if not _merchant_round_matches(names, merchant_info):
            logger.info(
                f'[洛克王国服务] 本轮远行商人没有该目标设置的商品，不推送: '
                f'subscribe_id={data.id}, uid={data.uid}, 设置={names}'
            )
            continue
        if data.user_type == 'group' and _is_merchant_at_all(data):
            await data.send([MessageSegment.at('all'), im])
        else:
            await data.send(im)


# 每轮刷新后半小时补拉一次，避免整点首拉时接口未刷新导致当天缺轮
@scheduler.scheduled_job('cron', hour='8,12,16,20', minute='30')
async def record_merchant_today_after_refresh():
    if wegame_api_key == '':
        logger.warning("您未设置wegame_api_key，请设置后再次记录远行商人数据")
        return

    merchant_info = await _fetch_merchant_info(refresh=True)
    if not _is_valid_merchant_info(merchant_info):
        logger.warning('[洛克王国服务] 远行商人刷新后半小时数据无效，跳过记录')
        return

    _record_merchant_info(merchant_info)


# 插件载入（重启）时把今日缓存文件预热进内存
try:
    _get_today_merchant_cache()
except Exception as e:
    logger.warning(f'[洛克王国服务] 今日远行商人缓存预热失败: {e!r}')


# 商人推送筛选
_MERCHANT_SELECTED_SPLIT_RE = re.compile(r'[\s,，、;；/／|｜+＋]+')


def _is_subsequence(needle: str, haystack: str) -> bool:
    it = iter(haystack)
    return all(char in it for char in needle)


def _merchant_name_matches(name: str, good: str) -> bool:
    """用户设置的词能不能算命中某个商品名。"""
    if not name or not good:
        return False
    if name in good or good in name:
        return True
    return _is_subsequence(name, good)


def _merchant_filter_scope_id(source) -> str:
    return str(
        getattr(source, 'group_id', None)
        or getattr(source, 'user_id', None)
        or ''
    )


def _load_merchant_filter(data: Subscribe) -> list[str]:
    """从订阅行读商人推送筛选。"""
    raw = getattr(data, 'extra_message', None)
    if not raw:
        return []
    try:
        names = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if not isinstance(names, list):
        return []
    return [name for name in (str(n).strip() for n in names) if name]


def _dump_merchant_filter(names: list[str]) -> str:
    return json.dumps([str(name) for name in names], ensure_ascii=False)


async def _save_merchant_filter(uid: str, names: list[str]) -> bool:
    rows = await gs_subscribe.get_subscribe(_MERCHANT_TASK_NAME, uid=uid)
    if not rows:
        return False
    payload = _dump_merchant_filter(names)
    for row in rows:
        await Subscribe.update_data_by_data({'id': row.id}, {'extra_message': payload})
    return True


async def _load_merchant_filter_for_uid(uid: str) -> list[str] | None:
    rows = await gs_subscribe.get_subscribe(_MERCHANT_TASK_NAME, uid=uid)
    if not rows:
        return None
    return _load_merchant_filter(rows[0])


def _merchant_round_matches(names: list, merchant_info: list) -> bool:
    """这一轮里有没有用户设置的推送商品"""
    if not names:
        return True
    for product in merchant_info:
        pname = str(product.get('name') or '') if isinstance(product, dict) else str(product)
        if any(_merchant_name_matches(str(name), pname) for name in names):
            return True
    return False


def _match_merchant_goods(names: list[str]) -> tuple[list[str], list[int]]:
    """把用户设置的内容匹配到商品名单里的商品名。"""
    all_indexes = list(range(1, len(names) + 1))
    if not merchant_goods_names:
        return [], all_indexes

    matched: list[str] = []
    hit_indexes: set[int] = set()
    for good in merchant_goods_names:
        good_hit = False
        for index, name in enumerate(names, 1):
            if _merchant_name_matches(name, good):
                hit_indexes.add(index)
                good_hit = True
        if good_hit:
            matched.append(good)

    unmatched_indexes = [index for index in all_indexes if index not in hit_indexes]
    return matched, unmatched_indexes


def _parse_merchant_selected_text(text: str) -> list[str]:
    names: dict[str, None] = {}
    for name in _MERCHANT_SELECTED_SPLIT_RE.split(text or ''):
        name = name.strip()
        if name:
            names.setdefault(name, None)
    return list(names)


def _format_merchant_push_filter(names: list[str], prefix: str) -> str:
    matched, unmatched_indexes = _match_merchant_goods(names)
    unmatched_text = '、'.join(f'第{index}个' for index in unmatched_indexes)

    if not matched:
        return '\n'.join([
            f'{prefix}未匹配到商品，可能不会推送：',
            f'• {unmatched_text}',
        ])

    lines = [f'{prefix}匹配到{len(matched)}个商品：']
    lines += [f'• {good}' for good in matched]
    if unmatched_indexes:
        lines.append(f'未匹配到：{unmatched_text}')

    return '\n'.join(lines)


@sv_merchant.on_command(('设置商人推送',))
async def set_merchant_push_filter(bot: Bot, ev: Event):
    names = _parse_merchant_selected_text(ev.text)
    if not await _save_merchant_filter(_merchant_filter_scope_id(ev), names):
        return await bot.send(
            f"尚未开启远行商人推送，请先发送[{P}开启远行商人]，再设置推送筛选。",
            at_sender=True,
        )

    if not names:
        return await bot.send("已清空远行商人推送筛选，之后每一轮商品都会推送。", at_sender=True)

    await bot.send(
        _format_merchant_push_filter(names, '已设置远行商人推送筛选，')
        + f"\n输入[{P}设置商人推送]可清空设置恢复全部推送",
        at_sender=True,
    )


@sv_merchant.on_fullmatch(('查看商人推送',))
async def get_merchant_push_filter(bot: Bot, ev: Event):
    names = await _load_merchant_filter_for_uid(_merchant_filter_scope_id(ev))
    if names is None:
        return await bot.send(
            f"尚未开启远行商人推送，请先发送[{P}开启远行商人]。",
            at_sender=True,
        )
    if not names:
        return await bot.send(
            "当前未设置远行商人推送筛选，每一轮商品都会推送。\n"
            f"可输入[{P}设置商人推送 商品名]推送包含指定商品的轮次",
            at_sender=True,
        )

    await bot.send(
        _format_merchant_push_filter(names, '当前远行商人推送筛选')
        + f"\n输入[{P}设置商人推送]可清空设置恢复全部推送",
        at_sender=True,
    )


def _load_merchant_extra(data) -> Dict[str, Any]:
    raw = getattr(data, 'extra_data', None)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


async def set_merchant_at_all(uid: str, enabled: bool) -> bool:
    rows = await gs_subscribe.get_subscribe(_MERCHANT_TASK_NAME, uid=uid)
    if not rows:
        return False
    for row in rows:
        extra = _load_merchant_extra(row)
        if enabled:
            extra[_MERCHANT_AT_ALL_KEY] = True
        else:
            extra.pop(_MERCHANT_AT_ALL_KEY, None)
        await Subscribe.update_data_by_data(
            {'id': row.id},
            {'extra_data': json.dumps(extra, ensure_ascii=False)},
        )
    return True


def _is_merchant_at_all(data) -> bool:
    return bool(_load_merchant_extra(data).get(_MERCHANT_AT_ALL_KEY))
