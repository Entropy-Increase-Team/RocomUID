"""菜园(种植)：纯 PIL 出图（新版 UI；与旧 PIL draw_info_image.py 的菜园回退并存）。

布局取自布局编辑器导出的坐标：5 列网格竖卡、卡内圆形作物 icon(沿像素轮廓奶油描边)、
作物名/状态/倒计时**水平居中**、进度条(透明槽框压黄条)。卡片三色(橙/绿/紫)按作物随机。
素材隔离在 `texture2D/garden_ui/`，背景为菜园专属 bg.png(1024²)。**无浏览器依赖**：
旋转文字/阴影全走 PIL（fairytale.paste_text/drop_shadow/tilt/sticker/paste_center）。
"""
import json
import time
from pathlib import Path
from random import Random

from PIL import Image

from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import draw_pic_with_ring, get_qq_avatar

from ..utils.image import fairytale as ft
from .draw_info_image import is_config_enabled

HERE = Path(__file__).parent
TEX = HERE / 'texture2D'
GARDEN = TEX / 'garden_ui'
HOME_ICON = TEX / 'home_icon'          # 作物道具图 {iconid}_2.png

W, H = 1024, 1024

HEAD_XYWH = (92, 49, 142, 142)         # 左上头像
CARD_COLORS = ['card_orange', 'card_green', 'card_purple']

# 作物卡网格（列距 171 / 行距 168，卡 120×150，最多 5×3=15）
COLX = [110, 281, 452, 623, 794]
ROWY = [489, 657, 825]
CARDW, CARDH = 120, 150
MAXN = len(COLX) * len(ROWY)

# 卡内相对偏移（相对卡左上角）
ICON_REL = (24, 5, 72, 72)             # 作物 icon（沿像素轮廓描边后 58+2*(3+4)=72）
NAME_RELY, NAME_SIZE = 82, 17          # 作物名（居中 + 描边 + 微倾斜）
STAT_RELY, STAT_SIZE = 100, 16         # 状态：成长中 / 已成熟
TIME_RELY, TIME_SIZE = 116, 14         # 倒计时（仅成长中）
PB_REL = (17, 126, 86, 20)             # 进度条显示区

CREAM = (245, 238, 222, 255)           # 作物 icon 奶油描边色

_imgcache = {}
_pb_track = None


def _load(name) -> Image.Image:
    if name not in _imgcache:
        _imgcache[name] = Image.open(GARDEN / f'{name}.png').convert('RGBA')
    return _imgcache[name]


def _blit(base: Image.Image, im: Image.Image, x, y, w, h,
          rot: float = 0.0, shadow: bool = False) -> None:
    """把 im 缩放到 (w,h) 落到 base 上，(x,y)=左上角。可旋转(绕中心)/加投影。"""
    im = im.resize((int(w), int(h)), Image.LANCZOS)
    cx, cy = x + w / 2, y + h / 2
    if rot:
        im = ft.tilt(im, -rot)           # CSS rotate 顺时针为正，PIL 逆时针，取负对齐
    if shadow:
        im, _pad = ft.drop_shadow(im)
    ft.paste_center(base, im, int(round(cx)), int(round(cy)))


def _icon_img(iconid) -> Image.Image:
    """作物道具图 → 沿像素轮廓描一圈奶油细边（fairytale.sticker，无投影、不裁形状）。"""
    p = HOME_ICON / f'{iconid}_2.png'
    if not p.exists():
        p = HOME_ICON / f'{iconid}.png'
    if not p.exists():
        return Image.new('RGBA', (72, 72), (0, 0, 0, 0))
    im = Image.open(p).convert('RGBA').resize((58, 58), Image.LANCZOS)
    return ft.sticker(im, border=3, border_color=CREAM, shadow=False)


def _progress_img(pct: float) -> Image.Image:
    """按进度合成进度条：透明槽框压在按比例左裁的黄条之上（全尺寸，落图时降采样）。"""
    global _pb_track
    pct = max(0.0, min(1.0, pct))
    if _pb_track is None:
        _pb_track = json.loads((GARDEN / 'progress_track.json').read_text('utf-8'))
    tx, ty, tw, th = (_pb_track['x'], _pb_track['y'], _pb_track['w'], _pb_track['h'])
    slot = _load('progress_slot')
    fill = _load('progress_fill')
    left_ext, right_ext, vert_ext = 55, 35, 18      # 黄条相对轨道左/右/上下扩展
    fx, fy = tx - left_ext, ty - vert_ext
    fw, fh = tw + left_ext + right_ext, th + 2 * vert_ext
    full = fill.resize((fw, fh), Image.LANCZOS)
    base = Image.new('RGBA', slot.size, (0, 0, 0, 0))
    if pct > 0:
        w = max(1, int(round(fw * pct)))
        base.alpha_composite(full.crop((0, 0, w, fh)), (fx, fy))
    base.alpha_composite(slot, (0, 0))
    return base


