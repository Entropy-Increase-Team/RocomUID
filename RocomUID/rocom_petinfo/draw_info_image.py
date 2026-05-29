import re
import math
from pathlib import Path
import os
import copy
import time
from PIL import Image, ImageDraw, ImageChops
from ..utils.image.image_tools import get_text_line
from gsuid_core.utils.image.convert import convert_img
from ..utils.resource.RESOURCE_PATH import ROCOM_HEAD_PATH, ROCOM_ICON_PATH, ROCOM_CHARACTER_PATH, ROCOM_SKILL_PATH
from ..utils.map.rocom_map import skill_list
from ..utils.fonts.rocom_fonts import rc_font_30, rc_font_32, rc_font_34, rc_font_40, rc_font_64, rc_font_72, rc_font_22, rc_font_28, rc_font_44, skill_font_20, skill_font_22, skill_font_24, skill_font_32, skill_font_42
from ..utils.convert import get_pet_info
from ..utils.error_reply import prefix

TEXT_PATH = Path(__file__).parent / 'texture2D'
mask_bar = Image.open(TEXT_PATH / 'mask_bar.png')
top_bg = Image.open(TEXT_PATH / 'top_bg.png')
skill_bg = Image.open(TEXT_PATH / 'skill_bg.png')
bg_skill = Image.open(TEXT_PATH / 'skill_bg.png').convert('RGBA').resize((520, 220))
table_img = Image.open(TEXT_PATH / 'table.png')
tags_img = Image.open(TEXT_PATH / 'tags.png')
info_title_img = Image.open(TEXT_PATH / 'title.png')
pet_bg_mask = Image.open(TEXT_PATH / 'pet_bg.png').convert('RGBA').resize((575, 575))
rocom_title = Image.open(TEXT_PATH / 'a_title.png')
right_jinhua = Image.open(TEXT_PATH / 'right_jinhua.png')
pet_bg = Image.open(TEXT_PATH / 'pet_rocom_bg.png')
yise_overlay = Image.open(TEXT_PATH / 'yise_overlay.png')
xuancai_overlay = Image.open(TEXT_PATH / 'xuancai_overlay.png')
pet_rocom = Image.open(TEXT_PATH / 'pet_rocom.png')
jinhua_bg = Image.open(TEXT_PATH / 'jinhua_bg.png')
skill_mask = Image.open(TEXT_PATH / 'skill_mask.png')
cost_star = Image.open(TEXT_PATH / 'star.png')
star_cost = Image.open(TEXT_PATH / 'star.png').convert('RGBA').resize((45, 46))
footer = Image.open(TEXT_PATH / 'footer.png')
info_text_color = (100, 92, 79)

SHUX_LIST_XX = ['物攻', '魔攻', '物防', '魔防', '速度']
SHUX_SKILLLIST_DRAW = {
    '冰': (95, 173, 221),
    '草': (78, 188, 115),
    '虫': (158, 206, 33),
    '地': (154, 126, 63),
    '电': (231, 197, 6),
    '毒': (186, 98, 224),
    '恶': (207, 70, 122),
    '光': (79, 192, 255),
    '幻': (159, 167, 248),
    '火': (219, 85, 37),
    '机械': (64, 203, 169),
    '龙': (237, 73, 98),
    '萌': (252, 124, 172),
    '普通': (63, 137, 180),
    '水': (106, 169, 254),
    '无': (186, 187, 198),
    '武': (255, 150, 54),
    '翼': (62, 199, 202),
    '幽': (148, 70, 236),
}

SHUX_LIST_DRAW = {
    9: [(95, 173, 221), '冰'],
    3: [(78, 188, 115), '草'],
    13: [(158, 206, 33), '虫'],
    8: [(154, 126, 63), '地'],
    11: [(231, 197, 6), '电'],
    12: [(186, 98, 224), '毒'],
    18: [(207, 70, 122), '恶'],
    6: [(79, 192, 255), '光'],
    20: [(159, 167, 248), '幻'],
    4: [(219, 85, 37), '火'],
    19: [(64, 203, 169), '机械'],
    10: [(237, 73, 98), '龙'],
    16: [(252, 124, 172), '萌'],
    2: [(63, 137, 180), '普通'],
    5: [(106, 169, 254), '水'],
    23: [(186, 187, 198), '污染'],
    14: [(255, 150, 54), '武'],
    15: [(62, 199, 202), '翼'],
    17: [(148, 70, 236), '幽'],
}

