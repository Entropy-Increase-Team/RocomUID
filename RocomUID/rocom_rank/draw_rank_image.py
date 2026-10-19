import io
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from PIL import Image, ImageDraw, ImageFilter

from gsuid_core.logger import logger
from gsuid_core.utils.image.convert import convert_img

from ..utils.rocom_api import wegame_api
from ..utils.image.image_tools import get_footer_w, FOOTER_SOURCE
from ..utils.fonts.rocom_fonts import (
    rc_font_18,
    rc_font_20,
    rc_font_22,
    rc_font_24,
    rc_font_28,
    rc_font_42,
)

TEXT_PATH = Path(__file__).parent / 'texture2D'
ICON_GLASS = Image.open(TEXT_PATH / 'star_9.png').convert('RGBA')
ICON_SHINING = Image.open(TEXT_PATH / 'star_1.png').convert('RGBA')
DEFAULT_AVATAR = Image.open(TEXT_PATH / 'img_head.png').convert('RGBA')

WIKI_ASSET_BASE = 'https://wegame.shallow.ink/api/v1/resources/wiki/assets/profile'

# 版式
PAGE_W = 880
CARD_X = 40
CARD_W = 800
CARD_H = 150
CARD_GAP = 14
CARD_RADIUS = 20
BANNER_H = 108
AVATAR_SIZE = 128

# 配色
COLOR_TITLE = (88, 68, 46)
COLOR_SUB = (150, 128, 100)
COLOR_CARD = (255, 253, 247)
COLOR_SIGN = (110, 91, 69)
COLOR_EMPTY_SIGN = (166, 150, 128)
COLOR_DIVIDER = (222, 205, 176)

RANK_BADGE_COLOR = {
    1: (231, 163, 30),
    2: (166, 178, 194),
    3: (196, 128, 68),
}
RANK_BADGE_DEFAULT = (72, 72, 84)

RANK_META = {
    'glass': {
        'title': '炫彩排行',
        'icon': ICON_GLASS,
    },
    'shining': {
        'title': '异色排行',
        'icon': ICON_SHINING,
    },
}

EMPTY_SIGNATURE = '这个人很神秘，什么也没有留下~'


