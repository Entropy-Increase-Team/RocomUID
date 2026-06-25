"""家园(精灵)：纯 PIL 出图（与旧 PIL draw_info_image.py 并存）。

布局坐标来自布局编辑器导出（左右两列卡内坐标已统一，除蛋外共用 REL）。**无浏览器依赖**：
旋转文字/阴影全走 PIL（fairytale.paste_text/drop_shadow/tilt/sticker/paste_center）。
素材：独有 UI 素材在 `texture2D/home_ui/`，img_head 复用上游 `texture2D/`，
背景 `home_ui/bg.png`(1024×1050)。左上头像随 `RC_home_use_qq_avatar`：开→玩家 QQ 头像(带环)，
关→上游 img_head。
"""
import json
import time
from pathlib import Path
from random import Random

from PIL import Image

from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import draw_pic_with_ring, get_qq_avatar

from ..utils.image import fairytale as ft
from ..utils.resource.RESOURCE_PATH import ROCOM_HEAD_PATH
from .draw_info_image import (
    feed_status_text,
    format_egg_time_text,
    is_config_enabled,
)

TEX = Path(__file__).parent / 'texture2D'        # 上游家园资源（img_head 复用）
HOME_UI = TEX / 'home_ui'                          # 家园独有素材 + bg
MAP_PATH = Path(__file__).parent.parent / 'utils' / 'map' / 'nature_map.json'

W, H = 1024, 1050
ROW0_Y = 372                 # 第 1 行卡顶
PITCH = 123                  # 行距
COL_X = [80, 517]            # 两列卡左边缘
CARD = (428, 126)            # 卡片显示尺寸
CARD_COLORS = ['card_purple', 'card_orange', 'card_green']

# 卡内元素相对卡左上角偏移（左右两列统一）
REL = {
    'frame': (77, 21), 'head': (80, 27), 'star': (24, 22),
    'name': (169, 29), 'label': (166, 56), 'status': (178, 61), 'eggline': (163, 86),
}
LV_CENTER_X, LV_Y = 50, 14            # Lv 水平居中于 cx+50、顶 cy+14
GENDER_SIZE = 26                      # 性别图标统一正方形尺寸
NATURE_REL, NATURE_SIZE = (357, 32), 20    # 性格：固定右上角
EGG_CRX, EGG_CRY, EGG_W, EGG_H = 383, 87, 40, 45   # 蛋按中心定位 + 绕中心旋转
EGG_ROT = [9.5, -9.5]                 # 左列 / 右列 蛋旋转
BLOOD_ICON_REL, BLOOD_ICON = (15, 81), 28  # 系别图标
BLOOD_TEXT_REL, BLOOD_SIZE = (42, 86), 20  # "血脉" 文字

# 素材显示尺寸
SIZE = {
    'tab_house': (200, 100), 'tab_plant': (200, 100),
    'tab_badge': (200, 100), 'tab_sofa': (200, 100), 'banner_title': (221, 47),
    'card_purple': (428, 126), 'card_orange': (428, 126), 'card_green': (428, 126),
    'avatar_frame': (90, 90), 'egg_green': (63, 72), 'egg_red': (63, 72),
    'label_blue': (113, 27), 'crown': (120, 96),
    'star_1': (47, 47), 'star_8': (47, 47), 'star_9': (47, 47),
}

_imgcache = {}
_nature_map = None


def _load(name) -> Image.Image:
    if name not in _imgcache:
        _imgcache[name] = Image.open(HOME_UI / f'{name}.png').convert('RGBA')
    return _imgcache[name]


def _blit(base: Image.Image, im: Image.Image, x, y, w, h,
          rot: float = 0.0, shadow: bool = False) -> None:
    """把 im 缩放到 (w,h) 落到 base，(x,y)=左上角。可旋转(绕中心)/加投影。"""
    im = im.resize((int(round(w)), int(round(h))), Image.LANCZOS)
    cx, cy = x + w / 2, y + h / 2
    if rot:
        im = ft.tilt(im, -rot)           # CSS rotate 顺时针为正，PIL 逆时针，取负对齐
    if shadow:
        im, _pad = ft.drop_shadow(im)
    ft.paste_center(base, im, int(round(cx)), int(round(cy)))