XUEMAI_LIST_DRAW = {
    7: [(95, 173, 221), '冰'],
    2: [(78, 188, 115), '草'],
    11: [(158, 206, 33), '虫'],
    6: [(154, 126, 63), '地'],
    9: [(231, 197, 6), '电'],
    10: [(186, 98, 224), '毒'],
    16: [(207, 70, 122), '恶'],
    5: [(79, 192, 255), '光'],
    18: [(159, 167, 248), '幻'],
    3: [(219, 85, 37), '火'],
    17: [(64, 203, 169), '机械'],
    8: [(237, 73, 98), '龙'],
    14: [(252, 124, 172), '萌'],
    1: [(63, 137, 180), '普通'],
    4: [(106, 169, 254), '水'],
    23: [(186, 187, 198), '污染'],
    12: [(255, 150, 54), '武'],
    13: [(62, 199, 202), '翼'],
    15: [(148, 70, 236), '幽'],
    19: [(197, 66, 84), '首领'],
    21: [(219, 85, 37), '首领'],
    24: [(232, 202, 49), '奇异'],
}

tag_w_add = [0, 132, 143]

tag_title = ['HP', '物攻', '魔攻', '物防', '魔防', '速度']

attribute_tag = ['value', 'talent', 'effort_add']

async def draw_pet_info(uid, pet_data):
    bg_height = 970
    #计算已装备技能占用
    skill_equip_num = len(pet_data['equip_skills'])
    if skill_equip_num > 0:
        bg_height += math.ceil(skill_equip_num / 2) * 220 + 80
    #计算已学习技能占用
    skill_num = len(pet_data['skills'])
    if skill_num > 0:
        bg_height += math.ceil(skill_num / 5) * 99 + 80
    #计算特性信息占用
    tx_line_height = 0
    txname = pet_data['feature']['name']
    tx_content = pet_data['feature']['desc']
    txname_para = await get_text_line(f'{tx_content}', 28)
    tx_line_height += len(txname_para) * 40
    tx_line_height += 120
    tx_line_height = max(210, tx_line_height)
    bg_height += tx_line_height + 80
    #生成背景图
    img = Image.open(TEXT_PATH / 'bg.jpg').convert('RGB')
    if bg_height > 2417:
        img = img.resize((1200, bg_height))
    else:
        img = img.crop((0, 0, 1200, bg_height))
    
    img.paste(info_title_img, (0, 0), info_title_img)
    img_draw = ImageDraw.Draw(img)
    # 画名称标题
    img_draw.text(
        (600, 96),
        f'精灵状态',
        (255, 255, 255),
        rc_font_72,
        'mm',
    )
    
    img_draw.text(
        (600, 260),
        f'{pet_data["name"]}',
        info_text_color,
        rc_font_64,
        'mm',
    )
    
    pet_base = await get_pet_info(pet_data["pet_id"])
    img_draw.text(
        (1050, 280),
        f'UID{uid}',
        info_text_color,
        rc_font_30,
        'rm',
    )
    pet_bg_img = Image.new('RGBA', (575, 575), SHUX_LIST_DRAW[pet_base['unit_type_list'][0]][0])
    img.paste(pet_bg_img, (-6, 359), pet_bg_mask)
    # 画形象
    pet_icon_name = pet_base['icon']
    if pet_data['mutation_type'] in [9, 1]:
        pet_icon_name = pet_base['icon'] + '_yise'
    pet_head_icon = ROCOM_ICON_PATH / f'{pet_icon_name}.png'
    if not os.path.exists(pet_head_icon):
        pet_head_icon = ROCOM_HEAD_PATH / 'dimo.png'
    
    pokemon_img = (
        Image.open(pet_head_icon)
        .convert('RGBA')
        .resize((552, 552))
    )
    
    
    
    img.paste(pokemon_img, (0, 371), pokemon_img)
    
    #画稀有类型
    if pet_data['mutation_type'] in [1,8,9]:
        star_img = Image.open(TEXT_PATH / f'star_{pet_data["mutation_type"]}.png').convert('RGBA').resize((80, 80))
        img.paste(star_img, (470, 850), star_img)
    
    #画精灵属性
    img.paste(rocom_title, (565, 334), rocom_title)
    img_draw.text(
        (631, 363),
        f'精灵属性',
        (255, 255, 255),
        rc_font_28,
        'lm',
    )
    x_num = 730
    y_num = 483
    img.paste(table_img, (550, 405), table_img)
    for index_x in range(0, 3):
        x_num = x_num + tag_w_add[index_x]
        for index_y, sx_item in enumerate(pet_data['attribute_info'].keys()):
            tag_x = x_num
            tag_y = y_num + index_y * 54
            img.paste(tags_img, (tag_x, tag_y), tags_img)
            if index_x == 0:
                img_draw.text(
                    (tag_x - 95, tag_y + 22),
                    f'{tag_title[index_y]}',
                    info_text_color,
                    rc_font_34,
                    'lm',
                )
            img_draw.text(
                (tag_x + 58, tag_y + 22),
                f"{pet_data['attribute_info'][sx_item][attribute_tag[index_x]]}",
                (240, 236, 225),
                rc_font_32,
                'mm',
            )
    
    # 画属性类型
    shux_num = 0
    for shul, shuxing in enumerate(pet_base['unit_type']):
        shuxing_img = Image.new('RGBA', (142, 38), SHUX_LIST_DRAW[shuxing][0])
        sx_image = Image.open(TEXT_PATH / '属性' / f'{shuxing}.png').convert('RGBA').resize((42, 42))
        shuxing_img.paste(sx_image, (-2, -2), sx_image)
        shuxing_temp = Image.new('RGBA', (142, 38))
        shuxing_temp.paste(shuxing_img, (0, 0), mask_bar)
        shuxing_draw = ImageDraw.Draw(shuxing_temp)
        shuxing_draw.text(
            (91, 19),
            f'{SHUX_LIST_DRAW[shuxing][1]}',
            (255, 255, 255),
            rc_font_32,
            'mm',
        )
        img.paste(shuxing_temp, (150 * shul + 580, 830), shuxing_temp)
        shux_num = shul
    
    # 画血脉类型
    shux_num = shux_num + 1
    shuxing_img = Image.new('RGBA', (142, 38), XUEMAI_LIST_DRAW[pet_data['blood_id']][0])
    sx_image = Image.open(TEXT_PATH / '血脉' / f'{pet_data["blood_id"]}.png').convert('RGBA').resize((42, 42))
    shuxing_img.paste(sx_image, (-2, -2), sx_image)
    shuxing_temp = Image.new('RGBA', (142, 38))
    shuxing_temp.paste(shuxing_img, (0, 0), mask_bar)
    shuxing_draw = ImageDraw.Draw(shuxing_temp)
    shuxing_draw.text(
        (88, 19),
        f"{XUEMAI_LIST_DRAW[pet_data['blood_id']][1]}",
        (255, 255, 255),
        rc_font_32,
        'mm',
    )
    img.paste(shuxing_temp, (150 * shux_num + 580, 830), shuxing_temp)
    
    start_height = 970
    img.paste(rocom_title, (68, start_height), rocom_title)
    img_draw.text(
        (134, start_height + 29),
        f'精灵特性',
        (255, 255, 255),
        rc_font_28,
        'lm',
    )
    start_height += 70
    tx_icon = ROCOM_CHARACTER_PATH / f'{txname}.png'
    if not os.path.exists(tx_icon):
        tx_icon = ROCOM_CHARACTER_PATH / '最好的伙伴.png'
    tx_img = Image.open(tx_icon).convert('RGBA').resize((121, 121))
    img.paste(tx_img, (90, start_height), skill_mask)
    start_height += 20
    img_draw.text(
        (220, start_height),
        f"{txname}",
        (0,0,0),
        rc_font_40,
        'lm',
    )
    start_height += 20
    tx_line_h = 20
    for line in txname_para:
        img_draw.text(
            (220, start_height + tx_line_h),
            line,
            info_text_color,
            skill_font_32,
            'lm',
        )
        tx_line_h += 40

    tx_line_h = max(110, tx_line_h)
    
    start_height = start_height + tx_line_h
    
    if len(pet_data['equip_skills']) > 0:
        img.paste(rocom_title, (68, start_height), rocom_title)
        img_draw.text(
            (134, start_height + 30),
            f'装备技能',
            (255, 255, 255),
            rc_font_28,
            'lm',
        )
        start_height += 70
        jn_y = 0
        for shul, skill in enumerate(pet_data['equip_skills']):
            jn_y = math.floor(shul / 2)
            jn_x = shul - (2 * jn_y)
            jineng = skill['name']
            jineng_img = Image.new(
                'RGBA', (520, 220), SHUX_SKILLLIST_DRAW[skill_list[jineng][0]]
            )
            skill_image = Image.open(ROCOM_SKILL_PATH / f'{jineng}.png').convert('RGBA').resize((158, 158))
            jineng_temp = Image.new('RGBA', (520, 220))
            jineng_temp.paste(jineng_img, (0, 0), bg_skill)
            jineng_temp.paste(skill_image, (35, 32), skill_image)
            sx_image = Image.open(TEXT_PATH / '属性' / f'{skill_list[jineng][0]}.png').convert('RGBA').resize((75, 75))
            jineng_temp.paste(sx_image, (-5, -5), sx_image)
            jineng_draw = ImageDraw.Draw(jineng_temp)
            jineng_draw.text(
                (220, 70),
                f'{jineng}',
                (255, 255, 255),
                skill_font_42,
                'lm',
            )
            jineng_temp.paste(star_cost, (270, 127), star_cost)
            jineng_draw.text(
                (220, 150),
                f'{skill_list[jineng][1]}',
                (255, 255, 255),
                skill_font_42,
                'lm',
            )
            jineng_draw.text(
                (350, 150),
                f'{skill_list[jineng][2] if skill_list[jineng][2] != "0" else "—"}',
                (255, 255, 255),
                skill_font_42,
                'lm',
            )
            img.paste(
                jineng_temp, (516 * jn_x + 82, jn_y * 220 + start_height), jineng_temp
            )
        start_height += (jn_y + 1) * 220 + 10
    
    if len(pet_data['skills']) > 0:
        img.paste(rocom_title, (68, start_height), rocom_title)
        img_draw.text(
            (134, start_height + 30),
            f'已学技能',
            (255, 255, 255),
            rc_font_28,
            'lm',
        )
        start_height += 70
        jn_y = 0
        for shul, skill in enumerate(pet_data['skills']):
            jineng = skill['name']
            jn_y = math.floor(shul / 5)
            jn_x = shul - (5 * jn_y)
            jineng_img = Image.new(
                'RGBA', (207, 99), SHUX_SKILLLIST_DRAW[skill_list[jineng][0]]
            )
            skill_image = Image.open(ROCOM_SKILL_PATH / f'{jineng}.png').convert('RGBA').resize((67, 67))
            jineng_temp = Image.new('RGBA', (207, 99))
            jineng_temp.paste(jineng_img, (0, 0), skill_bg)
            jineng_temp.paste(skill_image, (15, 16), skill_image)
            sx_image = Image.open(TEXT_PATH / '属性' / f'{skill_list[jineng][0]}.png').convert('RGBA').resize((45, 45))
            jineng_temp.paste(sx_image, (-5, -5), sx_image)
            jineng_draw = ImageDraw.Draw(jineng_temp)
            jineng_draw.text(
                (94, 35),
                f'{jineng}',
                (255, 255, 255),
                skill_font_22,
                'lm',
            )
            jineng_temp.paste(cost_star, (120, 52), cost_star)
            jineng_draw.text(
                (94, 65),
                f'{skill_list[jineng][1]}',
                (255, 255, 255),
                skill_font_22,
                'lm',
            )
            jineng_draw.text(
                (150, 65),
                f'{skill_list[jineng][2] if skill_list[jineng][2] != "0" else "—"}',
                (255, 255, 255),
                skill_font_22,
                'lm',
            )
            img.paste(
                jineng_temp, (208 * jn_x + 82, jn_y * 99 + start_height), jineng_temp
            )
        
        start_height += (jn_y + 1) * 99 + 10
    
    
    img.paste(footer, (370, bg_height - 44), footer)
    res = await convert_img(img)
    return res

