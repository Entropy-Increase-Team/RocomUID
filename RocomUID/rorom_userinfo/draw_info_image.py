import re
import math
from pathlib import Path
import os
import copy
import time
from PIL import Image, ImageDraw, ImageChops
from ..utils.image.image_tools import get_text_line
from gsuid_core.utils.image.convert import convert_img
from ..utils.resource.RESOURCE_PATH import ROCOM_HEAD_PATH
from ..utils.fonts.rocom_fonts import rc_font_22, rc_font_28, rc_font_44, rc_font_42, skill_font_24, skill_font_42
from gsuid_core.utils.image.image_tools import (
    draw_pic_with_ring,
    get_qq_avatar,
)
from ..utils.convert import name_id_list

TEXT_PATH = Path(__file__).parent / 'texture2D'
top_bg = Image.open(TEXT_PATH / 'top_bg.png')
title_fg = Image.open(TEXT_PATH / 'title_fg.png')
touxiang_mask = Image.open(TEXT_PATH / 'touxiang_mask.png')
rocom_title = Image.open(TEXT_PATH / 'a_title.png')
rank_bg = Image.open(TEXT_PATH / 'rank_bg.png')
banner_img = Image.open(TEXT_PATH / 'banner.png')
pet_bg = Image.open(TEXT_PATH / 'pet_bg.png')
yise_overlay = Image.open(TEXT_PATH / 'yise_overlay.png')
xuancai_overlay = Image.open(TEXT_PATH / 'xuancai_overlay.png')
pet_rocom = Image.open(TEXT_PATH / 'pet_rocom.png')
footer = Image.open(TEXT_PATH / 'footer.png')
info_text_color = (66, 66, 66)

SHUX_LIST_DRAW = {
    9: (95, 173, 221),
    3: (78, 188, 115),
    13: (158, 206, 33),
    8: (154, 126, 63),
    11: (231, 197, 6),
    12: (186, 98, 224),
    18: (207, 70, 122),
    6: (79, 192, 255),
    20: (159, 167, 248),
    4: (219, 85, 37),
    19: (64, 203, 169),
    10: (237, 73, 98),
    16: (252, 124, 172),
    2: (63, 137, 180),
    5: (106, 169, 254),
    23: (186, 187, 198),
    14: (255, 150, 54),
    15: (62, 199, 202),
    17: (148, 70, 236),
}

rank_name_list = {
    "1": "",
    "2": "见习决斗家Ⅰ",
    "3": "见习决斗家Ⅱ",
    "4": "见习决斗家Ⅲ",
    "5": "见习决斗家Ⅳ",
    "6": "见习决斗家Ⅴ",
    "7": "初级决斗家Ⅰ",
    "7": "初级决斗家Ⅱ",
    "8": "初级决斗家Ⅲ",
    "9": "初级决斗家Ⅳ",
    "10": "初级决斗家Ⅴ",
    "11": "中级决斗家Ⅰ",
    "12": "中级决斗家Ⅱ",
    "13": "中级决斗家Ⅲ",
    "14": "中级决斗家Ⅳ",
    "15": "中级决斗家Ⅴ",
    "16": "高级决斗家Ⅰ",
    "17": "高级决斗家Ⅱ",
    "18": "高级决斗家Ⅲ",
    "19": "高级决斗家Ⅳ",
    "20": "高级决斗家Ⅴ",
    "21": "大师决斗家",
    "22": "大师决斗家",
    "23": "大师决斗家"
    
}

