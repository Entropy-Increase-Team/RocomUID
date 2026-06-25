import re
import math
from pathlib import Path
import pytz
import time
import os
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageChops
from gsuid_core.utils.image.convert import convert_img
from ..utils.resource.RESOURCE_PATH import ROCOM_HEAD_PATH
from ..utils.fonts.rocom_fonts import rc_font_22, rc_font_26, rc_font_28, rc_font_30, rc_font_35, skill_font_24, skill_font_38, skill_font_42, skill_font_46
from gsuid_core.utils.image.image_tools import get_pic
from gsuid_core.utils.image.image_tools import (
    draw_pic_with_ring,
    get_qq_avatar,
)
from ..rocom_config.rocom_config import RC_CONFIG

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

def is_config_enabled(config_key: str) -> bool:
    config_value = RC_CONFIG.get_config(config_key).data
    if isinstance(config_value, bool):
        return config_value
    return str(config_value).lower() in ["true", "1", "yes", "on", "开启"]


def format_egg_countdown_text(target_time: int, now_time: int) -> str:
    remaining_seconds = max(0, target_time - now_time)
    days = remaining_seconds // 86400
    hours = (remaining_seconds % 86400) // 3600
    minutes = (remaining_seconds % 3600) // 60
    seconds = remaining_seconds % 60

    if remaining_seconds < 60:
        return f'{seconds}秒'

    day_mes = f'{days}天' if days > 0 else ''
    return f'{day_mes}{hours}时{minutes}分'

def format_egg_time_text(target_time: int, now_time: int) -> str:
    target_dt = datetime.fromtimestamp(target_time)
    now_dt = datetime.fromtimestamp(now_time)
    if target_dt.date() == now_dt.date():
        day_mes = ''
    elif target_dt.date() == (now_dt + timedelta(days=1)).date():
        day_mes = '明天'
    elif target_dt.date() == (now_dt + timedelta(days=2)).date():
        day_mes = '后天'
    else:
        day_mes = f'{target_dt.month}月{target_dt.day}日'
    return f'{day_mes}{target_dt.hour}点{target_dt.minute}分'


# 喂食状态：接口 home_pet_info.status（旧的 feed_info 计时字段已被服务端移除）
_FEED_STATUS = {1700: '未喂食', 1701: '喂养中', 1702: '可收取灵感', 1704: '空闲'}


def feed_status_text(status: int) -> str:
    """把接口 status 码映射为喂食状态文案，未知码兜底为「未喂食」。"""
    code = int(status or 0)
    return _FEED_STATUS[code] if code in _FEED_STATUS else '未喂食'