async def draw_pet_list(uid, pet_data):
    bg_height = 370
    pet_list_height = max(200, math.ceil(len(pet_data) / 6) * 216)
    bg_height += pet_list_height
    img = Image.open(TEXT_PATH / 'bg.jpg').convert('RGB')
    if bg_height > 2417:
        img = img.resize((1000, bg_height))
    else:
        img = img.crop((0, 0, 1000, bg_height))
    
    img.paste(top_bg, (0, 0), top_bg)
    img_draw = ImageDraw.Draw(img)
    #写昵称与uid
    img_draw.text(
        (45, 90),
        f'UID{uid} 精灵数据已刷新完成',
        (255, 255, 255),
        rc_font_44,
        'lm',
    )
    img_draw.text(
        (45, 130),
        f'可使用【{prefix}查询[ID]】查看精灵详细信息',
        (255, 255, 255),
        skill_font_24,
        'lm',
    )
    #画精灵背包
    img.paste(rocom_title, (48, 220), rocom_title)
    img_draw.text(
        (114, 249),
        f'精灵背包',
        (255, 255, 255),
        rc_font_28,
        'lm',
    )
    
    start_height = 300
    for shul, pet_id in enumerate(pet_data):
        rc_y = math.floor(shul / 6)
        rc_x = shul - (6 * rc_y)
        pet_info = pet_data[pet_id]
        rocom_img = Image.new('RGBA', (150, 216), (255, 255, 255, 0))
        #画背景与头像
        if pet_info['mutation_type'] in [9, 1]:
            overlay_img = copy.deepcopy(yise_overlay)
            pet_head_icon = ROCOM_HEAD_PATH / f'{pet_info["pet_id"]}_1.png'
        else:
            overlay_img = copy.deepcopy(xuancai_overlay)
            pet_head_icon = ROCOM_HEAD_PATH / f'{pet_info["pet_id"]}.png'
        if not os.path.exists(pet_head_icon):
            pet_head_icon = ROCOM_HEAD_PATH / '3004.png'
        head_img = Image.open(pet_head_icon).convert('RGBA').resize((130, 130))
        pet_base = await get_pet_info(pet_info["pet_id"])
        pet_bg_img = Image.new('RGBA', (150, 216), SHUX_LIST_DRAW[pet_base['unit_type'][0]][0])
        combined_image = ImageChops.overlay(pet_bg_img, overlay_img)
        rocom_img.paste(combined_image, (0, 0), pet_bg)
        rocom_img.paste(pet_rocom, (0, 0), pet_rocom)
        rocom_img.paste(head_img, (10, 35), head_img)
        #画属性
        for index_sx, shuxing_item in enumerate(pet_base['unit_type']):
            sx_img = Image.open(TEXT_PATH / '属性' / f'{shuxing_item}.png').convert('RGBA').resize((45, 45))
            rocom_img.paste(sx_img, (index_sx * 30 - 5, -5), sx_img)
        #画血脉
        xm_img = Image.open(TEXT_PATH / '血脉' / f'{pet_info["blood_id"]}.png').convert('RGBA').resize((45, 45))
        rocom_img.paste(xm_img, (110, -5), xm_img)
        #画标志
        if pet_info['mutation_type'] in [1,8,9]:
            star_img = Image.open(TEXT_PATH / f'star_{pet_info["mutation_type"]}.png')
            rocom_img.paste(star_img, (6, 110), star_img)
        #画等级
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
        rocom_img.paste(level_img, (69, 110), level_img)
        #画昵称
        rocom_draw = ImageDraw.Draw(rocom_img)
        rocom_draw.text(
            (75, 170),
            f'{pet_info["name"]}',
            (255, 255, 255),
            skill_font_22,
            'mm',
        )
        rocom_draw.text(
            (75, 193),
            f'ID{pet_id}',
            (255, 255, 255),
            skill_font_20,
            'mm',
        )
        img.paste(rocom_img, (150 * rc_x + 55, rc_y * 216 + start_height), rocom_img)
    img.paste(footer, (270, bg_height - 44), footer)
    res = await convert_img(img)
    return res