def _head_img(pet) -> Image.Image:
    name = f'{pet.pet_id}_1' if pet.mutation_type in (1, 9) else f'{pet.pet_id}'
    p = ROCOM_HEAD_PATH / f'{name}.png'
    if not p.exists():
        p = ROCOM_HEAD_PATH / f'{pet.pet_id}.png'
    if not p.exists():
        p = ROCOM_HEAD_PATH / '3004.png'
    return Image.open(p).convert('RGBA')


def _feed_text(pet, now):
    return feed_status_text(pet.status)


def _egg_state(pet, now):
    """返回 (生蛋行文字, 蛋素材名|None)。仅母性(gender==2)有生蛋逻辑。"""
    if pet.gender != 2:
        return '', None
    if pet.have_egg:
        return '已生蛋', 'egg_green'
    p = pet.predicted_egg_time
    if p > now:
        return f'预计生蛋 {format_egg_time_text(p, now)}', None
    if p > 0:
        return '预计已生蛋', 'egg_red'
    return '未生蛋', None


def get_nature_name(nid: int) -> str:
    """性格 id → 名（utils/map/nature_map.json）。未知 id 返回空串。"""
    global _nature_map
    if _nature_map is None:
        _nature_map = json.loads(MAP_PATH.read_text('utf-8')) if MAP_PATH.exists() else {}
    v = _nature_map.get(str(int(nid or 0)))
    if isinstance(v, dict):
        return v['name']
    return v if isinstance(v, str) else ''


async def _top_head_img(ev) -> Image.Image:
    """左上头像：配置开 + 有 QQ 头像 → QQ 头像(带环)；否则上游 img_head。"""
    if ev is not None and is_config_enabled('RC_home_use_qq_avatar'):
        sender = ev.sender if isinstance(ev.sender, dict) else {}
        avatar = sender['avatar'] if 'avatar' in sender else ''
        if avatar:
            pic = await get_qq_avatar(avatar_url=avatar)
            return await draw_pic_with_ring(pic, 140, None, False)
    return Image.open(TEX / 'img_head.png').convert('RGBA')


def _name_row(base, x, y, name, gname) -> None:
    """名字 + 性别图标：性别图标跟随名字尾部、与文字垂直居中。"""
    ft.paste_text(base, x, y, name, 27, '#58473d')
    nw = ft.cute_width(name, 27)
    _blit(base, _load(gname), x + nw + 8, y, GENDER_SIZE, GENDER_SIZE)


def _blood(base, cx, cy, blood_id) -> None:
    """血脉：系别图标 + "血脉" 文字。无图标系别(首领/污染/奇异等)→不显示。"""
    name = f'elem_{blood_id}'
    if not (HOME_UI / f'{name}.png').exists():
        return
    ix, iy = BLOOD_ICON_REL
    tx, ty = BLOOD_TEXT_REL
    _blit(base, _load(name), cx + ix, cy + iy, BLOOD_ICON, BLOOD_ICON, shadow=True)
    ft.paste_text(base, cx + tx, cy + ty, '血脉', BLOOD_SIZE, '#524640')


