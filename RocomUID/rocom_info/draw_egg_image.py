"""「查蛋」结果出图：与远行商人统一的手绘黑板/卡片/吊牌风格。

素材自带于本目录 texture2D（黑板面板 / 吊牌 / 卡形状），与远行商人隔离；
绘图基元复用 utils/image/fairytale（混合可爱字体 / 九宫格 / 卡形状 / 贴纸）。
只展示精灵头像 + 名称，顶部用 3 个吊牌显示查询条件，无命中也出图。
"""

import math
import os
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw

from gsuid_core.utils.image.convert import convert_img

from ..utils.image import fairytale as ft
from ..utils.resource.RESOURCE_PATH import ROCOM_HEAD_PATH

# 孵蛋自带素材目录（放 texture2D/egg/ 子目录，与作者上游 rocom_info 素材隔离避免重名）
TEX = Path(__file__).parent / 'texture2D' / 'egg'

W = 1024
SIDE = 28
TOP_H = 26                     # 黑板起始 y（往上挪，吊牌挂板底）
PANEL_INSET = 96               # 面板九宫格固定边距
PAD = 52                       # 面板内容内边距
GAP = 20                       # 卡片间距
COLS = 4
CARD_H = 178
HEAD_SIZE = 104

BLUE_TOP = (58, 104, 168)
BLUE_BOTTOM = (40, 78, 134)
NAME_COLOR = (255, 255, 255, 255)       # 名字白色
FOOTER_COLOR = (250, 242, 222)          # footer 染成暖奶油色，蓝底上清晰可读
NAME_STROKE = (66, 58, 52, 255)         # 名字深色描边
FALLBACK_HEAD = '3004.png'

# 固定挑 3 个好看的圆角卡形状（不随机），按列循环
EGG_SHAPES = ['card_purple_2.png', 'card_blue_1.png', 'card_red_2.png']
# 名字字号候选（放不下就降一档）。用混合字体绘制，生僻字自动回退 skill 字体
_NAME_SIZES = [24, 20]

_cache = {}


def _load_tex(name):
    if name not in _cache:
        p = TEX / name
        _cache[name] = Image.open(p).convert('RGBA') if p.exists() else None
    return _cache[name]


def _load_head(pet_id: str) -> Image.Image:
    path = ROCOM_HEAD_PATH / f'{pet_id}.png'
    if not os.path.exists(path):
        path = ROCOM_HEAD_PATH / FALLBACK_HEAD
    if not os.path.exists(path):
        return Image.new('RGBA', (HEAD_SIZE, HEAD_SIZE), (0, 0, 0, 0))
    return Image.open(path).convert('RGBA').resize((HEAD_SIZE, HEAD_SIZE))


def _pick_size(text, max_w):
    for s in _NAME_SIZES:
        if ft.cute_width(text, s) <= max_w:
            return s
    return _NAME_SIZES[-1]


