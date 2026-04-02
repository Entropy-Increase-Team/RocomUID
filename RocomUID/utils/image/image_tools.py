from pathlib import Path
from PIL import Image
import textwrap

TEXT_PATH = Path(__file__).parent / "texture2d"
ICON = TEXT_PATH / "ICON.png"

async def get_text_line(content, num):
    content_line = []
    text_list = content.split('\n')
    for text in text_list:
        para = textwrap.wrap(text, width=num)
        for line in para:
            content_line.append(line)
    return content_line

def get_footer():
    return Image.open(TEXT_PATH / "footer.png")

def add_footer(img: Image.Image, w: int = 0) -> Image.Image:
    footer = get_footer()
    w = img.size[0] if not w else w
    if w != footer.size[0]:
        footer = footer.resize(
            (w, int(footer.size[1] * w / footer.size[0])),
        )
    x, y = (
        int((img.size[0] - footer.size[0]) / 2),
        img.size[1] - footer.size[1] - 10,
    )
    img.paste(footer, (x, y), footer)
    return img

def get_ICON():
    return Image.open(ICON)