async def draw_home_info(ev, uid, home_info, show_pets: bool = True, show_plants: bool = True):
    bg_height = 460
    pet_list_height = math.ceil(len(home_info.home_pets) / 2) * 192 if show_pets else 0
    if pet_list_height > 0:
        bg_height = bg_height + 120 + pet_list_height
    plant_list_height = math.ceil(len(home_info.home_plants) / 3) * 148 if show_plants else 0
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
    if is_config_enabled("RC_home_use_qq_avatar"):
        if ev.sender.get("avatar", '') != '':
            char_pic = await get_qq_avatar(avatar_url=ev.sender["avatar"])
            char_pic = await draw_pic_with_ring(char_pic, 152, None, False)
        else:
            char_pic = Image.open(TEXT_PATH / 'img_head.png')
        img.paste(char_pic, (31, 28), char_pic)
    else:
        char_pic = Image.open(TEXT_PATH / 'img_head.png')
        img.paste(char_pic, (31, 13), char_pic)

    img_draw = ImageDraw.Draw(img)
    img_draw.text(
        (200, 110),
        f"{home_info.home_name}的小屋",
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
        f"{home_info.room_level}",
        (0, 0, 0),
        skill_font_42,
        'mm',
    )

    img_draw.text(
        (407, 282),
        f"{home_info.home_level}",
        (0, 0, 0),
        skill_font_42,
        'mm',
    )

    if home_info.home_experience > 100000:
        home_experience = round(home_info.home_experience / 10000, 2)
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
            f"{home_info.home_experience}",
            (0, 0, 0),
            skill_font_42,
            'mm',
        )

    img_draw.text(
        (786, 282),
        f"{home_info.home_comfort_level}",
        (0, 0, 0),
        skill_font_42,
        'mm',
    )
    start_height = 417
    now_time = int(time.time())
    if show_pets and len(home_info.home_pets) > 0:
        #画精灵信息
        img.paste(rocom_title, (48, start_height), rocom_title)
        img_draw.text(
            (114, start_height + 29),
            f'精灵信息',
            (255, 255, 255),
            rc_font_28,
            'lm',
        )
        start_height += 80
        #18 484
        for shul, pet_info in enumerate(home_info.home_pets):
            rc_y = math.floor(shul / 2)
            rc_x = shul - (2 * rc_y)
            pet_img = Image.new('RGBA', (486, 192), (255, 255, 255, 0))
            pet_bg_img = Image.new('RGBA', (486, 192), (110, 171, 32))
            pet_img.paste(pet_bg, (0, 0), pet_bg)

            if pet_info.mutation_type in [9, 1]:
                pet_head_icon = ROCOM_HEAD_PATH / f'{pet_info.pet_id}_1.png'
            else:
                pet_head_icon = ROCOM_HEAD_PATH / f'{pet_info.pet_id}.png'
            if not os.path.exists(pet_head_icon):
                pet_head_icon = ROCOM_HEAD_PATH / '3004.png'
            head_img = Image.open(pet_head_icon).convert('RGBA').resize((130, 130))
            pet_img.paste(head_img, (24, 28), head_img)

            if pet_info.mutation_type in [1, 8, 9]:
                star_img = Image.open(TEXT_PATH / f'star_{pet_info.mutation_type}.png').convert('RGBA').resize((70, 70))
                pet_img.paste(star_img, (21, 8), star_img)

            pet_draw = ImageDraw.Draw(pet_img)
            pet_draw.text(
                (166, 75),
                f'{pet_info.name}',
                (255, 255, 0),
                rc_font_35,
                'lm',
            )
            predicted_egg_time = int(getattr(pet_info, 'predicted_egg_time', 0) or 0)
            has_egg_prediction = pet_info.gender == 2 and predicted_egg_time > 0
            has_predicted_egg_time = has_egg_prediction and predicted_egg_time > now_time
            pet_status_y = 136 if has_predicted_egg_time else 109
            progress_bar_y = 159 if has_predicted_egg_time else 132
            if pet_info.gender == 2:
                name_right = pet_draw.textbbox((166, 75), f'{pet_info.name}', font=rc_font_35, anchor='lm')[2] + 15
                if pet_info.have_egg:
                    egg_status_text = '已生蛋'
                elif has_predicted_egg_time:
                    egg_status_text = format_egg_countdown_text(predicted_egg_time, now_time)
                elif has_egg_prediction:
                    egg_status_text = '预计已生蛋'
                else:
                    egg_status_text = '未生蛋'
                pet_draw.text(
                    (name_right, 77),
                    egg_status_text,
                    (255, 255, 255),
                    rc_font_30,
                    'lm',
                )
                if has_predicted_egg_time:
                    pet_draw.text(
                        (166, 108),
                        f'预计生蛋：{format_egg_time_text(predicted_egg_time, now_time)}',
                        (255, 255, 255),
                        rc_font_22,
                        'lm',
                    )

            # 喂食状态改读接口 status（旧 feed_info/pet_rip_time 计时已被服务端移除，无法再算进度条）
            pet_draw.text(
                (166, pet_status_y),
                feed_status_text(pet_info.status),
                (255, 255, 255),
                rc_font_28,
                'lm',
            )

            level_img = Image.open(TEXT_PATH / f'level_icon.png').convert('RGBA')
            level_draw = ImageDraw.Draw(level_img)
            level_draw.text(
                (37, 19),
                f'Lv{pet_info.level}',
                (255, 255, 255),
                rc_font_22,
                'mm',
            )
            level_img = level_img.rotate(10, expand=True)
            pet_img.paste(level_img, (62, 125), level_img)

            img.paste(pet_img, (486 * rc_x + 18, rc_y * 192 + start_height), pet_img)

        start_height += (rc_y + 1) * 192 + 10

    if show_plants and len(home_info.home_plants) > 0:
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
        for shul, plant_info in enumerate(home_info.home_plants):
            rc_y = math.floor(shul / 3)
            rc_x = shul - (3 * rc_y)
            plant_img = Image.new('RGBA', (306, 148), (255, 255, 255, 0))
            plant_rip_time = plant_info.plant_rip_time
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
                plant_bg_img = Image.new('RGBA', (306, 148), (110, 171, 32, 255))
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
                    f'{hours}时{minutes}分',
                    (255, 255, 255),
                    rc_font_26,
                    'lm',
                )

                jindu_tc = Image.open(TEXT_PATH / 'jindu_tc.png').convert('RGBA').resize((147, 13))
                plant_img.paste(jindu_tc, (130, 103), jindu_tc)
                jindu_zhanbi = ((21600 * plant_info.plant_tab_id) - (plant_rip_time - now_time)) / (21600 * plant_info.plant_tab_id)
                jindu_len = max(5, int(146 * jindu_zhanbi) + 1)
                jindu_bar = Image.open(TEXT_PATH / 'jindu_bar.png').convert('RGBA').resize((jindu_len, 13))
                plant_img.paste(jindu_bar, (130, 103), jindu_bar)

            item_img = Image.open(TEXT_PATH / "home_icon" / f'{plant_info.plant_info.iconid}_2.png').convert('RGBA').resize((105, 105))
            plant_img.paste(item_img, (17, 19), item_img)
            plant_draw.text(
                (131, 45),
                f"{plant_info.plant_info.name}",
                (255, 255, 0),
                rc_font_35,
                'lm',
            )
            img.paste(plant_img, (306 * rc_x + 46, rc_y * 148 + start_height), plant_img)

    dt = datetime.fromtimestamp(int(home_info.finished_at))
    img_draw.text(
        (920, bg_height - 80),
        f"数据更新时间：{dt.strftime('%Y-%m-%d %H:%M:%S')}",
        (0, 0, 0),
        skill_font_24,
        'rm',
    )

    img.paste(footer, (110, bg_height - 44), footer)
    res = await convert_img(img)
    return res
