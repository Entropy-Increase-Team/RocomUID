import math
import time
from pathlib import Path

import pytz
from datetime import datetime
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import get_pic

from ..rocom_config.rocom_config import RC_CONFIG
from ..utils.fonts.rocom_fonts import rc_font_40, skill_font_18, skill_font_26

TEXT_PATH = Path(__file__).parent / 'texture2D'

# 远行商人样式素材
title = Image.open(TEXT_PATH / 'title.png').convert('RGBA')
num_badge = Image.open(TEXT_PATH / 'num_badge.png').convert('RGBA')
footer_frame = Image.open(TEXT_PATH / 'footer_frame.png').convert('RGBA')
hot_badge = Image.open(TEXT_PATH / 'hot.png').convert('RGBA')
coin_icon = Image.open(TEXT_PATH / 'coin.png').convert('RGBA')

# 远行商人样式素材
classic_badge = Image.open(TEXT_PATH / 'badge.png').convert('RGBA')
classic_banner = Image.open(TEXT_PATH / 'banner.png').convert('RGBA')
classic_susume = Image.open(TEXT_PATH / 'susume.png').convert('RGBA')
classic_footer = Image.open(TEXT_PATH / 'footer.png').convert('RGBA')
classic_top_img = Image.open(TEXT_PATH / 'bg_top.jpg').convert('RGB')
classic_footer_img = Image.open(TEXT_PATH / 'bg_footer.jpg').convert('RGB')

PRODUCT_FONT_PATH = TEXT_PATH / 'product.ttf'
NUMBER_FONT_PATH = TEXT_PATH / 'number.woff2'


def product_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(PRODUCT_FONT_PATH), size=size)


def number_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(NUMBER_FONT_PATH), size=size)


font_name = product_font(150)
font_empty = product_font(64)
font_date = product_font(32)
font_time = product_font(50)
font_num = number_font(28)
font_price = number_font(136)
font_unit = number_font(58)
font_limit = number_font(36)

PAGE_WIDTH = 1080
PAGE_BG = (244, 238, 224, 255)
DARK = (63, 56, 50, 255)
CREAM = (244, 238, 224, 255)
CARD_BG = (206, 200, 188, 255)
GRAY = (131, 127, 118, 255)
LIMIT_BG = (135, 128, 112, 255)
LIMIT_TEXT = (253, 247, 233, 255)

ROUND_WINDOWS = [
    {'id': 1, 'label': '08:00-12:00', 'start': 8, 'end': 12},
    {'id': 2, 'label': '12:00-16:00', 'start': 12, 'end': 16},
    {'id': 3, 'label': '16:00-20:00', 'start': 16, 'end': 20},
    {'id': 4, 'label': '20:00-24:00', 'start': 20, 'end': 24},
]

CLASSIC_ROUND_WINDOWS = [
    ['1', 8, 11],
    ['2', 12, 15],
    ['3', 16, 19],
    ['4', 20, 23],
]


def _fit_font(text: str, base_size: int, max_width: int) -> ImageFont.FreeTypeFont:
    size = base_size
    while size >= 72:
        font = product_font(size)
        bbox = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 6
    return product_font(size)