def _pet_card(pet_id, name, shape_name, w, h) -> Image.Image:
    src = _load_tex(shape_name)
    card = (ft.nine_slice(src, 56, 30, 56, 30, w, h) if src is not None
            else ft.wobbly_card(w, h, fill=(190, 198, 222, 255), radius=22,
                                border_w=8, shadow=False))
    # 白边精灵头像（贴纸，放大）
    badge = ft.sticker(_load_head(str(pet_id)), border=6, shadow=True)
    ft.paste_center(card, badge, w // 2, 16 + badge.height // 2)
    ty = 16 + badge.height - 10
    size = _pick_size(name, w - 16)
    ft.draw_cute(ImageDraw.Draw(card), (w // 2, ty), name, size, NAME_COLOR,
                 anchor='mm', stroke_width=3, stroke_fill=NAME_STROKE)
    return card


def _draw_tags(img, texts, x0, y0, tw=176):
    """3 个吊牌横排挂在黑板顶沿，混合可爱字体居中。"""
    gap, x = 16, x0
    for i, text in enumerate(texts):
        tag = _load_tex(f'tag{i + 1}.png')
        if tag is None:
            continue
        t = tag.resize((tw, int(tag.height * tw / tag.width)), Image.LANCZOS)
        td = ImageDraw.Draw(t)
        size = next((s for s in (24, 22, 20) if ft.cute_width(text, s) <= tw - 40), 20)
        ft.draw_cute(td, (t.width // 2, int(t.height * 0.78)), text, size,
                     (82, 62, 44), anchor='mm')
        img.alpha_composite(t, (x, y0))
        x += tw + gap


def _compose(condition: dict, results: list) -> Image.Image:
    panel_w = W - 2 * SIDE
    inner_w = panel_w - 2 * PAD
    card_w = (inner_w - GAP * (COLS - 1)) // COLS
    rows = max(1, math.ceil(len(results) / COLS))
    panel_h = PAD + rows * CARD_H + GAP * (rows - 1) + PAD

    # 吊牌挂在黑板下方：上半截被黑板压住，只露下半截
    tag_w = 176
    tag_h = int(tag_w * 152 / 176)
    tag_hide = int(tag_h * 0.46)            # 被黑板盖住的高度
    _foot = _load_tex('footer.png')
    footer = ft.tint(_foot, FOOTER_COLOR) if _foot else None
    foot_h = (footer.height + 24) if footer else 0
    board_bottom = TOP_H + panel_h
    total_h = board_bottom + (tag_h - tag_hide) + 18 + foot_h

    img = ft.make_paper_bg(W, total_h, BLUE_TOP, BLUE_BOTTOM)

    # 条件吊牌（先画在黑板下方，随后黑板盖住绳头）
    egg_type = condition.get('egg_type', '随机') or '随机'
    texts = [
        f"高度 {condition.get('length', '?')}m",
        f"重量 {condition.get('weight', '?')}kg",
        f"{egg_type}蛋",
    ]
    total_tag_w = tag_w * 3 + 18 * 2
    _draw_tags(img, texts, x0=(W - total_tag_w) // 2, y0=board_bottom - tag_hide, tw=tag_w)

    # 黑板面板（panel_big 九宫格拉伸；最后贴，压住吊牌绳头）
    panel = _load_tex('panel_big.png')
    if panel is not None:
        board = ft.nine_slice(panel, PANEL_INSET, PANEL_INSET, PANEL_INSET,
                              PANEL_INSET, panel_w, panel_h)
    else:
        board = ft.wobbly_card(panel_w, panel_h, fill=(54, 52, 58, 255),
                               outline=(150, 120, 70, 255), radius=30, border_w=10,
                               shadow=False)

    if results:
        for idx, (pet_id, name) in enumerate(results):
            r, c = divmod(idx, COLS)
            shape = Random(pet_id).choice(EGG_SHAPES)   # 按 pet_id 稳定随机配色
            card = _pet_card(pet_id, name, shape, card_w, CARD_H)
            x = PAD + c * (card_w + GAP)
            y = PAD + r * (CARD_H + GAP)
            board.alpha_composite(card, (x, y))
    else:
        bd = ImageDraw.Draw(board)
        cy = panel_h // 2
        ft.draw_cute(bd, (panel_w // 2, cy - 20), '没有找到匹配的精灵蛋', 40,
                     (236, 232, 240), anchor='mm')
        ft.draw_cute(bd, (panel_w // 2, cy + 36), '换个尺寸或重量再试试吧', 26,
                     (196, 192, 205), anchor='mm')

    img.alpha_composite(board, (SIDE, TOP_H))
    # 版权底栏（居中贴在最底部）
    if footer:
        img.alpha_composite(footer, ((W - footer.width) // 2, total_h - footer.height - 12))
    return img


async def draw_egg_info(condition: dict, results: list) -> bytes:
    """对外接口：渲染查蛋结果图并返回可发送的图片。

    :param condition: {"length", "weight", "egg_type"}
    :param results: [(pet_id, name), ...]
    """
    return await convert_img(_compose(condition, results))