def _grow(rip, now, tab_id):
    """返回 (状态文字, 倒计时文字|None, 进度0~1)。成熟则倒计时 None、进度满。"""
    if now >= rip:
        return '已成熟', None, 1.0
    remain = rip - now
    hours, minutes = remain // 3600, (remain % 3600) // 60
    total = 21600 * max(1, tab_id)
    pct = max(0.0, min(1.0, (total - remain) / total))
    return '成长中', f'{hours}小时{minutes}分钟', pct


async def _top_head_img(ev) -> Image.Image:
    """左上头像：配置开 + 有 QQ 头像 → QQ 头像(带环)；否则上游 img_head。"""
    if ev is not None and is_config_enabled('RC_home_use_qq_avatar'):
        sender = ev.sender if isinstance(ev.sender, dict) else {}
        avatar = sender['avatar'] if 'avatar' in sender else ''
        if avatar:
            pic = await get_qq_avatar(avatar_url=avatar)
            return await draw_pic_with_ring(pic, 140, None, False)
    return Image.open(TEX / 'img_head.png').convert('RGBA')


def _plant_card(base: Image.Image, plant, idx: int, now: int) -> None:
    col, row = idx // len(ROWY), idx % len(ROWY)   # 竖排：先填满一列再换下一列
    cx, cy = COLX[col], ROWY[row]
    ccx = cx + CARDW / 2
    color = Random(f'{plant.plant_info.iconid}_{idx}').choice(CARD_COLORS)   # 三色稳定随机
    _blit(base, _load(color), cx, cy, CARDW, CARDH, shadow=True)
    ix, iy, iw, ih = ICON_REL
    _blit(base, _icon_img(plant.plant_info.iconid), cx + ix, cy + iy, iw, ih)
    ft.paste_text(base, ccx, cy + NAME_RELY, plant.plant_info.name, NAME_SIZE,
                  '#efdebd', rot=-5, stroke_width=2, stroke_fill='#423a34', center=True)
    stat, ttext, pct = _grow(plant.plant_rip_time, now, plant.plant_tab_id)
    ft.paste_text(base, ccx, cy + STAT_RELY, stat, STAT_SIZE, '#624e3a', center=True)
    if ttext:
        ft.paste_text(base, ccx, cy + TIME_RELY, ttext, TIME_SIZE, '#624e3a', center=True)
    px, py, pw, ph = PB_REL
    _blit(base, _progress_img(pct), cx + px, cy + py, pw, ph)


def _render(uid, home_info, head_img: Image.Image) -> Image.Image:
    now = int(time.time())
    base = _load('bg').copy()

    hx, hy, hw, hh = HEAD_XYWH
    _blit(base, head_img, hx, hy, hw, hh)
    ft.paste_text(base, 263, 111, home_info.home_name, 40, '#614a3b', rot=-3)
    _blit(base, _load('banner_plant'), 253, 163, 186, 46, rot=-1, shadow=True)
    ft.paste_text(base, 260, 172, f'学号{uid}', 25, '#554d31', rot=-1)

    exp = home_info.home_experience
    exp_t = f'{round(exp / 10000, 2)}w' if exp >= 100000 else str(exp)
    # 4 个数值水平居中于各栏中心（位数变化也对称、不偏不溢出）
    vals = [(204, 289, home_info.room_level), (422, 281, home_info.home_level),
            (654, 270, exp_t), (875, 261, home_info.home_comfort_level)]
    for x, y, v in vals:
        ft.paste_text(base, x, y, str(v), 37, '#4d392d', rot=-2.5, center=True)
    labels = [(167, 346, '小屋等级'), (387, 337, '家园等级'),
              (603, 329, '家园经验'), (848, 315, '舒适度')]
    for x, y, t in labels:
        ft.paste_text(base, x, y, t, 19, '#624e3a', rot=-2.5)
    ft.paste_text(base, 157, 435, '种植信息', 31, '#f3ebda', rot=-4.5)

    for idx, plant in enumerate(home_info.home_plants[:MAXN]):
        _plant_card(base, plant, idx, now)

    _blit(base, _load('wood_bar'), 860, 462, 80, 69)
    _blit(base, _load('deco_leaf'), 853, 896, 128, 109)
    return base


async def draw_garden_image(ev, uid, home_info, show_pets: bool = False,
                            show_plants: bool = True) -> bytes:
    head_img = await _top_head_img(ev)
    base = _render(uid, home_info, head_img)
    return await convert_img(base)
