import re
import math
from pathlib import Path
import pytz
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageChops
from gsuid_core.utils.image.convert import convert_img
from ..utils.resource.RESOURCE_PATH import ROCOM_HEAD_PATH
from ..utils.fonts.rocom_fonts import rc_font_22, rc_font_26, rc_font_28, rc_font_30, rc_font_35, skill_font_38, skill_font_42, skill_font_46
from gsuid_core.utils.image.image_tools import get_pic
from gsuid_core.utils.image.image_tools import (
    draw_pic_with_ring,
    get_qq_avatar,
)

TEXT_PATH = Path(__file__).parent / 'texture2D'
top_bg = Image.open(TEXT_PATH / 'top_bg.png')
touxiang_mask = Image.open(TEXT_PATH / 'touxiang_mask.png')
rocom_title = Image.open(TEXT_PATH / 'a_title.png')
title_fg = Image.open(TEXT_PATH / 'title_fg.png')
banner_bg = Image.open(TEXT_PATH / 'banner_bg.png')
pet_bg = Image.open(TEXT_PATH / 'pet_bg.png')
plant_bg = Image.open(TEXT_PATH / 'plant_bg.png')
footer = Image.open(TEXT_PATH / 'footer.png')
info_text_color = (66, 66, 66)

async def draw_home_info(ev, uid, home_info):
    bg_height = 410
    pet_list_height = math.ceil(len(home_info['home_pets']) / 2) * 192
    if pet_list_height > 0:
        bg_height = bg_height + 120 + pet_list_height
    plant_list_height = math.ceil(len(home_info['home_plants']) / 3) * 148
    if plant_list_height > 0:
        bg_height = bg_height + 120 + plant_list_height
    
    img = Image.open(TEXT_PATH / 'bg.jpg').convert('RGB')
    if bg_height > 2417:
        img = img.resize((1000, bg_height))
    else:
        img = img.crop((0, 0, 1000, bg_height))
    
    img.paste(top_bg, (0, 0), top_bg)
    img.paste(title_fg, (0, 0), title_fg)
    
    #画头像
    if ev.sender.get("avatar", '') != '':
        char_pic = await get_qq_avatar(avatar_url=ev.sender["avatar"])
        char_pic = await draw_pic_with_ring(char_pic, 152, None, False)
    else:
        char_pic = Image.open(TEXT_PATH / 'img_head.png')
    img.paste(char_pic, (31, 28), char_pic)
    
    img_draw = ImageDraw.Draw(img)
    img_draw.text(
        (200, 110),
        f"{home_info['home_name']}的小屋",
        (255, 255, 255),
        skill_font_46,
        'lm',
    )
    img_draw.text(
        (200, 155),
        f'学号 {uid}',
        (255, 255, 255),
        skill_font_38,
        'lm',
    )
    
    #画家园信息
    img.paste(banner_bg, (0, 228), banner_bg)
    img_draw.text(
        (219, 282),
        f"{home_info['room_level']}",
        (0, 0, 0),
        skill_font_42,
        'mm',
    )
    
    img_draw.text(
        (407, 282),
        f"{home_info['home_level']}",
        (0, 0, 0),
        skill_font_42,
        'mm',
    )
    
    if home_info['home_experience'] > 100000:
        home_experience = round(home_info['home_experience'] / 10000, 2)
        img_draw.text(
            (596, 282),
            f'{home_experience}w',
            (0, 0, 0),
            skill_font_42,
            'mm',
        )
    else:
        img_draw.text(
            (596, 282),
            f"{home_info['home_experience']}",
            (0, 0, 0),
            skill_font_42,
            'mm',
        )
    
    img_draw.text(
        (786, 282),
        f"{home_info['home_comfort_level']}",
        (0, 0, 0),
        skill_font_42,
        'mm',
    )
    start_height = 417
    now_time = int(time.time())
    if len(home_info['home_pets']) > 0:
        #画精灵信息
        img.paste(rocom_title, (48, start_height), rocom_title)
        img_draw.text(
            (114, 446),
            f'精灵信息',
            (255, 255, 255),
            rc_font_28,
            'lm',
        )
        start_height += 80
        #18 484
        for shul, pet_info in enumerate(home_info["home_pets"]):
            rc_y = math.floor(shul / 2)
            rc_x = shul - (2 * rc_y)
            pet_img = Image.new('RGBA', (486, 192), (255, 255, 255, 0))
            pet_bg_img = Image.new('RGBA', (486, 192), (110, 171, 32))
            pet_img.paste(pet_bg_img, (0, 0), pet_bg)
            
            if pet_info['mutation_type'] in [9, 1]:
                head_img = Image.open(ROCOM_HEAD_PATH / f'{pet_info["pet_id"]}_1.png').convert('RGBA').resize((150, 150))
            else:
                head_img = Image.open(ROCOM_HEAD_PATH / f'{pet_info["pet_id"]}.png').convert('RGBA').resize((150, 150))
            pet_img.paste(head_img, (24, 28), head_img)
            
            pet_draw = ImageDraw.Draw(pet_img)
            pet_draw.text(
                (166, 75),
                f'{pet_info["name"]}',
                (255, 255, 0),
                rc_font_35,
                'lm',
            )
            if pet_info['gender'] == 2:
                name_len = len(pet_info["name"]) * 40 + 15 + 166
                pet_draw.text(
                    (name_len, 77),
                    "已生蛋" if pet_info['have_egg'] else "未生蛋",
                    (255, 255, 255),
                    rc_font_30,
                    'lm',
                )
            
            if pet_info['pet_rip_time'] != 0:
                pet_rip_time = pet_info['pet_rip_time']
                jindu_tc = Image.open(TEXT_PATH / 'jindu_tc.png').convert('RGBA').resize((270, 13))
                pet_img.paste(jindu_tc, (166, 132), jindu_tc)
                if now_time >= pet_rip_time:
                    pet_draw.text(
                        (166, 109),
                        f'灵感已收集完成',
                        (255, 255, 255),
                        rc_font_28,
                        'lm',
                    )
                    jindu_len = 270
                else:
                    dt1 = datetime.utcfromtimestamp(now_time)
                    dt2 = datetime.utcfromtimestamp(pet_rip_time)
                    # 计算两个时间点之间的差异
                    delta = dt2 - dt1
                    # 提取小时和分钟
                    hours = delta.seconds // 3600
                    minutes = (delta.seconds % 3600) // 60
                    pet_draw.text(
                        (166, 109),
                        f'{hours}小时{minutes}分钟',
                        (255, 255, 255),
                        rc_font_28,
                        'lm',
                    )
                    jindu_zhanbi = (pet_info['time_cost'] - (pet_rip_time - now_time)) / pet_info['time_cost']
                    jindu_len = int(269 * jindu_zhanbi) + 1
                jindu_bar = Image.open(TEXT_PATH / 'jindu_bar.png').convert('RGBA').resize((jindu_len, 13))
                pet_img.paste(jindu_bar, (166, 132), jindu_bar)
            else:
                pet_draw.text(
                    (166, 109),
                    f'未喂食',
                    (255, 255, 255),
                    rc_font_28,
                    'lm',
                )
            
            level_img = Image.open(TEXT_PATH / f'level_icon.png').convert('RGBA')
            level_draw = ImageDraw.Draw(level_img)
            level_draw.text(
                (37, 19),
                f'Lv{pet_info["level"]}',
                (255, 255, 255),
                rc_font_22,
                'mm',
            )
            level_img = level_img.rotate(10, expand=True)
            pet_img.paste(level_img, (62, 125), level_img)
            
            img.paste(pet_img, (486 * rc_x + 18, rc_y * 192 + start_height), pet_img)
            
        start_height += (rc_y + 1) * 192 + 10
    
    if len(home_info['home_plants']) > 0:
        #画种植信息
        img.paste(rocom_title, (48, start_height), rocom_title)
        img_draw.text(
            (114, start_height + 29),
            f'种植信息',
            (255, 255, 255),
            rc_font_28,
            'lm',
        )
        start_height += 80
        #46 1173 1481
        for shul, plant_info in enumerate(home_info["home_plants"]):
            rc_y = math.floor(shul / 3)
            rc_x = shul - (3 * rc_y)
            plant_img = Image.new('RGBA', (306, 148), (255, 255, 255, 0))
            plant_rip_time = plant_info['plant_rip_time']
            plant_draw = ImageDraw.Draw(plant_img)
            if now_time >= plant_rip_time:
                plant_img.paste(plant_bg, (0, 0), plant_bg)
                plant_draw.text(
                    (131, 94),
                    f'已成熟',
                    (103, 215, 55),
                    rc_font_35,
                    'lm',
                )
            else:
                plant_bg_img = Image.new('RGBA', (306, 148), (103, 68, 198, 255))
                plant_img.paste(plant_bg_img, (0, 0), plant_bg)
                dt1 = datetime.utcfromtimestamp(now_time)
                dt2 = datetime.utcfromtimestamp(plant_rip_time)
                # 计算两个时间点之间的差异
                delta = dt2 - dt1
                # 提取小时和分钟
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                plant_draw.text(
                    (131, 81),
                    f'{hours}小时{minutes}分钟',
                    (255, 255, 255),
                    rc_font_26,
                    'lm',
                )
                
                jindu_tc = Image.open(TEXT_PATH / 'jindu_tc.png').convert('RGBA').resize((147, 13))
                plant_img.paste(jindu_tc, (130, 103), jindu_tc)
                jindu_zhanbi = ((21600 * plant_info['plant_tab_id']) - (plant_rip_time - now_time)) / (21600 * plant_info['plant_tab_id'])
                jindu_len = int(146 * jindu_zhanbi) + 1
                jindu_bar = Image.open(TEXT_PATH / 'jindu_bar.png').convert('RGBA').resize((jindu_len, 13))
                plant_img.paste(jindu_bar, (130, 103), jindu_bar)
                
            item_img = Image.open(TEXT_PATH / "home_icon" / f'{plant_info["plant_info"]["iconid"]}_2.png').convert('RGBA').resize((105, 105))
            plant_img.paste(item_img, (17, 19), item_img)
            plant_draw.text(
                (131, 45),
                f"{plant_info['plant_info']['name']}",
                (255, 255, 0),
                rc_font_35,
                'lm',
            )
            img.paste(plant_img, (306 * rc_x + 46, rc_y * 148 + start_height), plant_img)
            
            
    img.paste(footer, (270, bg_height - 44), footer) 
    res = await convert_img(img)
    return res