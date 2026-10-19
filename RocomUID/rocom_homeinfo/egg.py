"""生蛋了吗"""
from typing import Dict

from ..utils.convert import get_nature_name
from ..utils.rocom_api import wegame_api

_CIRCLED_NUM = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'


def _mutation_tag(egg: Dict) -> str:
    name = str(egg.get('mutation_name') or '').strip()
    return f'（{name}）' if name and name != '普通' else ''


def _format_voice(voice) -> str:
    if voice in [None, '']:
        return ''
    try:
        return f'{int(float(voice))}dB'
    except (TypeError, ValueError):
        return f'{voice}dB'


def build_egg_line(index: int, egg: Dict) -> str:
    mother = egg.get('mother_candidate') or {}
    fathers = egg.get('father_candidates') or []
    father = fathers[0] if fathers and isinstance(fathers[0], dict) else {}

    mother_nature = get_nature_name(mother.get('nature'))
    mother_name = str(mother.get('name') or mother.get('pet_default_name') or '未知精灵')
    mark = _CIRCLED_NUM[index] if index < len(_CIRCLED_NUM) else f'{index + 1}.'

    detail = _format_voice(father.get('voice'))
    if not detail:
        detail = _format_voice(mother.get('voice'))
    return f'{mark} {mother_nature}{mother_name}{_mutation_tag(egg)}：{detail}'


async def api_to_home_egg_text(uid: str) -> str:
    data = await wegame_api.get_home_scene_info(uid)
    if data is None:
        return await wegame_api._get_last_error()

    scene = data.get('home_scene_info')
    if not isinstance(scene, dict):
        return '没有获取到该用户的家园场景信息'

    home = scene.get('home') or {}
    owner_id = home.get('home_owner_id') or uid
    home_name = home.get('home_name') or '未命名家园'
    eggs = [egg for egg in (scene.get('eggs') or []) if isinstance(egg, dict)]

    lines = [f'\nUID {owner_id}（{home_name}）{len(eggs)}颗']
    lines.extend(build_egg_line(index, egg) for index, egg in enumerate(eggs))
    lines.append(f'共发现 {len(eggs)} 个待收取的蛋。')
    return '\n'.join(lines)
