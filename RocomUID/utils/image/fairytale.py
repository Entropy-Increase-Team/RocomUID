"""童话/拼贴风格的可复用绘图基元。

全部基于 PIL，无需额外资源文件。供「查蛋」与日后「远行商人」等功能共用，
统一奶油纸底 + 白边贴纸 + 手绘卡片 + 倾斜拼贴的视觉语言。
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from ..fonts.rocom_fonts import dundun_font_origin, skill_font_origin

# 童话风格配色
PAPER_TOP = (255, 248, 236)      # 奶油色（偏上）
PAPER_BOTTOM = (250, 238, 222)   # 奶油色（偏下，做轻微渐变）
INK = (96, 84, 66)               # 暖棕主文字色
WHITE = (255, 255, 255, 255)
SHADOW = (120, 100, 78)          # 阴影底色


def _vertical_gradient(w: int, h: int, top, bottom) -> Image.Image:
    """生成竖向渐变底色。"""
    base = Image.new('RGB', (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        base.putpixel(
            (0, y),
            (
                int(top[0] + (bottom[0] - top[0]) * t),
                int(top[1] + (bottom[1] - top[1]) * t),
                int(top[2] + (bottom[2] - top[2]) * t),
            ),
        )
    return base.resize((w, h))


def make_paper_bg(w: int, h: int, top=PAPER_TOP, bottom=PAPER_BOTTOM) -> Image.Image:
    """纸底：竖向渐变 + 轻噪点 + 四角暗角，营造手绘纸张质感（默认奶油色，可传色）。"""
    img = _vertical_gradient(w, h, top, bottom).convert('RGBA')

    # 轻噪点（低透明度叠加），让纯色底显得像纸。
    # effect_noise 是全画布开销大头，在半尺寸生成再放大≈省 3/4 面积；
    # 16% 透明的纸纹放大后肉眼无差。
    nw, nh = max(1, w // 2), max(1, h // 2)
    noise = Image.effect_noise((nw, nh), 14).point(lambda v: int(abs(v - 128) * 0.16))
    noise_rgba = Image.new('RGBA', (w, h), (255, 255, 255, 0))
    noise_rgba.putalpha(noise.resize((w, h), Image.BILINEAR))
    img = Image.alpha_composite(img, noise_rgba)

    # 四角暗角：径向式柔光遮罩（在 1/3 缩略图上做大半径模糊，省时）
    margin = int(min(w, h) * 0.12)
    sw, sh = max(1, w // 3), max(1, h // 3)
    vignette = Image.new('L', (sw, sh), 0)
    m3 = max(1, margin // 3)
    ImageDraw.Draw(vignette).rounded_rectangle(
        (m3, m3, sw - m3, sh - m3), radius=m3, fill=255,
    )
    vignette = vignette.filter(ImageFilter.GaussianBlur(m3)).resize((w, h))
    dark = Image.new('RGBA', (w, h), (210, 196, 176, 60))
    img = Image.composite(img, Image.alpha_composite(img, dark), vignette)

    return img


def sticker(
    img: Image.Image,
    border: int = 12,
    border_color=(255, 255, 255, 255),
    shadow: bool = True,
) -> Image.Image:
    """白边贴纸效果：沿透明图形剪影膨胀出白色描边，并在下方加柔和投影。

    返回的画布比原图四周各扩 (border + 投影余量) 像素。
    """
    img = img.convert('RGBA')
    w, h = img.size
    pad = border + (10 if shadow else 4)
    canvas = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))

    alpha = img.split()[3]
    # 膨胀 alpha 得到比原剪影更胖的轮廓
    kernel = border * 2 + 1
    dilated = alpha.filter(ImageFilter.MaxFilter(kernel if kernel <= 255 else 255))

    if shadow:
        shadow_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        shadow_mask = dilated.point(lambda v: int(v * 0.45))
        shadow_solid = Image.new('RGBA', (w, h), (*SHADOW, 255))
        shadow_layer.paste(shadow_solid, (pad + 4, pad + 8), shadow_mask)
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(6))
        canvas = Image.alpha_composite(canvas, shadow_layer)

    # 白色描边层
    white_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    white_solid = Image.new('RGBA', (w, h), border_color)
    white_layer.paste(white_solid, (pad, pad), dilated)
    canvas = Image.alpha_composite(canvas, white_layer)

    # 贴上原图
    canvas.alpha_composite(img, (pad, pad))
    return canvas


def tint(img: Image.Image, color) -> Image.Image:
    """把整图染成 color（保留原 alpha 与边缘羽化），用于深色字图换浅色。"""
    img = img.convert('RGBA')
    solid = Image.new('RGBA', img.size, (*color, 255))
    solid.putalpha(img.split()[3])
    return solid


def wobbly_card(
    w: int,
    h: int,
    fill=(255, 255, 255, 235),
    outline=(255, 255, 255, 255),
    radius: int = 28,
    border_w: int = 6,
    shadow: bool = True,
) -> Image.Image:
    """圆角 + 粗白描边的手绘卡片底，可带柔和投影。"""
    pad = 12 if shadow else border_w
    canvas = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))

    if shadow:
        shadow_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        sd.rounded_rectangle(
            (pad + 3, pad + 6, pad + w + 3, pad + h + 6),
            radius=radius,
            fill=(*SHADOW, 70),
        )
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(7))
        canvas = Image.alpha_composite(canvas, shadow_layer)

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (pad, pad, pad + w, pad + h),
        radius=radius,
        fill=fill,
        outline=outline,
        width=border_w,
    )
    return canvas


def title_pill(
    text: str,
    font,
    fg=(255, 255, 255, 255),
    bg=(255, 173, 120, 255),
    pad_x: int = 26,
    pad_y: int = 12,
    border_color=(255, 255, 255, 255),
    border_w: int = 5,
) -> Image.Image:
    """圆角胶囊标签（带白边），用于标题与「高度/重量/类型」条件项。"""
    tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    box = tmp.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]

    w = tw + pad_x * 2
    h = th + pad_y * 2
    margin = 14
    canvas = Image.new('RGBA', (w + margin * 2, h + margin * 2), (0, 0, 0, 0))

    # 投影
    shadow_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)
    sd.rounded_rectangle(
        (margin + 2, margin + 5, margin + w + 2, margin + h + 5),
        radius=h // 2,
        fill=(*SHADOW, 70),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(6))
    canvas = Image.alpha_composite(canvas, shadow_layer)

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (margin, margin, margin + w, margin + h),
        radius=h // 2,
        fill=bg,
        outline=border_color,
        width=border_w,
    )
    draw.text(
        (margin + w // 2, margin + h // 2),
        text,
        font=font,
        fill=fg,
        anchor='mm',
    )
    return canvas


def tilt(img: Image.Image, angle: float) -> Image.Image:
    """轻微旋转（保留透明背景并扩展画布），制造拼贴随性感。"""
    return img.convert('RGBA').rotate(angle, expand=True, resample=Image.BICUBIC)


def paste_center(bg: Image.Image, fg: Image.Image, cx: int, cy: int) -> None:
    """以 (cx, cy) 为中心把 fg 贴到 bg 上（原地修改 bg）。"""
    x = cx - fg.size[0] // 2
    y = cy - fg.size[1] // 2
    bg.alpha_composite(fg.convert('RGBA'), (x, y))


def outline_text(
    draw: ImageDraw.ImageDraw,
    xy,
    text: str,
    font,
    fill=INK,
    anchor='mm',
    stroke_width: int = 4,
    stroke_fill=(255, 255, 255, 255),
) -> None:
    """白边描边文字（与贴纸/卡片白边统一），原地画到 draw 上。"""
    draw.text(
        xy, text, font=font, fill=fill, anchor=anchor,
        stroke_width=stroke_width, stroke_fill=stroke_fill,
    )


# ---- 混合可爱字体：顿顿体为主，缺字回退 skill ----
_pair_cache = {}


def font_pair(size: int):
    if size not in _pair_cache:
        _pair_cache[size] = (dundun_font_origin(size), skill_font_origin(size))
    return _pair_cache[size]


_runs_cache = {}


def _cute_runs(text: str, size: int):
    # 同字串同字号的逐字字体回退判断是确定的，缓存复用（调用方只读不改）
    key = (text, size)
    cached = _runs_cache.get(key)
    if cached is not None:
        return cached
    rc, fb = font_pair(size)
    runs = []
    for ch in text:
        use = rc if (ch == ' ' or rc.getmask(ch).getbbox()) else fb
        runs.append((ch, use, use.getlength(ch)))
    _runs_cache[key] = runs
    return runs


def cute_width(text: str, size: int) -> float:
    return sum(w for _, _, w in _cute_runs(text, size))


def draw_cute(draw, xy, text: str, size: int, fill, anchor: str = 'lm',
              stroke_width: int = 0, stroke_fill=None) -> None:
    """逐字混合字体绘制：顿顿体为主，缺字（标点/生僻字）逐字回退 skill。

    anchor 支持 l/m 水平 + 垂直居中。可选 stroke_width/stroke_fill 描边；
    描边与字面分两遍画，避免相邻字的描边盖住前一字的字面。
    """
    runs = _cute_runs(text, size)
    total = sum(w for _, _, w in runs)
    x, y = xy
    if anchor and anchor[0] == 'm':
        x -= total / 2
    if stroke_width and stroke_fill is not None:
        sx = x
        for ch, fnt, w in runs:
            draw.text((sx, y), ch, font=fnt, fill=stroke_fill, anchor='lm',
                      stroke_width=stroke_width, stroke_fill=stroke_fill)
            sx += w
    for ch, fnt, w in runs:
        draw.text((x, y), ch, font=fnt, fill=fill, anchor='lm')
        x += w


# ---- 卡形状缓存与随机取用 ----
_shape_cache = {}        # 源图：路径 → 原始 RGBA
_shape_result_cache = {}  # 九宫格结果：(路径, w, h) → 拉伸后卡底


def card_shape(tier: str, w: int, h: int, tex_dir, shape_files: dict, seed: int = 0):
    """按 tier 取一种随机卡形状(从 tex_dir 读取对应文件)，九宫格拉伸到 (w,h)。

    左右边距大、上下小以保住尖角/票券形状；缺图回退圆角白边卡。
    同尺寸同形状的九宫格结果缓存复用，命中返回副本（调用方会在卡底上贴字/图标）。
    """
    tex_dir = Path(tex_dir)
    files = shape_files.get(tier) or next(iter(shape_files.values()))
    imgs, keys = [], []
    for name in files:
        key = str(tex_dir / name)
        if key not in _shape_cache:
            p = tex_dir / name
            _shape_cache[key] = Image.open(p).convert('RGBA') if p.exists() else None
        if _shape_cache[key] is not None:
            imgs.append(_shape_cache[key])
            keys.append(key)
    if imgs:
        i = seed % len(imgs)
        rk = (keys[i], w, h)
        if rk not in _shape_result_cache:
            _shape_result_cache[rk] = nine_slice(imgs[i], 56, 30, 56, 30, w, h)
        return _shape_result_cache[rk].copy()
    return wobbly_card(w, h, fill=(200, 200, 220, 255), radius=24, border_w=8, shadow=False)


def nine_slice(
    img: Image.Image,
    left: int,
    top: int,
    right: int,
    bottom: int,
    w: int,
    h: int,
) -> Image.Image:
    """九宫格拉伸：四角固定、四边与中心拉伸，把 img 适配到 (w, h)。

    left/top/right/bottom 为四个边角的固定边距（像素）。
    """
    img = img.convert('RGBA')
    sw, sh = img.size
    w = max(w, left + right + 1)
    h = max(h, top + bottom + 1)

    # 源九宫格切片边界
    sx = [0, left, sw - right, sw]
    sy = [0, top, sh - bottom, sh]
    # 目标九宫格边界
    dx = [0, left, w - right, w]
    dy = [0, top, h - bottom, h]

    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for i in range(3):
        for j in range(3):
            piece = img.crop((sx[i], sy[j], sx[i + 1], sy[j + 1]))
            tw, th = dx[i + 1] - dx[i], dy[j + 1] - dy[j]
            if tw <= 0 or th <= 0:
                continue
            if piece.size != (tw, th):
                piece = piece.resize((tw, th), Image.BICUBIC)
            out.alpha_composite(piece, (dx[i], dy[j]))
    return out