def _rounded_mask(size: Tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new('L', size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255
    )
    return mask


def _cover(img: Image.Image, size: Tuple[int, int]) -> Image.Image:
    tw, th = size
    ratio = max(tw / img.width, th / img.height)
    nw, nh = max(tw, round(img.width * ratio)), max(th, round(img.height * ratio))
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def _fit(img: Image.Image, size: Tuple[int, int]) -> Image.Image:
    ratio = min(size[0] / img.width, size[1] / img.height)
    return img.resize(
        (max(1, round(img.width * ratio)), max(1, round(img.height * ratio))),
        Image.LANCZOS,
    )


def _truncate(
    draw: ImageDraw.ImageDraw, text: str, font, max_width: int
) -> str:
    if draw.textlength(text, font=font) <= max_width:
        return text
    while text and draw.textlength(text + '…', font=font) > max_width:
        text = text[:-1]
    return (text + '…') if text else ''


def _clean_signature(signature: Any) -> str:
    text = str(signature or '').strip()
    if not text or 'hex=' in text.lower() or text.startswith('<'):
        return ''
    return ' '.join(text.split())


def _clean_name(name: Any) -> str:
    text = str(name or '').strip()
    if not text:
        return '神秘玩家'
    return ' '.join(text.split())


def _count(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


async def _download_image(
    client: httpx.AsyncClient, url: str, retries: int = 1
) -> Optional[Image.Image]:
    """下载图片，失败重试一次（并发多张时偶发断连）"""
    if not url:
        return None
    last_error = ''
    for attempt in range(retries + 1):
        try:
            resp = await client.get(url)
            if resp.status_code == 200 and resp.content:
                return Image.open(io.BytesIO(resp.content)).convert('RGBA')
            last_error = f'HTTP {resp.status_code}'
        except Exception as e:
            last_error = str(e)
        if attempt < retries:
            await asyncio.sleep(0.4)
    logger.debug(f'[RocomUID] 排行图片下载失败 {url}: {last_error}')
    return None


def _asset_id(value: Any) -> str:
    try:
        asset_id = str(int(value))
    except (TypeError, ValueError):
        return ''
    return '' if asset_id == '0' else asset_id


async def _load_row_images(
    client: httpx.AsyncClient,
    row: Dict[str, Any],
    url_cache: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[Image.Image], Optional[Image.Image]]:
    """返回 (头像, 名片皮肤背景)；url_cache 用于同一次出图内复用下载"""
    avatar_id = _asset_id(row.get('card_icon_selected'))
    skin_id = _asset_id(row.get('card_skin_selected'))

    skin_url = ''
    if skin_id:
        skin_asset = await wegame_api.get_profile_asset('card_skin', skin_id)
        if isinstance(skin_asset, dict):
            skin_url = str(
                skin_asset.get('preview_image') or skin_asset.get('icon') or ''
            )

    avatar_url = f'{WIKI_ASSET_BASE}/avatar/{avatar_id}.png' if avatar_id else ''

    async def fetch(url: str):
        if not url:
            return None
        if url_cache is None:
            return await _download_image(client, url)
        if url not in url_cache:
            url_cache[url] = asyncio.ensure_future(_download_image(client, url))
        return await url_cache[url]

    avatar, skin = await asyncio.gather(fetch(avatar_url), fetch(skin_url))
    return avatar, skin


def _draw_shadow(
    img: Image.Image, box: Tuple[int, int, int, int], radius: int
) -> None:
    left, top, right, bottom = box
    shadow = Image.new('RGBA', (right - left + 40, bottom - top + 40), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [20, 20, right - left + 20, bottom - top + 20],
        radius=radius,
        fill=(120, 96, 62, 46),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    img.alpha_composite(shadow, (left - 20, top - 20 + 5))


def _draw_badge(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    rank: int,
) -> None:
    """名次徽章"""
    x, y = xy
    text = f'#{rank}' if rank > 0 else '未上榜'
    text_w = draw.textlength(text, font=rc_font_22)
    width = int(text_w) + 30
    height = 32
    color = RANK_BADGE_COLOR.get(rank, RANK_BADGE_DEFAULT)
    draw.rounded_rectangle(
        [x, y, x + width, y + height],
        radius=height // 2,
        fill=(*color, 255),
    )
    draw.text(
        (x + width / 2, y + height / 2 - 1),
        text,
        (255, 255, 255),
        rc_font_22,
        'mm',
        stroke_width=2,
        stroke_fill=(0, 0, 0, 90),
    )


def _draw_count_pill(
    draw: ImageDraw.ImageDraw,
    card_img: Image.Image,
    *,
    right: int,
    center_y: int,
    glass: int,
    shining: int,
) -> None:
    """右上角的炫彩 / 异色数量胶囊"""
    entries = [(ICON_GLASS, str(glass)), (ICON_SHINING, str(shining))]
    icon_size = 26
    gap_icon_text = 3
    gap_entry = 14
    pad_x = 12
    height = 38

    widths = []
    for _, text in entries:
        widths.append(icon_size + gap_icon_text + int(draw.textlength(text, font=rc_font_22)))
    total_w = pad_x * 2 + sum(widths) + gap_entry * (len(entries) - 1)

    left = right - total_w
    top = center_y - height // 2
    draw.rounded_rectangle(
        [left, top, right, top + height],
        radius=height // 2,
        fill=(24, 24, 30, 150),
    )

    cursor = left + pad_x
    for (icon, text), width in zip(entries, widths):
        icon_img = icon.resize((icon_size, icon_size), Image.LANCZOS)
        card_img.alpha_composite(
            icon_img, (int(cursor), int(center_y - icon_size / 2))
        )
        draw.text(
            (cursor + icon_size + gap_icon_text, center_y),
            text,
            (255, 255, 255),
            rc_font_22,
            'lm',
        )
        cursor += width + gap_entry


def _draw_row(
    img: Image.Image,
    row: Dict[str, Any],
    *,
    rank: int,
    top: int,
    avatar: Optional[Image.Image],
    skin: Optional[Image.Image],
    highlight: bool = False,
) -> None:
    draw = ImageDraw.Draw(img)
    box = (CARD_X, top, CARD_X + CARD_W, top + CARD_H)
    _draw_shadow(img, box, CARD_RADIUS)

    card = Image.new('RGBA', (CARD_W, CARD_H), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card)
    card_draw.rounded_rectangle(
        [0, 0, CARD_W - 1, CARD_H - 1], radius=CARD_RADIUS, fill=(*COLOR_CARD, 255)
    )

    # 名片皮肤背景（
    if skin is not None:
        banner = _cover(skin, (CARD_W, BANNER_H)).convert('RGBA')
        card.alpha_composite(banner, (0, 0))
    else:
        fallback = RANK_BADGE_COLOR.get(rank, (128, 140, 156))
        card_draw.rectangle([0, 0, CARD_W, BANNER_H], fill=(*fallback, 255))

    # 左侧压暗
    shade = Image.new('RGBA', (460, BANNER_H), (0, 0, 0, 0))
    shade_draw = ImageDraw.Draw(shade)
    for x in range(460):
        alpha = int(96 * (1 - x / 460) ** 1.4)
        shade_draw.line([(x, 0), (x, BANNER_H)], fill=(0, 0, 0, alpha))
    card.alpha_composite(shade, (0, 0))

    # 底部签名区域
    card_draw.rectangle([0, BANNER_H, CARD_W, CARD_H], fill=(*COLOR_CARD, 255))

    card.putalpha(_rounded_mask((CARD_W, CARD_H), CARD_RADIUS))
    img.alpha_composite(card, (CARD_X, top))

    draw = ImageDraw.Draw(img)
    if highlight:
        draw.rounded_rectangle(
            [CARD_X, top, CARD_X + CARD_W - 1, top + CARD_H - 1],
            radius=CARD_RADIUS,
            outline=(226, 176, 78, 255),
            width=3,
        )

    # 头像
    avatar_img = avatar if avatar is not None else DEFAULT_AVATAR
    avatar_img = _fit(avatar_img, (AVATAR_SIZE, AVATAR_SIZE))
    img.alpha_composite(
        avatar_img,
        (CARD_X + 2, top + (CARD_H - avatar_img.height) // 2 + 8),
    )

    _draw_badge(draw, (CARD_X + 16, top + 12), rank)

    text_x = CARD_X + 152
    name = _truncate(draw, _clean_name(row.get('player_name')), rc_font_28, 330)
    draw.text(
        (text_x, top + BANNER_H // 2 + 6),
        name,
        (255, 255, 255),
        rc_font_28,
        'lm',
        stroke_width=3,
        stroke_fill=(0, 0, 0, 150),
    )

    signature = _clean_signature(row.get('card_signature'))
    signature_color = COLOR_SIGN
    if not signature:
        signature = EMPTY_SIGNATURE
        signature_color = COLOR_EMPTY_SIGN
    signature = _truncate(draw, signature, rc_font_22, CARD_W - 160)
    draw.text(
        (text_x, top + BANNER_H + (CARD_H - BANNER_H) // 2),
        signature,
        signature_color,
        rc_font_22,
        'lm',
    )

    _draw_count_pill(
        draw,
        img,
        right=CARD_X + CARD_W - 16,
        center_y=top + BANNER_H // 2 + 4,
        glass=_count(row.get('collected_glass_pet_count')),
        shining=_count(row.get('collected_shining_pet_count')),
    )


async def _load_images(
    client: httpx.AsyncClient, rows: List[Dict[str, Any]]
) -> List[Tuple[Optional[Image.Image], Optional[Image.Image]]]:
    """并发加载头像/名片；同一张图只下载一次"""
    url_cache: Dict[str, Any] = {}
    return list(
        await asyncio.gather(
            *(_load_row_images(client, row, url_cache) for row in rows)
        )
    )


async def draw_pet_rank(
    rank_type: str,
    items: List[Dict[str, Any]],
    currents: Optional[List[Dict[str, Any]]] = None,
    total: int = 0,
    missing_uids: Optional[List[str]] = None,
) -> bytes:
    """渲染炫彩/异色排行榜"""
    meta = RANK_META.get(rank_type, RANK_META['glass'])
    rows = [row for row in items if isinstance(row, dict)]

    current_rows = [row for row in (currents or []) if isinstance(row, dict)]
    current_rows.sort(key=lambda row: _count(row.get('rank')) or 10**9)
    missing = [str(uid) for uid in (missing_uids or []) if uid]

    async with httpx.AsyncClient(timeout=20.0) as client:
        assets = await _load_images(client, [*rows, *current_rows])
    row_assets = assets[: len(rows)]
    current_assets = assets[len(rows) :]

    title_h = 108
    rows_area = len(rows) * (CARD_H + CARD_GAP) if rows else 120
    current_area = 0
    if current_rows:
        current_area = 46 + len(current_rows) * (CARD_H + CARD_GAP)
    if missing:
        current_area += 34

    footer = get_footer_w(FOOTER_SOURCE, 640)
    page_h = title_h + rows_area + current_area + 20 + footer.height + 16

    # 背景
    img = Image.new('RGBA', (PAGE_W, page_h), (250, 244, 231, 255))
    top_color = (252, 247, 236)
    bottom_color = (241, 229, 205)
    gradient = Image.new('RGBA', (1, page_h))
    for y in range(page_h):
        ratio = y / max(1, page_h - 1)
        gradient.putpixel(
            (0, y),
            (
                round(top_color[0] + (bottom_color[0] - top_color[0]) * ratio),
                round(top_color[1] + (bottom_color[1] - top_color[1]) * ratio),
                round(top_color[2] + (bottom_color[2] - top_color[2]) * ratio),
                255,
            ),
        )
    img.alpha_composite(gradient.resize((PAGE_W, page_h)))

    draw = ImageDraw.Draw(img)

    # 标题
    title = meta['title']
    icon = meta['icon'].resize((44, 44), Image.LANCZOS)
    title_w = draw.textlength(title, font=rc_font_42)
    total_w = title_w + 54
    start_x = (PAGE_W - total_w) / 2
    img.alpha_composite(icon, (int(start_x), 22))
    draw.text(
        (start_x + 54, 46),
        title,
        COLOR_TITLE,
        rc_font_42,
        'lm',
    )
    sub_text = f'TOP {len(rows)}  ·  全服共 {total} 位玩家'
    draw.text(
        (PAGE_W / 2, 86),
        sub_text,
        COLOR_SUB,
        rc_font_18,
        'mm',
    )

    # 榜单
    cursor_y = title_h
    if rows:
        for index, (row, (avatar, skin)) in enumerate(
            zip(rows, row_assets), start=1
        ):
            _draw_row(
                img,
                row,
                rank=_count(row.get('rank')) or index,
                top=cursor_y,
                avatar=avatar,
                skin=skin,
            )
            cursor_y += CARD_H + CARD_GAP
    else:
        draw.text(
            (PAGE_W / 2, cursor_y + 60),
            '暂时还没有收集记录，快来成为第一个吧~',
            COLOR_SIGN,
            rc_font_24,
            'mm',
        )
        cursor_y += 120

    # 自己绑定的 UID 排名
    if current_rows:
        cursor_y += 8
        draw.line(
            [(CARD_X + 10, cursor_y), (CARD_X + CARD_W - 10, cursor_y)],
            fill=COLOR_DIVIDER,
            width=2,
        )
        draw.text(
            (CARD_X + 4, cursor_y + 22),
            '我的排名',
            COLOR_TITLE,
            rc_font_20,
            'lm',
        )
        row_top = cursor_y + 46
        for row, (avatar, skin) in zip(current_rows, current_assets):
            _draw_row(
                img,
                row,
                rank=_count(row.get('rank')),
                top=row_top,
                avatar=avatar,
                skin=skin,
                highlight=True,
            )
            row_top += CARD_H + CARD_GAP
        cursor_y = row_top

    if missing:
        hint = _truncate(
            draw,
            f'UID {"、".join(missing)} 暂未收录收集记录',
            rc_font_20,
            CARD_W - 20,
        )
        draw.text(
            (PAGE_W / 2, cursor_y + 17),
            hint,
            COLOR_SIGN,
            rc_font_20,
            'mm',
        )
        cursor_y += 34

    # 页脚
    footer_y = page_h - footer.height - 16
    img.alpha_composite(footer, ((PAGE_W - footer.width) // 2, footer_y))

    return await convert_img(img.convert('RGB'))
