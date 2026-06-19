"""远行商人：阿信识区手绘蜡笔/拼贴风格出图。"""

import asyncio
import json
import math
from pathlib import Path

import pytz
from datetime import datetime
from PIL import Image, ImageChops, ImageDraw

from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import get_pic

from ..utils.fonts.rocom_fonts import rc_font_34, rc_font_40, rc_font_46, rc_font_84
from ..utils.image import fairytale as ft

# 名称自动缩字号（放不下就降一档），避免长名溢出卡框
_NAME_FONTS_H = [rc_font_46, rc_font_40, rc_font_34]

TEXT_PATH = Path(__file__).parent / "texture2D" / "axin"

# 画布
W = 1024
SIDE = 28
TOP_H = 248
GAP_PANEL = -12
TAG_TOP_PAD = 128
BLUE_TOP = (58, 104, 168)
BLUE_BOTTOM = (40, 78, 134)

NAME_COLOR = (74, 70, 92)
TIME_COLOR = (108, 102, 124)
FOOTER_COLOR = (250, 242, 222)

PANEL_INSET = 96
CARD_INSET = 38
PAD = 66

lunci_list = [["1", 8, 11], ["2", 12, 15], ["3", 16, 19], ["4", 20, 23]]

_cache = {}


def _pick_font(text, fonts, max_w):
    for font in fonts:
        if font.getlength(text) <= max_w:
            return font
    return fonts[-1]


# 混合可爱字体绘制走 fairytale 共享实现
_cute_width = ft.cute_width
_draw_cute = ft.draw_cute


def _load(name: str):
    if name not in _cache:
        path = TEXT_PATH / name
        _cache[name] = Image.open(path).convert("RGBA") if path.exists() else None
    return _cache[name]


def _fit_h(im, h):
    return im.resize((max(1, int(im.width * h / im.height)), h), Image.Resampling.LANCZOS)


def _fit_w(im, w):
    return im.resize((w, max(1, int(im.height * w / im.width))), Image.Resampling.LANCZOS)


def _fit_box(im, mw, mh):
    r = min(mw / im.width, mh / im.height)
    return im.resize(
        (max(1, int(im.width * r)), max(1, int(im.height * r))),
        Image.Resampling.LANCZOS,
    )


def _placeholder_icon(tier):
    color = {
        "red": (220, 120, 120),
        "purple": (170, 140, 210),
        "blue": (120, 170, 220),
    }[tier]
    im = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((10, 10, 170, 170), fill=(*color, 255))
    return im


# 品质排序：红→紫→蓝（仅排版用；list.sort 稳定，同品质保持接口原序）
_TIER_RANK = {"red": 0, "purple": 1, "blue": 2}

# 每个 tier 颜色对应的多种卡形状（按商品名稳定取用）
_SHAPE_FILES = {
    "red": ["card_red_1.png", "card_red_2.png"],
    "purple": ["card_purple_1.png", "card_purple_2.png", "card_purple_3.png"],
    "blue": ["card_blue_1.png", "card_blue_2.png"],
}


def _card_bg(tier, w, h, seed=0):
    """按 tier 取卡形状，九宫格拉伸到 (w,h)（走 fairytale 共享实现）。"""
    return ft.card_shape(tier, w, h, TEXT_PATH, _SHAPE_FILES, seed)


def _status(prop_num):
    """返回三段紧凑状态文字（贴到 3 个吊牌上）。"""
    now = datetime.now(pytz.timezone("Asia/Shanghai"))
    hh, mm = now.hour, now.minute
    lunci, idx = "1", 0
    for item in lunci_list:
        if item[1] <= hh <= item[2]:
            lunci, idx = item[0], int(item[0]) - 1
            break
    last_h, last_m = lunci_list[idx][2] - hh, 59 - mm
    last = (f"{last_h}时" if last_h > 0 else "") + (f"{last_m}分" if last_m > 0 else "")
    return f"商品 {prop_num}", f"{lunci}/4 轮", f"剩 {last or '0分'}"


