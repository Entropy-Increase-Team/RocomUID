import re
import math
from pathlib import Path
import pytz
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageChops
from gsuid_core.utils.image.convert import convert_img
from ..utils.fonts.rocom_fonts import rc_font_40, skill_font_18, skill_font_26
from gsuid_core.utils.image.image_tools import get_pic

TEXT_PATH = Path(__file__).parent / 'texture2D'
badge = Image.open(TEXT_PATH / 'badge.png')
banner = Image.open(TEXT_PATH / 'banner.png')
susume = Image.open(TEXT_PATH / 'susume.png')
footer = Image.open(TEXT_PATH / 'footer.png')

lunci_list = [
    ['1', 8, 11],
    ['2', 12, 15],
    ['3', 16, 19],
    ['4', 20, 23]
]

async def draw_merchant_info(merchant_info):
    img = Image.open(TEXT_PATH / 'bg.jpg').convert('RGB')
    img.paste(banner, (196, 252), banner)
    img_draw = ImageDraw.Draw(img)
    prop_num = len(merchant_info)
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    this_hour = now.hour
    this_minute = now.minute
    lunci = '1'
    lunci_index = 0
    for item in lunci_list:
        if this_hour >= item[1] and this_hour <= item[2]:
            lunci = item[0]
            lunci_index = int(item[0]) - 1
            break
    
    last_hour = lunci_list[lunci_index][2] - this_hour
    last_min = 59 - this_minute
    last_time = ''
    if last_hour > 0:
        last_time += f"{last_hour}时"
    if last_min > 0:
        last_time += f"{last_min}分"
    
    img_draw.text(
        (285, 270),
        f'当前商品 {prop_num}',
        (255, 255, 255),
        skill_font_26,
        'mm',
    )
    
    img_draw.text(
        (500, 270),
        f'第 {lunci}/4 轮',
        (255, 255, 255),
        skill_font_26,
        'mm',
    )
    
    img_draw.text(
        (706, 270),
        f'剩余 {last_time}',
        (255, 255, 255),
        skill_font_26,
        'mm',
    )
    start_height = 277
    for shul, prop_item in enumerate(merchant_info):
        rc_y = math.floor(shul / 2)
        rc_x = shul - (2 * rc_y)
        prop_img = Image.new('RGBA', (512, 256), (255, 255, 255, 0))
        prop_img.paste(badge, (0, 0), badge)
        prop_icon = await get_pic(prop_item['image'])
        width = prop_icon.size[0]  # 获取图片宽度
        height = prop_icon.size[1]  # 获取图片高度
        if width >= height:
            beilv = 145/width
            height = int(height * beilv)
            width = 145
        else:
            beilv = 145/height
            width = int(width * beilv)
            height = 145
        prop_icon = prop_icon.resize((width, height))
        icon_x = 131 - int(width / 2)
        icon_y = 128 - int(height / 2)
        
        prop_img.paste(prop_icon, (icon_x, icon_y), prop_icon)
        prop_draw = ImageDraw.Draw(prop_img)
        prop_draw.text(
            (210, 116),
            f"{prop_item['name']}",
            (255, 255, 63),
            rc_font_40,
            'lm',
        )
        
        prop_draw.text(
            (210, 152),
            f"{prop_item['starttime']} ~ {prop_item['endtime']}",
            (198, 222, 246),
            skill_font_18,
            'lm',
        )
        
        if prop_item['name'] in ['炫彩精灵蛋', '棱镜球', '国王球']:
            prop_img.paste(susume, (371, 37), susume)
        img.paste(prop_img, (453 * rc_x + 14, rc_y * 206 + start_height), prop_img)
    img.paste(footer, (277, 941), footer)
    res = await convert_img(img)
    return res