def _pet_card(base, pet, idx, now) -> None:
    col, row = idx % 2, idx // 2
    cx, cy = COL_X[col], ROW0_Y + row * PITCH

    def P(key):
        rx, ry = REL[key]
        return cx + rx, cy + ry

    color = Random(pet.pet_id).choice(CARD_COLORS)      # 卡色稳定随机
    _blit(base, _load(color), cx, cy, *CARD, rot=0.5, shadow=True)
    x, y = P('frame'); _blit(base, _load('avatar_frame'), x, y, *SIZE['avatar_frame'])
    x, y = P('head'); _blit(base, _head_img(pet), x, y, 90, 90)
    if pet.mutation_type in (1, 8, 9):
        x, y = P('star'); _blit(base, _load(f'star_{pet.mutation_type}'), x, y,
                                *SIZE[f'star_{pet.mutation_type}'])
    # Lv 居中（不随位数偏移）
    ft.paste_text(base, cx + LV_CENTER_X, cy + LV_Y, f'Lv.{pet.level}', 16,
                  '#f8f3e8', center=True)
    # 名字 + 性别
    x, y = P('name')
    gname = 'gender_female' if pet.gender == 2 else 'gender_male'
    _name_row(base, x, y, pet.name, gname)
    # 性格固定右上角
    nature = get_nature_name(pet.nature)
    if nature:
        ft.paste_text(base, cx + NATURE_REL[0], cy + NATURE_REL[1], nature,
                      NATURE_SIZE, '#7a6a52')
    # 状态条 + 喂食状态
    x, y = P('label'); _blit(base, _load('label_blue'), x, y, *SIZE['label_blue'])
    x, y = P('status'); ft.paste_text(base, x, y, _feed_text(pet, now), 18, '#e3d7c6')
    # 生蛋行（母）+ 蛋（中心定位 + 旋转）
    egg_line, egg_name = _egg_state(pet, now)
    if egg_line:
        x, y = P('eggline'); ft.paste_text(base, x, y, egg_line, 18, '#524640')
    if egg_name:
        _blit(base, _load(egg_name), cx + EGG_CRX - EGG_W / 2, cy + EGG_CRY - EGG_H / 2,
              EGG_W, EGG_H, rot=EGG_ROT[col], shadow=True)
    # 血脉
    _blood(base, cx, cy, pet.blood_id)


def _render(uid, home_info, head_img: Image.Image) -> Image.Image:
    now = int(time.time())
    base = _load('bg').copy()

    # 顶部：头像 / 名字 / 学号
    _blit(base, head_img, 54, 55, 140, 140)
    ft.paste_text(base, 220, 94, home_info.home_name, 40, '#58473d', rot=-2.5)
    ft.paste_text(base, 223, 145, f'学号{uid}', 30, '#857c71', rot=-2.0)

    # 信息条：4 tab 作底 + 数值 + 标签
    tabs = [('tab_house', 75, 237), ('tab_plant', 299, 242),
            ('tab_badge', 523, 246), ('tab_sofa', 747, 250)]
    for name, x, y in tabs:
        _blit(base, _load(name), x, y, *SIZE[name], rot=0.5, shadow=True)
    exp = home_info.home_experience
    exp_txt = f'{round(exp / 10000, 2)}w' if exp >= 100000 else str(exp)
    vals = [(207, 259, home_info.room_level), (418, 263, home_info.home_level),
            (609, 267, exp_txt), (847, 272, home_info.home_comfort_level)]
    for x, y, v in vals:
        ft.paste_text(base, x, y, str(v), 25, '#4e4136')
    labels = [(178, 292, '小屋等级'), (397, 295, '家园等级'),
              (622, 298, '家园经验'), (858, 301, '舒适度')]
    for x, y, t in labels:
        ft.paste_text(base, x, y, t, 18, '#948271')

    # 精灵卡（最多 10）
    for idx, pet in enumerate(home_info.home_pets[:10]):
        _pet_card(base, pet, idx, now)

    # 区块标题横幅 + 标题（最后画 → 压在第一行卡片之上）
    _blit(base, _load('banner_title'), 24, 335, *SIZE['banner_title'], rot=-0.5, shadow=True)
    ft.paste_text(base, 119, 344, '精灵信息', 26, '#feebd1',
                  stroke_width=2, stroke_fill='#423a34')

    # 右下角装饰（树叶）
    _blit(base, _load('crown'), 885, 930, *SIZE['crown'])
    return base


async def draw_home_image(ev, uid, home_info, show_pets: bool = True,
                          show_plants: bool = True) -> bytes:
    head_img = await _top_head_img(ev)
    base = _render(uid, home_info, head_img)
    return await convert_img(base)        # §9.5：发图前统一过 convert_img