def _draw_status_tags(img, parts, x0, y0, tw=172):
    """3 个挂环吊牌(蓝/黄/红)横排，挂在黑板顶沿。"""
    gap, x = 16, x0
    for name, text in zip(("tag1.png", "tag2.png", "tag3.png"), parts):
        tag = _load(name)
        if tag is None:
            continue
        t = _fit_w(tag, tw)
        td = ImageDraw.Draw(t)
        size = next((s for s in (24, 22, 20) if _cute_width(text, s) <= tw - 40), 20)
        _draw_cute(td, (t.width // 2, int(t.height * 0.78)), text, size, (82, 62, 44), anchor="mm")
        img.alpha_composite(t, (x, y0))
        x += tw + gap


def _date_time(item):
    """把 starttime('06月07日 20:00') 拆成 日期行 / 时间段行。"""
    starttime = str(item.get("starttime") or item.get("startTime") or "")
    parts = starttime.split()
    date = parts[0] if parts else ""
    stime = parts[1] if len(parts) > 1 else ""
    end = str(item.get("endtime") or item.get("endTime") or "")
    time_line = f"{stime} ~ {end}" if stime else end

    if not date and not time_line:
        remaining = item.get("remainingStr") or item.get("limit") or ""
        if remaining:
            time_line = str(remaining)

    return date, time_line


def _icon_with_edge(icon, size):
    """给商品 icon 加细白边。

    带真实透明的剪影图沿轮廓膨胀白边；不透明方图先圆形裁切再加白圈，
    避免被描成方框白边。
    """
    ic = _fit_box(icon, size, size).convert("RGBA")
    hist = ic.split()[3].histogram()
    transparent_ratio = hist[0] / max(1, ic.width * ic.height)
    if transparent_ratio <= 0.08:
        iw, ih = ic.size
        circle = Image.new("L", (iw, ih), 0)
        ImageDraw.Draw(circle).ellipse((0, 0, iw - 1, ih - 1), fill=255)
        ic.putalpha(ImageChops.multiply(ic.split()[3], circle))

    pad = 8
    canvas = Image.new("RGBA", (ic.width + pad * 2, ic.height + pad * 2), (0, 0, 0, 0))
    canvas.alpha_composite(ic, (pad, pad))
    return ft.sticker(canvas, border=6, shadow=False)


def _item_name(item):
    return str(item.get("name") or item.get("goods_name") or "未知商品")


def _draw_card(item, w, h):
    """单张商品卡（横排）：卡模板底 + icon(细白边) + 名称/日期/时间段。"""
    tier = item.get("tier", "blue")
    name = _item_name(item)
    card = _card_bg(tier, w, h, seed=sum(ord(c) for c in name))
    cd = ImageDraw.Draw(card)
    icon = item.get("_icon") or _placeholder_icon(tier)
    date, time_line = _date_time(item)

    isz = int(h * 0.62)
    ic = _icon_with_edge(icon, isz - 12)
    ft.paste_center(card, ic, CARD_INSET + 14 + ic.width // 2, h // 2)
    tx = CARD_INSET + 14 + ic.width + 22
    nf = _pick_font(name, _NAME_FONTS_H, w - CARD_INSET - tx - 6)
    cd.text((tx, h // 2 - 28), name, font=nf, fill=NAME_COLOR, anchor="lm")
    _draw_cute(cd, (tx, h // 2 + 8), date, 20, TIME_COLOR, anchor="lm")
    _draw_cute(cd, (tx, h // 2 + 32), time_line, 20, TIME_COLOR, anchor="lm")
    return card


def _draw_panel(items, cols, card_h, panel_src, top_pad=PAD):
    panel_w = W - 2 * SIDE
    inner_w = panel_w - 2 * PAD
    gap = 24
    card_w = (inner_w - gap * (cols - 1)) // cols
    rows = max(1, math.ceil(len(items) / cols))
    panel_h = top_pad + rows * card_h + gap * (rows - 1) + PAD

    if panel_src is not None:
        board = ft.nine_slice(panel_src, PANEL_INSET, PANEL_INSET, PANEL_INSET, PANEL_INSET, panel_w, panel_h)
    else:
        board = ft.wobbly_card(
            panel_w,
            panel_h,
            fill=(54, 52, 58, 255),
            outline=(150, 120, 70, 255),
            radius=30,
            border_w=10,
            shadow=False,
        )

    for i, item in enumerate(items):
        r, c = divmod(i, cols)
        card = _draw_card(item, card_w, card_h)
        x = PAD + c * (card_w + gap)
        y = top_pad + r * (card_h + gap)
        board.alpha_composite(card, (x, y))
    return board


def _compose(merchant_info):
    rotating = [i for i in merchant_info if i.get("is_rotating")]
    longterm = [i for i in merchant_info if not i.get("is_rotating")]

    # 各面板内按品质排序（红→紫→蓝），同品质保持接口原序（稳定排序）
    by_tier = lambda i: _TIER_RANK.get(i.get("tier", "blue"), 9)
    rotating.sort(key=by_tier)
    longterm.sort(key=by_tier)

    # 角色状态只看轮换商品（上面板）：常驻商品固定，参与状态判断没意义
    tiers = {i.get("tier", "blue") for i in rotating}
    char_name = (
        "char_yuange.png"
        if "red" in tiers
        else "char_yuanshang.png"
        if "purple" in tiers
        else "char_yuanqu.png"
    )
    char = _load(char_name) or _load("char_yuange.png")
    banner = _load("banner.png")

    rot_board = _draw_panel(rotating, 2, 150, _load("panel_big.png"), top_pad=TAG_TOP_PAD) if rotating else None
    long_top_pad = PAD if rotating else TAG_TOP_PAD
    long_board = _draw_panel(longterm, 2, 150, _load("panel_big.png"), top_pad=long_top_pad) if longterm else None

    footer_src = _load("footer.png")
    footer = ft.tint(footer_src, FOOTER_COLOR) if footer_src else None
    foot_h = (footer.height + 24) if footer else 0

    total_h = TOP_H
    if rot_board:
        total_h += rot_board.height + GAP_PANEL
    if long_board:
        total_h += long_board.height + GAP_PANEL
    if not rot_board and not long_board:
        total_h += 260
    total_h += 16 + foot_h

    img = ft.make_paper_bg(W, total_h, BLUE_TOP, BLUE_BOTTOM)
    draw = ImageDraw.Draw(img)

    # 面板（先画，横幅/吊牌/角色再压上去）
    y = TOP_H
    if rot_board:
        img.alpha_composite(rot_board, (SIDE, y))
        y += rot_board.height + GAP_PANEL
    if long_board:
        img.alpha_composite(long_board, (SIDE, y))
    if not rot_board and not long_board:
        empty_board = _draw_panel([], 2, 150, _load("panel_big.png"), top_pad=TAG_TOP_PAD)
        _draw_cute(ImageDraw.Draw(empty_board), (empty_board.width // 2, empty_board.height // 2 + 40), "暂无商品", 34, (250, 242, 222), anchor="mm")
        img.alpha_composite(empty_board, (SIDE, y))

    # 吊牌（先画，上移让绳子探到横幅区，随后被横幅盖住绳头）
    _draw_status_tags(img, _status(len(merchant_info)), x0=SIDE + 40, y0=TOP_H - 30)

    # 横幅（放大上移，压在黑板顶沿无缝，并盖住吊牌绳子顶端）
    if banner:
        b = _fit_w(banner, 704)
        img.alpha_composite(b, (SIDE - 8, 62))
    else:
        ft.outline_text(draw, (340, 150), "远行商人", rc_font_84)

    # 角色（最上层）
    if char:
        if char_name == "char_yuanqu.png":
            ch = _fit_w(char, 280)
            img.alpha_composite(ch, (660, TOP_H - ch.height + 20))
        else:
            ch = _fit_h(char, 330)
            img.alpha_composite(ch, (W - SIDE - ch.width - 30, TOP_H - ch.height + 82))

    # 版权底栏（居中贴在最底部）
    if footer:
        img.alpha_composite(footer, ((W - footer.width) // 2, total_h - footer.height - 12))
    return img


async def _fetch_icon(item):
    item.setdefault("_icon", None)
    url = item.get("image") or item.get("iconUrl")
    if not url:
        return
    try:
        pic = await get_pic(url)
        # get_pic 拉取失败会返回整张透明空图，getbbox 为 None → 视为无图标
        if pic is not None and pic.convert("RGBA").getbbox() is not None:
            item["_icon"] = pic.convert("RGBA")
    except Exception:
        pass


# 商品价格表：仅供本样式按价值分色。缺失时使用兜底规则。
_GOODS_CONF_PATH = Path(__file__).parent.parent / "utils" / "map" / "RANDOM_GOODS_CONF.json"
_GOODS_PRICE = {}
if _GOODS_CONF_PATH.exists():
    try:
        with _GOODS_CONF_PATH.open(encoding="utf-8") as file:
            _GOODS_PRICE = {
                it["goods_name"]: it.get("price", 0)
                for it in json.load(file).get("RocoDataRows", {}).values()
            }
    except Exception:
        _GOODS_PRICE = {}


def _classify_value(name: str) -> str:
    """按价格把商品分为 red/purple/blue 三档（柔和分色）。"""
    price = _GOODS_PRICE.get(name)
    if price is None:
        # 接口里蛋叫「炫彩精灵蛋」，价格表里叫「炫彩蛋」，去掉「精灵」再查一次
        price = _GOODS_PRICE.get(name.replace("精灵蛋", "蛋"))
    if price is None:
        if name in ["炫彩精灵蛋", "炫彩蛋", "棱镜球", "祝福项坠"]:
            return "red"
        if name in ["国王球"] or "血脉秘药" in name:
            return "purple"
        return "purple"
    if price >= 800000:
        return "red"
    if price >= 160000:
        return "purple"
    return "blue"


# 轮换商品时长上限 ≈4.5h：时长不超过此值算「轮换」(上面板)，否则「常驻」(下面板)
_ROTATING_MAX_MS = int(4.5 * 3600 * 1000)


def _classify(item):
    """给商品补出图分组字段：tier(品质分色) / is_rotating(轮换→上面板，常驻→下面板)。"""
    name = _item_name(item)
    item["tier"] = _classify_value(name)

    is_rotating = False
    start = item.get("start_time") or item.get("startTime")
    end = item.get("end_time") or item.get("endTime")
    if start is not None and end is not None:
        try:
            duration = int(end) - int(start)
            is_rotating = 0 < duration <= _ROTATING_MAX_MS
        except (TypeError, ValueError):
            is_rotating = False

    # 如果接口已直接标记，优先兼容
    if "is_rotating" in item:
        is_rotating = bool(item.get("is_rotating"))

    item["is_rotating"] = is_rotating


async def draw_merchant_info_axin(merchant_info):
    # 不直接污染上游传入对象，避免影响其他样式/后续逻辑
    items = [dict(i) for i in merchant_info]

    # 出图前先补分组字段（品质分色 / 轮换·常驻）
    for item in items:
        _classify(item)

    # 并发拉取商品图标（避免网络串行）
    await asyncio.gather(*(_fetch_icon(item) for item in items))

    # _compose 是纯 CPU PIL 合成，丢线程跑，避免卡住事件循环里其他请求
    img = await asyncio.to_thread(_compose, items)
    return await convert_img(img)