def _paste_with_outline(
    base: Image.Image,
    img: Image.Image,
    pos: tuple[int, int],
    outline: int = 11,
    outline_color: tuple[int, int, int, int] = CREAM,
    offset: tuple[int, int] = (3, 3),
) -> None:
    source = img.convert('RGBA')
    pad = outline + max(abs(offset[0]), abs(offset[1])) + 4

    padded = Image.new('RGBA', (source.width + pad * 2, source.height + pad * 2), (0, 0, 0, 0))
    padded.paste(source, (pad, pad), source)

    alpha = padded.getchannel('A')
    outline_alpha = alpha.filter(ImageFilter.MaxFilter(outline * 2 + 1))
    outline_img = Image.new('RGBA', padded.size, outline_color)
    outline_img.putalpha(outline_alpha)

    layer = Image.new('RGBA', padded.size, (0, 0, 0, 0))
    layer.paste(outline_img, offset, outline_img)
    layer.paste(padded, (0, 0), padded)

    base.paste(layer, (pos[0] - pad, pos[1] - pad), layer)


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    stroke_width: int = 0,
    stroke_fill: tuple[int, int, int, int] = CREAM,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    x = center[0] - (bbox[2] - bbox[0]) / 2 - bbox[0]
    y = center[1] - (bbox[3] - bbox[1]) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def _draw_gradient_text(
    base: Image.Image,
    pos: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    top_color: tuple[int, int, int] = (208, 115, 56),
    bottom_color: tuple[int, int, int] = (221, 144, 54),
    stroke_width: int = 0,
    stroke_fill: tuple[int, int, int, int] = CREAM,
    scale_x: float = 1.0,
    tracking: int = 0,
) -> int:
    if not text:
        text = '0'

    text = str(text)
    tmp = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    tmp_draw = ImageDraw.Draw(tmp)

    char_boxes = [tmp_draw.textbbox((0, 0), ch, font=font, stroke_width=stroke_width) for ch in text]
    min_y = min(box[1] for box in char_boxes)
    max_y = max(box[3] for box in char_boxes)
    advances = [font.getlength(ch) for ch in text]
    width = math.ceil(sum(advances) + tracking * max(0, len(text) - 1))
    height = math.ceil(max_y - min_y)

    text_layer = Image.new('RGBA', (width + 40, height + 40), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    mask = Image.new('L', text_layer.size, 0)
    mask_draw = ImageDraw.Draw(mask)

    cursor_x = 20
    base_y = 20 - min_y

    for index, ch in enumerate(text):
        if stroke_width > 0:
            text_draw.text(
                (cursor_x, base_y),
                ch,
                font=font,
                fill=(0, 0, 0, 0),
                stroke_width=stroke_width,
                stroke_fill=stroke_fill,
            )
        mask_draw.text((cursor_x, base_y), ch, font=font, fill=255)
        cursor_x += advances[index] + tracking

    gradient = Image.new('RGBA', text_layer.size, (0, 0, 0, 0))
    grad_px = gradient.load()
    for y in range(text_layer.height):
        ratio = y / max(1, text_layer.height - 1)
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        for x in range(text_layer.width):
            grad_px[x, y] = (r, g, b, 255)
    text_layer.alpha_composite(Image.composite(gradient, Image.new('RGBA', text_layer.size, (0, 0, 0, 0)), mask))

    if scale_x != 1.0:
        scaled_width = max(1, int(text_layer.width * scale_x))
        text_layer = text_layer.resize((scaled_width, text_layer.height), Image.Resampling.LANCZOS)
        width = max(1, int(width * scale_x))

    base.paste(text_layer, (int(pos[0] - 20), int(pos[1] - 20)), text_layer)
    return width


def _get_current_round_info() -> tuple[str, str]:
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    date_str = f'{now.month}.{now.day}'
    time_range = '--:--~--:--'
    for win in ROUND_WINDOWS:
        if win['start'] <= now.hour < win['end']:
            time_range = win['label']
            break
    return date_str, time_range


def _is_hot_item(item: dict) -> bool:
    if 'isHot' in item:
        return bool(item.get('isHot'))
    return item.get('name') in ['炫彩精灵蛋', '棱镜球', '国王球']


async def _draw_goods_card(img: Image.Image, item: dict, index: int, top: int) -> None:
    card = Image.new('RGBA', (1043, 308), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)

    is_ended = bool(item.get('isEnded', False))
    card_alpha = 128 if is_ended else 255
    name_color = (135, 128, 112, card_alpha) if is_ended else DARK
    shadow_color = (200, 194, 184, card_alpha) if is_ended else CREAM
    price_gray = (135, 128, 112, card_alpha) if is_ended else GRAY

    draw.rounded_rectangle((0, 0, 1043, 308), radius=15, fill=(*CARD_BG[:3], card_alpha))

    # 商品名
    name = str(item.get('goods_name') or item.get('name') or '未知商品')
    name_font = _fit_font(name, 150, 735)
    bbox = draw.textbbox((0, 0), name, font=name_font)
    name_x = 378 - (bbox[2] - bbox[0]) / 2 - bbox[0]
    name_y = -8 - bbox[1]
    draw.text((name_x + 2, name_y + 4), name, font=name_font, fill=shadow_color, stroke_width=11, stroke_fill=shadow_color)
    draw.text((name_x, name_y), name, font=name_font, fill=name_color)

    # 编号角标
    num = str(item.get('num') or f'{index + 1:02d}')
    card.paste(num_badge, (725, -15), num_badge)
    _draw_centered_text(draw, (762, 12), num, font_num, LIMIT_TEXT)

    # 商品图标
    icon_url = item.get('iconUrl') or item.get('image')
    if icon_url:
        try:
            prop_icon = await get_pic(icon_url)
            prop_icon = prop_icon.convert('RGBA')
            prop_icon.thumbnail((296, 246), Image.Resampling.LANCZOS)
            icon_x = 725 + (296 - prop_icon.width) // 2
            icon_y = 31 + (246 - prop_icon.height) // 2
            _paste_with_outline(card, prop_icon, (icon_x, icon_y), outline=11)
        except Exception:
            pass

    if _is_hot_item(item):
        hot = hot_badge.resize((111, 111), Image.Resampling.LANCZOS)
        card.paste(hot, (910, 0), hot)

    # 价格区域：金币 + 数字 + /个
    coin = coin_icon.resize((91, 90), Image.Resampling.LANCZOS)
    _paste_with_outline(card, coin, (171, 141), outline=8, offset=(0, 0))
    price = str(item.get('price') or item.get('cost') or 0)

    price_x = 260
    price_y = 135
    if is_ended:
        price_w = _draw_gradient_text(
            card,
            (price_x, price_y),
            price,
            font_price,
            top_color=price_gray[:3],
            bottom_color=price_gray[:3],
            stroke_width=11,
            scale_x=1.08,
            tracking=-14,
        )
    else:
        price_w = _draw_gradient_text(
            card,
            (price_x, price_y),
            price,
            font_price,
            stroke_width=11,
            scale_x=1.08,
            tracking=-14,
        )

    sep_x = price_x + price_w - 50
    sep_y = price_y - 1
    draw.text((sep_x + 2, sep_y + 4), '/', font=font_price, fill=CREAM, stroke_width=11, stroke_fill=CREAM)
    draw.text((sep_x, sep_y), '/', font=font_price, fill=price_gray)
    unit_x = sep_x + 58
    unit_y = price_y + 63
    draw.text((unit_x + 2, unit_y + 4), '个', font=font_unit, fill=CREAM, stroke_width=8, stroke_fill=CREAM)
    draw.text((unit_x, unit_y), '个', font=font_unit, fill=price_gray)

    # 限购信息
    remaining = str(item.get('remainingStr') or item.get('limit') or '')
    if not remaining:
        buy_limit = item.get('buy_limit_num') or item.get('limit_num') or item.get('limitNum')
        if buy_limit:
            remaining = f'本轮限购{buy_limit}个'
        else:
            remaining = f"{item.get('starttime', '')} {item.get('endtime', '')}".strip() or '本轮限购--个'

    limit_bbox = draw.textbbox((0, 0), remaining, font=font_limit)
    limit_w = max(393, limit_bbox[2] - limit_bbox[0] + 60)
    limit_x = 377 - limit_w // 2
    draw.rounded_rectangle((limit_x, 243, limit_x + limit_w, 297), radius=14, fill=CREAM)
    draw.rounded_rectangle((limit_x + 8, 251, limit_x + limit_w - 8, 289), radius=10, fill=LIMIT_BG)
    _draw_centered_text(draw, (377, 270), remaining, font_limit, LIMIT_TEXT)

    if is_ended:
        alpha = card.getchannel('A').point(lambda a: int(a * 0.5))
        card.putalpha(alpha)

    img.paste(card, (20, top), card)


async def _draw_merchant_info_new(merchant_info):
    goods_count = len(merchant_info)
    start_y = 592
    card_height = 308
    gap = 43

    last_card_top = start_y + max(goods_count - 1, 0) * (card_height + gap)
    bottom_frame_top = last_card_top + 287
    img_height = bottom_frame_top + 160

    img = Image.new('RGBA', (PAGE_WIDTH, img_height), PAGE_BG)
    draw = ImageDraw.Draw(img)

    # 顶部标题图与时间
    img.paste(title, (20, 21), title)
    date_str, time_range = _get_current_round_info()
    draw.text((342, 446), date_str, font=font_date, fill=(129, 120, 115, 255), stroke_width=10, stroke_fill=DARK)
    draw.text((468, 432), time_range, font=font_time, fill=(240, 201, 70, 255), stroke_width=10, stroke_fill=DARK)

    if merchant_info:
        for index, item in enumerate(merchant_info):
            await _draw_goods_card(img, item, index, start_y + index * (card_height + gap))
    else:
        draw.rounded_rectangle((20, start_y, 1063, start_y + card_height), radius=15, fill=CARD_BG)
        _draw_centered_text(draw, (541, start_y + 154), '暂无商品', font_empty, LIMIT_BG)

    img.paste(footer_frame, (0, bottom_frame_top), footer_frame)

    res = await convert_img(img)
    return res


def _get_classic_round_info(prop_num: int) -> tuple[str, str, str]:
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    this_hour = now.hour
    this_minute = now.minute

    round_id = '1'
    round_index = 0
    for index, item in enumerate(CLASSIC_ROUND_WINDOWS):
        if item[1] <= this_hour <= item[2]:
            round_id = item[0]
            round_index = index
            break

    last_hour = CLASSIC_ROUND_WINDOWS[round_index][2] - this_hour
    last_min = 59 - this_minute
    last_time = ''
    if last_hour > 0:
        last_time += f'{last_hour}时'
    if last_min > 0:
        last_time += f'{last_min}分'
    if not last_time:
        last_time = '即将刷新'

    return f'当前商品 {prop_num}', f'第 {round_id}/4 轮', f'剩余 {last_time}'


async def _draw_merchant_info_classic(merchant_info):
    prop_num = len(merchant_info)
    prop_height = max(556, math.ceil(prop_num / 2) * 206)
    img_height = prop_height + 474

    img = Image.new('RGBA', (1000, img_height))
    img.paste(classic_top_img, (0, 0))

    bg_center = Image.open(TEXT_PATH / 'bg_center.jpg').resize((1000, prop_height))
    img.paste(bg_center, (0, 321))
    img.paste(classic_footer_img, (0, prop_height + 321))
    img.paste(classic_banner, (196, 252), classic_banner)

    img_draw = ImageDraw.Draw(img)
    prop_num_text, round_text, last_time_text = _get_classic_round_info(prop_num)

    img_draw.text((285, 270), prop_num_text, (255, 255, 255), skill_font_26, 'mm')
    img_draw.text((500, 270), round_text, (255, 255, 255), skill_font_26, 'mm')
    img_draw.text((706, 270), last_time_text, (255, 255, 255), skill_font_26, 'mm')

    start_height = 277
    for index, prop_item in enumerate(merchant_info):
        rc_y = math.floor(index / 2)
        rc_x = index - (2 * rc_y)

        prop_img = Image.new('RGBA', (512, 256), (255, 255, 255, 0))
        prop_img.paste(classic_badge, (0, 0), classic_badge)

        icon_url = prop_item.get('image') or prop_item.get('iconUrl')
        if icon_url:
            try:
                prop_icon = await get_pic(icon_url)
                prop_icon = prop_icon.convert('RGBA')
                width, height = prop_icon.size
                if width >= height:
                    scale = 145 / width
                    width = 145
                    height = int(height * scale)
                else:
                    scale = 145 / height
                    width = int(width * scale)
                    height = 145
                prop_icon = prop_icon.resize((width, height), Image.Resampling.LANCZOS)
                icon_x = 131 - int(width / 2)
                icon_y = 128 - int(height / 2)
                prop_img.paste(prop_icon, (icon_x, icon_y), prop_icon)
            except Exception:
                pass

        prop_draw = ImageDraw.Draw(prop_img)
        name = str(prop_item.get('name') or prop_item.get('goods_name') or '未知商品')
        prop_draw.text((210, 116), name, (255, 255, 63), rc_font_40, 'lm')

        start_time = prop_item.get('starttime', '')
        end_time = prop_item.get('endtime', '')
        prop_draw.text((210, 152), f'{start_time} ~ {end_time}', (198, 222, 246), skill_font_18, 'lm')

        if name in ['炫彩精灵蛋', '棱镜球', '国王球']:
            prop_img.paste(classic_susume, (371, 37), classic_susume)

        img.paste(prop_img, (453 * rc_x + 14, rc_y * 206 + start_height), prop_img)

    img.paste(classic_footer, (277, img_height - 95), classic_footer)
    res = await convert_img(img)
    return res


async def draw_merchant_info(merchant_info):
    style = str(RC_CONFIG.get_config('RC_merchant_render_style').data or 'new').lower()
    if style == 'classic':
        return await _draw_merchant_info_classic(merchant_info)
    return await _draw_merchant_info_new(merchant_info)