async def draw_user_info(ev, uid, userinfo, petinfo):
    bg_height = 900
    bg_height += math.ceil(len(petinfo.list) / 6) * 216
    
    img = Image.open(TEXT_PATH / 'bg.jpg').convert('RGB')
    if bg_height > 2417:
        img = img.resize((1000, bg_height))
    else:
        img = img.crop((0, 0, 1000, bg_height))
    
    img.paste(top_bg, (0, 0), top_bg)
    img.paste(title_fg, (0, 0), title_fg)
    #画头像
    if ev.sender["avatar"]:
        char_pic = await get_qq_avatar(avatar_url=ev.sender["avatar"])
        char_pic = await draw_pic_with_ring(char_pic, 152, None, False)
    else:
        char_pic = Image.open(TEXT_PATH / 'img_head.png')
    img.paste(char_pic, (32, 28), char_pic)
    
    img_draw = ImageDraw.Draw(img)
    #写昵称与uid
    img_draw.text(
        (200, 65),
        f'{userinfo.basic.nickname}',
        (255, 255, 255),
        rc_font_44,
        'lm',
    )
    img_draw.text(
        (200, 110),
        f'Lv {userinfo.basic.level}',
        (255, 255, 255),
        rc_font_42,
        'lm',
    )
    img_draw.text(
        (200, 155),
        f'学号 {uid}',
        (255, 255, 255),
        rc_font_42,
        'lm',
    )
    
    #画段位
    img.paste(rank_bg, (0, 228), rank_bg)
    img_draw.text(
        (250, 281),
        f'{rank_name_list.get(userinfo.battle.rank, "")}',
        (0, 0, 0),
        skill_font_42,
        'mm',
    )
    img_draw.text(
        (605, 281),
        f'{round((userinfo.battle.wins/userinfo.battle.matches), 4) * 100}%',
        (0, 0, 0),
        skill_font_42,
        'mm',
    )
    img_draw.text(
        (785, 281),
        f'{userinfo.battle.matches}',
        (0, 0, 0),
        skill_font_42,
        'mm',
    )
    
    #画个人信息
    img.paste(rocom_title, (48, 417), rocom_title)
    img_draw.text(
        (114, 446),
        f'个人信息',
        (255, 255, 255),
        rc_font_28,
        'lm',
    )
    img.paste(banner_img, (0, 450), banner_img)
    #入学
    img_draw.text(
        (190, 575),
        f'{userinfo.basic.registerDate}',
        info_text_color,
        skill_font_24,
        'lm',
    )
    #时装
    img_draw.text(
        (480, 575),
        f'{userinfo.collection.costumeCount}',
        info_text_color,
        skill_font_24,
        'lm',
    )
    #图鉴
    img_draw.text(
        (760, 575),
        f'{userinfo.collection.pokedexCount}/347',
        info_text_color,
        skill_font_24,
        'lm',
    )
    #了不起
    img_draw.text(
        (190, 668),
        f'{userinfo.elves.amazingElves}',
        info_text_color,
        skill_font_24,
        'lm',
    )
    #炫彩
    img_draw.text(
        (480, 668),
        f'{userinfo.elves.colorfulElves}',
        info_text_color,
        skill_font_24,
        'lm',
    )
    #异色
    img_draw.text(
        (760, 668),
        f'{userinfo.elves.shinyElves}',
        info_text_color,
        skill_font_24,
        'lm',
    )
    
    #画精灵信息
    img.paste(rocom_title, (48, 765), rocom_title)
    img_draw.text(
        (114, 794),
        f'精灵背包',
        (255, 255, 255),
        rc_font_28,
        'lm',
    )
    start_height = 840
    for shul, rocom_item in enumerate(petinfo.list):
        rc_y = math.floor(shul / 6)
        rc_x = shul - (6 * rc_y)
        rocom_img = Image.new('RGBA', (150, 216), (255, 255, 255, 0))
        if rocom_item.PetMutation in [9, 1]:
            overlay_img = copy.deepcopy(yise_overlay)
            head_img = Image.open(ROCOM_HEAD_PATH / f'{rocom_item.PetBaseId}_1.png').convert('RGBA').resize((130, 130))
        else:
            overlay_img = copy.deepcopy(xuancai_overlay)
            head_img = Image.open(ROCOM_HEAD_PATH / f'{rocom_item.PetBaseId}.png').convert('RGBA').resize((130, 130))
        pet_bg_img = Image.new('RGBA', (150, 216), SHUX_LIST_DRAW[rocom_item.PetSkillDamType[0]])
        combined_image = ImageChops.overlay(pet_bg_img, overlay_img)
        rocom_img.paste(combined_image, (0, 0), pet_bg)
        rocom_img.paste(pet_rocom, (0, 0), pet_rocom)
        rocom_img.paste(head_img, (10, 35), head_img)
        for index_sx, shuxing_item in enumerate(rocom_item.PetSkillDamType):
            sx_img = Image.open(TEXT_PATH / '属性' / f'{shuxing_item}.png').convert('RGBA').resize((45, 45))
            rocom_img.paste(sx_img, (index_sx * 30 - 5, -5), sx_img)
        xm_img = Image.open(TEXT_PATH / '血脉' / f'{rocom_item.PetBlood}.png').convert('RGBA').resize((45, 45))
        rocom_img.paste(xm_img, (110, -5), xm_img)
        if rocom_item.PetMutation in [1,8,9]:
            star_img = Image.open(TEXT_PATH / f'star_{rocom_item.PetMutation}.png')
            rocom_img.paste(star_img, (6, 120), star_img)
        level_img = Image.open(TEXT_PATH / f'level_icon.png').convert('RGBA')
        level_draw = ImageDraw.Draw(level_img)
        level_draw.text(
            (37, 19),
            f'Lv{rocom_item.SpiritLevel}',
            (255, 255, 255),
            rc_font_22,
            'mm',
        )
        level_img = level_img.rotate(10, expand=True)
        rocom_img.paste(level_img, (69, 125), level_img)
        rocom_draw = ImageDraw.Draw(rocom_img)
        rocom_draw.text(
            (75, 183),
            f'{name_id_list[str(rocom_item.PetBaseId)]}',
            (255, 255, 255),
            skill_font_24,
            'mm',
        )
        
        img.paste(rocom_img, (150 * rc_x + 55, rc_y * 216 + start_height), rocom_img)
    
    img.paste(footer, (270, bg_height - 44), footer)
    res = await convert_img(img)
    return res