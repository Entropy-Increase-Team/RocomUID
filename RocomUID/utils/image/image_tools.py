from pathlib import Path
from PIL import Image
import textwrap

TEXT_PATH = Path(__file__).parent / "texture2d"
ICON = TEXT_PATH / "ICON.png"

# ---------------------------------------------------------------------------
# 统一页脚素材：
#   footer.png          460x29  Power by GsCore And copyright by 洛克王国
#   footer_source.png   780x29  上者 + And Source by 洛克魔法书
# ---------------------------------------------------------------------------
FOOTER_HELP = "footer_help.png"
FOOTER = "footer.png"
FOOTER_SOURCE = "footer_source.png"

_footer_cache = {}

async def get_text_line(content, num):
    content_line = []
    text_list = content.split('\n')
    for text in text_list:
        para = textwrap.wrap(text, width=num)
        for line in para:
            content_line.append(line)
    return content_line

def get_footer(name: str = FOOTER) -> Image.Image:
    """读取统一页脚素材（默认主用页脚 footer.png）。

    返回的是独立副本，调用方可自由缩放/染色而不影响其它渲染。
    """
    if name not in _footer_cache:
        path = TEXT_PATH / name
        if not path.exists():
            raise FileNotFoundError(f"[RocomUID] 缺少页脚素材: {path}")
        with Image.open(path) as src:  # 显式关闭句柄，避免 Windows 下文件被占用
            _footer_cache[name] = src.convert("RGBA")
    return _footer_cache[name].copy()


def get_footer_w(name: str = FOOTER, width: int = 0) -> Image.Image:
    """读取统一页脚素材并按 width 等比缩放（width=0 表示用素材原始尺寸）。"""
    footer = get_footer(name)
    if width and width != footer.width:
        footer = footer.resize(
            (width, max(1, round(footer.height * width / footer.width))),
            Image.LANCZOS,
        )
    return footer


def add_footer(img: Image.Image, w: int = 0) -> Image.Image:
    w = img.size[0] if not w else w
    footer = get_footer_w(FOOTER_HELP, w)
    x, y = (
        int((img.size[0] - footer.size[0]) / 2),
        img.size[1] - footer.size[1] - 10,
    )
    img.paste(footer, (x, y), footer)
    return img

def get_ICON():
    return Image.open(ICON)