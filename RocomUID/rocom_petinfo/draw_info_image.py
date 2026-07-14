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
from ..utils.fonts.rocom_fonts import rocom_font_origin, rc_font_14, rc_font_16, rc_font_18, rc_font_20, rc_font_22, rc_font_24, rc_font_28, rc_font_30, rc_font_32, rc_font_34, rc_font_40, rc_font_44, rc_font_64, rc_font_72, skill_font_16, skill_font_18, skill_font_20, skill_font_22, skill_font_24, skill_font_32, skill_font_42
from ..utils.convert import get_pet_info, get_skill_info, pet_list, nature_map
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
home_title_small = rocom_title.resize((int(rocom_title.width * 0.8), int(rocom_title.height * 0.8)))

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

def _get_attr_draw_info(shuxing):
    if shuxing in SHUX_LIST_DRAW:
        color, name = SHUX_LIST_DRAW[shuxing]
        return color, name, str(shuxing)
    if isinstance(shuxing, str):
        for attr_id, (color, name) in SHUX_LIST_DRAW.items():
            if shuxing == name:
                return color, name, shuxing
        if shuxing in SHUX_SKILLLIST_DRAW:
            return SHUX_SKILLLIST_DRAW[shuxing], shuxing, shuxing
    return SHUX_SKILLLIST_DRAW['无'], str(shuxing), '无'

async def draw_pet_info(uid, pet_data):
    bg_height = 970
    #计算已装备技能占用
    skill_equip_num = len(pet_data.equip_skills)
    if skill_equip_num > 0:
        bg_height += math.ceil(skill_equip_num / 2) * 220 + 80
    #计算已学习技能占用
    skill_num = len(pet_data.skills)
    if skill_num > 0:
        bg_height += math.ceil(skill_num / 5) * 99 + 80
    #计算特性信息占用
    tx_line_height = 0
    txname = pet_data.feature.name
    tx_content = pet_data.feature.desc
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
        f'{pet_data.name}',
        info_text_color,
        rc_font_64,
        'mm',
    )
    
    pet_base = await get_pet_info(pet_data.pet_id)
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
    if pet_data.mutation_type in [9, 1]:
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
    if pet_data.mutation_type in [1, 8, 9]:
        star_img = Image.open(TEXT_PATH / f'star_{pet_data.mutation_type}.png').convert('RGBA').resize((80, 80))
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
    attribute_items = [
        pet_data.attribute_info.pethp,
        pet_data.attribute_info.petatk,
        pet_data.attribute_info.petspatk,
        pet_data.attribute_info.petdef,
        pet_data.attribute_info.petspdef,
        pet_data.attribute_info.petspd,
    ]
    for index_x in range(0, 3):
        x_num = x_num + tag_w_add[index_x]
        for index_y, sx_item in enumerate(attribute_items):
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
                f"{getattr(sx_item, attribute_tag[index_x])}",
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
    shuxing_img = Image.new('RGBA', (142, 38), XUEMAI_LIST_DRAW[pet_data.blood_id][0])
    sx_image = Image.open(TEXT_PATH / '血脉' / f'{pet_data.blood_id}.png').convert('RGBA').resize((42, 42))
    shuxing_img.paste(sx_image, (-2, -2), sx_image)
    shuxing_temp = Image.new('RGBA', (142, 38))
    shuxing_temp.paste(shuxing_img, (0, 0), mask_bar)
    shuxing_draw = ImageDraw.Draw(shuxing_temp)
    shuxing_draw.text(
        (88, 19),
        f"{XUEMAI_LIST_DRAW[pet_data.blood_id][1]}",
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
    tx_icon = ROCOM_CHARACTER_PATH / f"{pet_data.feature.id}.png"
    if not os.path.exists(tx_icon):
        tx_icon = ROCOM_CHARACTER_PATH / '200191.png'
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
    
    if len(pet_data.equip_skills) > 0:
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
        for shul, skill in enumerate(pet_data.equip_skills):
            jn_y = math.floor(shul / 2)
            jn_x = shul - (2 * jn_y)
            jineng = skill.name
            info_skill = await get_skill_info(skill.id)
            jineng_img = Image.new(
                'RGBA', (520, 220), SHUX_SKILLLIST_DRAW[info_skill['families']]
            )
            skill_image = Image.open(ROCOM_SKILL_PATH / f"{skill.iconid}.png").convert('RGBA').resize((158, 158))
            jineng_temp = Image.new('RGBA', (520, 220))
            jineng_temp.paste(jineng_img, (0, 0), bg_skill)
            jineng_temp.paste(skill_image, (35, 32), skill_image)
            sx_image = Image.open(TEXT_PATH / '属性' / f"{info_skill['families']}.png").convert('RGBA').resize((75, 75))
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
                f"{info_skill['cost']}",
                (255, 255, 255),
                skill_font_42,
                'lm',
            )
            # jineng_draw.text(
                # (350, 150),
                # f'{skill_list[jineng][2] if skill_list[jineng][2] != "0" else "—"}',
                # (255, 255, 255),
                # skill_font_42,
                # 'lm',
            # )
            img.paste(
                jineng_temp, (516 * jn_x + 82, jn_y * 220 + start_height), jineng_temp
            )
        start_height += (jn_y + 1) * 220 + 10
    
    if len(pet_data.skills) > 0:
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
        for shul, skill in enumerate(pet_data.skills):
            jineng = skill.name
            jn_y = math.floor(shul / 5)
            jn_x = shul - (5 * jn_y)
            info_skill = await get_skill_info(skill.id)
            jineng_img = Image.new(
                'RGBA', (207, 99), SHUX_SKILLLIST_DRAW[info_skill['families']]
            )
            skill_image = Image.open(ROCOM_SKILL_PATH / f"{skill.iconid}.png").convert('RGBA').resize((67, 67))
            jineng_temp = Image.new('RGBA', (207, 99))
            jineng_temp.paste(jineng_img, (0, 0), skill_bg)
            jineng_temp.paste(skill_image, (15, 16), skill_image)
            sx_image = Image.open(TEXT_PATH / '属性' / f"{info_skill['families']}.png").convert('RGBA').resize((45, 45))
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
                f"{info_skill['cost']}",
                (255, 255, 255),
                skill_font_22,
                'lm',
            )
            # jineng_draw.text(
                # (150, 65),
                # f'{skill_list[jineng][2] if skill_list[jineng][2] != "0" else "—"}',
                # (255, 255, 255),
                # skill_font_22,
                # 'lm',
            # )
            img.paste(
                jineng_temp, (208 * jn_x + 82, jn_y * 99 + start_height), jineng_temp
            )
        
        start_height += (jn_y + 1) * 99 + 10
    
    
    img.paste(footer, (370, bg_height - 44), footer)
    res = await convert_img(img)
    return res

def _safe_open(path: Path, fallback: Path) -> Image.Image:
    if os.path.exists(path):
        return Image.open(path).convert('RGBA')
    return Image.open(fallback).convert('RGBA')

def _get_voice_badge_text(pet_info):
    voice = getattr(pet_info, 'voice', None)
    if voice is None:
        return None
    try:
        voice_num = int(voice)
    except (TypeError, ValueError):
        return None
    if 96 <= voice_num <= 100:
        return '婉转声'
    if -100 <= voice_num <= -96:
        return '粗嗓门'
    return f'{voice_num}db'

def _get_weight_badge_info(pet_info, pet_base):
    weight = getattr(pet_info, 'weight', None)
    weight_low = pet_base.get('weight_low')
    weight_high = pet_base.get('weight_high')
    if weight in [None, ''] or weight_low in [None, ''] or weight_high in [None, '']:
        return None
    try:
        weight_num = float(weight)
        low_num = float(weight_low)
        high_num = float(weight_high)
    except (TypeError, ValueError):
        return None
    if high_num <= low_num:
        return None
    edge = (high_num - low_num) * 0.05
    if weight_num >= high_num - edge:
        return '大块头', TEXT_PATH / 'img_MedalIcon_Huge.png'
    if weight_num <= low_num + edge:
        return '小块头', TEXT_PATH / 'img_MedalIcon_Mini.png'
    return None

def _get_voice_badge_info(pet_info):
    voice_badge_text = _get_voice_badge_text(pet_info)
    if voice_badge_text == '婉转声':
        return voice_badge_text, TEXT_PATH / 'img_MedalIcon_high.png'
    if voice_badge_text == '粗嗓门':
        return voice_badge_text, TEXT_PATH / 'img_MedalIcon_low.png'
    return None

def _measure_brief_tag(draw, text):
    bbox = draw.textbbox((0, 0), text, font=rc_font_18)
    return bbox[2] - bbox[0] + 24 + 2 + 8 * 2

def _draw_brief_tag(img, draw, x, y, text, icon_path, fill, border):
    return _draw_icon_text_badge(img, draw, x, y, icon_path, text, rc_font_18, fill, border, fill, pad_x=8, h=30, icon_gap=2)

def _draw_home_badge(text: str):
    badge_w = 90
    badge_h = 28
    badge = tags_img.resize((badge_w, badge_h)).convert('RGBA')
    badge_draw = ImageDraw.Draw(badge)
    text_bbox = badge_draw.textbbox((0, 0), text, font=rc_font_14)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    text_x = (badge_w - text_w) / 2 - text_bbox[0]
    text_y = (badge_h - text_h) / 2 - text_bbox[1]
    badge_draw.text((text_x, text_y), text, (255, 255, 255), rc_font_14)
    return badge

def _format_percent(value):
    if value in [None, '']:
        return '--'
    try:
        percent = float(value)
        if percent <= 1:
            percent *= 100
        return f'{percent:.2f}%'
    except (TypeError, ValueError):
        return str(value)

def _calc_range_percent(value, low, high):
    if value in [None, ''] or low in [None, ''] or high in [None, '']:
        return None
    try:
        low_num = float(low)
        high_num = float(high)
        if high_num == low_num:
            return None
        return max(0, min(100, (float(value) - low_num) * 100 / (high_num - low_num)))
    except (TypeError, ValueError):
        return None

def _calc_voice_percent(value):
    if value in [None, '']:
        return None
    try:
        return max(0, min(100, abs(float(value))))
    except (TypeError, ValueError):
        return None

def _format_height(value):
    if value in [None, '']:
        return '--'
    try:
        height = float(value)
        if height > 10:
            height /= 100
        return f'{height:.2f}m'
    except (TypeError, ValueError):
        return str(value)

def _format_weight(value):
    if value in [None, '']:
        return '--'
    try:
        weight = float(value)
        if weight > 500:
            weight /= 1000
        return f'{weight:.3f}kg'
    except (TypeError, ValueError):
        return str(value)

def _get_nature_name(nature):
    if isinstance(nature, dict):
        return nature.get('name') or nature.get('nature_name') or nature.get('desc') or '未知'
    if nature in [None, '']:
        return '未知'
    try:
        nature_info = nature_map.get(str(int(nature)))
        if isinstance(nature_info, dict):
            return nature_info.get('name') or str(nature)
        return str(nature)
    except (TypeError, ValueError):
        pass
    return str(nature)

def _get_speciality_name(pet_info, pet_base):
    speciality_map = {
        1: '无',
        101: '奇袭',
        103: '亲密',
        104: '灵巧',
        105: '灵巧',
        106: '灵巧',
        401: '疾行',
        402: '同乘',
        502: '勇敢',
        1001: '爱分享',
        3001: '家里蹲',
        5002: '热心教',
        50001: '慈悲为怀',
    }
    ids = getattr(pet_info, 'real_speciality_ids', None)
    if not ids:
        return None
    talent_list = pet_base.get('talent_random_list') or []
    names = []
    for item in ids:
        try:
            item_id = int(item)
        except (TypeError, ValueError):
            continue
        if item_id in speciality_map:
            names.append(speciality_map[item_id])
        elif 0 <= item_id < len(talent_list):
            names.append(str(talent_list[item_id]))
        elif item_id % 100 < len(talent_list):
            names.append(str(talent_list[item_id % 100]))
    names = [name for name in names if name and name != '无']
    return '、'.join(names[:2]) or '无'

def _get_metric_percent(pet_info, pet_base, metric):
    percent = getattr(pet_info, f'{metric}_percent', None)
    if percent not in [None, '']:
        return percent
    if metric == 'voice':
        return _calc_voice_percent(getattr(pet_info, 'voice', None))
    return _calc_range_percent(
        getattr(pet_info, metric, None),
        pet_base.get(f'{metric}_low'),
        pet_base.get(f'{metric}_high'),
    )

def _get_mutation_name(pet_info):
    mutation_name = getattr(pet_info, 'mutation_name', None)
    if mutation_name:
        return mutation_name
    mutation_type = getattr(pet_info, 'mutation_type', None)
    return {0: '普通', 1: '异色', 8: '炫彩', 9: '异色'}.get(mutation_type, '普通')

def _draw_round_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def _draw_text_badge(draw, x, y, text, font, fill, border, text_fill=None, pad_x=14, h=35):
    text_fill = text_fill or fill
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + pad_x * 2
    _draw_round_rect(draw, (x, y, x + w, y + h), h // 2, (255, 255, 255), border)
    draw.text((x + w / 2, y + h / 2), text, text_fill, font, 'mm')
    return w

def _draw_icon_text_badge(img, draw, x, y, icon_path, text, font, fill, border, text_fill=None, pad_x=12, h=34, icon_gap=4):
    text_fill = text_fill or fill
    icon_size = 24
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    w = text_w + icon_size + icon_gap + pad_x * 2
    _draw_round_rect(draw, (x, y, x + w, y + h), h // 2, (255, 255, 255), border)
    if os.path.exists(icon_path):
        icon_img = Image.open(icon_path).convert('RGBA').resize((icon_size, icon_size), Image.LANCZOS)
        img.paste(icon_img, (int(x + pad_x), int(y + (h - icon_size) / 2)), icon_img)
    draw.text((x + pad_x + icon_size + icon_gap, y + h / 2), text, text_fill, font, 'lm')
    return w

def _draw_fixed_text_badge(draw, x, y, w, text, font, fill, border, text_fill=None, h=35):
    text_fill = text_fill or fill
    _draw_round_rect(draw, (x, y, x + w, y + h), h // 2, (255, 255, 255), border)
    draw.text((x + w / 2, y + h / 2), text, text_fill, font, 'mm')

def _draw_metric(img, draw, x, y, icon_path, label, value, percent, color, bg):
    percent_text = _format_percent(percent)
    text = f'{label}：{value} ({percent_text})'
    bbox = draw.textbbox((0, 0), text, font=rc_font_22)
    icon_size = 24
    w = min(350, bbox[2] - bbox[0] + icon_size + 44)
    _draw_round_rect(draw, (x, y, x + w, y + 34), 17, bg, color)
    if os.path.exists(icon_path):
        icon_img = Image.open(icon_path).convert('RGBA').resize((icon_size, icon_size), Image.LANCZOS)
        img.paste(icon_img, (int(x + 12), int(y + 5)), icon_img)
    draw.text((x + 42, y + 17), text, color, rc_font_22, 'lm')
    return w

async def draw_pet_home_brief(uid, pet_data, home_name):
    pet_items = list(pet_data.items())
    card_h = 210
    bg_height = max(500, 260 + len(pet_items) * card_h - 5)
    img = Image.open(TEXT_PATH / 'bg.jpg').convert('RGB')
    if bg_height > 2417:
        img = img.resize((1000, bg_height))
    else:
        img = img.crop((0, 0, 1000, bg_height))

    img.paste(top_bg, (0, 0), top_bg)
    img_draw = ImageDraw.Draw(img)
    img_draw.text((45, 90), f'{home_name}的家园精灵', (255, 255, 255), rc_font_44, 'lm')
    img_draw.text((45, 132), f'UID{uid} · 共{len(pet_items)}只', (255, 255, 255), skill_font_24, 'lm')

    for pet_index, (gid, pet_info) in enumerate(pet_items):
        y0 = 210 + pet_index * card_h
        pet_base = await get_pet_info(pet_info.pet_id)
        card = Image.new('RGBA', (940, 195), (255, 255, 255, 235))
        card_mask = Image.new('L', (940, 195), 0)
        ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, 940, 195), radius=18, fill=255)
        img.paste(card, (30, y0), card_mask)

        first_attr = pet_base.get('unit_type_list', pet_base.get('unit_type', [2]))[0]
        attr_color = _get_attr_draw_info(first_attr)[0]
        head_bg = Image.new('RGBA', (142, 142), attr_color)
        head_mask = pet_bg_mask.resize((142, 142))
        img.paste(head_bg, (55, y0 + 23), head_mask)

        pet_icon_name = pet_base['icon']
        if pet_info.mutation_type in [9, 1]:
            pet_icon_name = pet_base['icon'] + '_yise'
        pet_head_icon = ROCOM_ICON_PATH / f'{pet_icon_name}.png'
        if not os.path.exists(pet_head_icon):
            pet_head_icon = ROCOM_HEAD_PATH / f'{pet_info.pet_id}.png'
        if not os.path.exists(pet_head_icon):
            pet_head_icon = ROCOM_HEAD_PATH / '3004.png'
        pokemon_img = Image.open(pet_head_icon).convert('RGBA').resize((138, 138), Image.LANCZOS)
        img.paste(pokemon_img, (57, y0 + 25), pokemon_img)
        if pet_info.mutation_type in [1, 8, 9]:
            star_img = Image.open(TEXT_PATH / f'star_{pet_info.mutation_type}.png').convert('RGBA').resize((46, 46))
            img.paste(star_img, (160, y0 + 18), star_img)

        gender_text = '♀ 雌性' if pet_info.gender == 2 else '♂ 雄性' if pet_info.gender == 1 else '未知'
        gender_color = (236, 73, 118) if pet_info.gender == 2 else (69, 145, 237)
        _draw_fixed_text_badge(img_draw, 78, y0 + 133, 96, gender_text, rc_font_18, gender_color, (255, 207, 218), gender_color, h=30)
        img_draw.text((125, y0 + 173), f'GID {gid}', (95, 106, 122), rc_font_18, 'mm')

        img_draw.text((235, y0 + 35), f'Lv.{pet_info.level}', (80, 96, 116), rc_font_22, 'lm')
        pet_name = pet_info.name or pet_base.get('name', '')
        img_draw.text((330, y0 + 35), pet_name, (27, 37, 52), rc_font_34, 'lm')
        mutation_name = _get_mutation_name(pet_info)
        if mutation_name != '普通':
            star_path = TEXT_PATH / f'star_{pet_info.mutation_type}.png'
            text_bbox = img_draw.textbbox((0, 0), mutation_name, font=rc_font_22)
            mutation_text_w = text_bbox[2] - text_bbox[0]
            mutation_text_x = 950 - mutation_text_w
            mutation_star_x = mutation_text_x - 38
            if os.path.exists(star_path):
                star_img = Image.open(star_path).convert('RGBA').resize((34, 34))
                img.paste(star_img, (int(mutation_star_x), y0 + 18), star_img)
            img_draw.text((mutation_text_x, y0 + 35), mutation_name, (154, 60, 34), rc_font_22, 'lm')

        extra_tag_y = y0 + 75 if mutation_name != '普通' else y0 + 20
        extra_tags = []
        weight_badge_info = _get_weight_badge_info(pet_info, pet_base)
        if weight_badge_info:
            weight_badge_text, weight_badge_icon = weight_badge_info
            extra_tags.append((weight_badge_text, weight_badge_icon, (199, 96, 22), (255, 222, 195)))
        voice_badge_info = _get_voice_badge_info(pet_info)
        if voice_badge_info:
            voice_badge_text, voice_badge_icon = voice_badge_info
            extra_tags.append((voice_badge_text, voice_badge_icon, (0, 137, 125), (203, 251, 240)))
        if extra_tags:
            tag_gap = 8
            extra_tag_widths = [_measure_brief_tag(img_draw, tag[0]) for tag in extra_tags]
            extra_tag_x = 950 - sum(extra_tag_widths) - tag_gap * (len(extra_tags) - 1)
            for tag_width, (tag_text, tag_icon, tag_fill, tag_border) in zip(extra_tag_widths, extra_tags):
                _draw_brief_tag(img, img_draw, extra_tag_x, extra_tag_y, tag_text, tag_icon, tag_fill, tag_border)
                extra_tag_x += tag_width + tag_gap

        badge_x = 235
        for shuxing in pet_base.get('unit_type', []):
            attr_color, attr_name, _ = _get_attr_draw_info(shuxing)
            blood_icon = TEXT_PATH / '血脉' / f'{pet_info.blood_id}.png'
            badge_x += _draw_icon_text_badge(img, img_draw, badge_x, y0 + 63, blood_icon, f'血脉：{attr_name}', rc_font_22, attr_color, (232, 229, 255), attr_color, pad_x=12, h=34) + 10
            break
        nature_name = _get_nature_name(pet_info.nature)
        badge_x += _draw_text_badge(img_draw, badge_x, y0 + 63, f'性格：{nature_name}', rc_font_22, (207, 92, 24), (255, 222, 195), (207, 92, 24), pad_x=12, h=34) + 10
        speciality_name = _get_speciality_name(pet_info, pet_base)
        if speciality_name:
            _draw_text_badge(img_draw, badge_x, y0 + 60, f'特长：{speciality_name}', rc_font_22, (78, 83, 224), (220, 226, 255), (78, 83, 224), pad_x=12, h=34)

        voice_text = f'{getattr(pet_info, "voice", "--")} dB' if getattr(pet_info, 'voice', None) not in [None, ''] else '--'
        _draw_metric(img, img_draw, 235, y0 + 105, TEXT_PATH / 'voice.png', '声音', voice_text, _get_metric_percent(pet_info, pet_base, 'voice'), (0, 137, 125), (203, 251, 240))
        height_w = _draw_metric(img, img_draw, 235, y0 + 145, TEXT_PATH / 'height.png', '身高', _format_height(getattr(pet_info, 'height', None)), _get_metric_percent(pet_info, pet_base, 'height'), (0, 121, 177), (214, 242, 255))
        weight_x = max(465, 235 + height_w + 16)
        _draw_metric(img, img_draw, weight_x, y0 + 145, TEXT_PATH / 'weight.png', '体重', _format_weight(getattr(pet_info, 'weight', None)), _get_metric_percent(pet_info, pet_base, 'weight'), (199, 96, 22), (255, 247, 220))

    img.paste(footer, (270, bg_height - 44), footer)
    res = await convert_img(img)
    return res

async def _draw_home_skill(skill, size: str = 'small'):
    info_skill = await get_skill_info(skill.id)
    family = info_skill.get('families', '无')
    if family == 'SDT_NONE':
        family = '无'
    bg_color = SHUX_SKILLLIST_DRAW.get(family, SHUX_SKILLLIST_DRAW['无'])
    if size == 'equip':
        card_w, card_h = 160, 64
        icon_size = 54
        family_size = 34
        name_font = skill_font_16
        cost_font = skill_font_16
        name_xy = (66, 24)
        star_xy = (127, 36)
        cost_xy = (66, 47)
    else:
        card_w, card_h = 130, 62
        icon_size = 47
        family_size = 30
        name_font = skill_font_16
        cost_font = skill_font_16
        name_xy = (58, 22)
        star_xy = (102, 32)
        cost_xy = (58, 42)

    skill_card_bg = skill_bg.resize((card_w, card_h))
    jineng_img = Image.new('RGBA', (card_w, card_h), bg_color)
    jineng_temp = Image.new('RGBA', (card_w, card_h))
    jineng_temp.paste(jineng_img, (0, 0), skill_card_bg)

    icon_path = ROCOM_SKILL_PATH / f"{skill.iconid}.png"
    if not os.path.exists(icon_path):
        icon_path = ROCOM_SKILL_PATH / f"{skill.id}.png"
    if not os.path.exists(icon_path):
        icon_path = ROCOM_SKILL_PATH / 'img_linshi.png'
    skill_image = Image.open(icon_path).convert('RGBA').resize((icon_size, icon_size))
    jineng_temp.paste(skill_image, (10, int((card_h - icon_size) / 2)), skill_image)

    family_icon = TEXT_PATH / '属性' / f"{family}.png"
    if not os.path.exists(family_icon):
        family_icon = TEXT_PATH / '属性' / '2.png'
    sx_image = Image.open(family_icon).convert('RGBA').resize((family_size, family_size))
    jineng_temp.paste(sx_image, (-4, -4), sx_image)

    jineng_draw = ImageDraw.Draw(jineng_temp)
    max_name_len = 4
    skill_name = skill.name if len(skill.name) <= max_name_len else f'{skill.name[:max_name_len]}…'
    jineng_draw.text(name_xy, skill_name, (255, 255, 255), name_font, 'lm')
    star_img = cost_star.resize((18, 18))
    jineng_temp.paste(star_img, star_xy, star_img)
    jineng_draw.text(cost_xy, f"{info_skill.get('cost', 0)}", (255, 255, 255), cost_font, 'lm')
    return jineng_temp

async def draw_pet_home(uid, pet_data, home_name):
    pet_items = list(pet_data.items())
    card_h = 420
    bg_height = max(850, 360 + len(pet_items) * card_h + 70)
    img = Image.open(TEXT_PATH / 'bg.jpg').convert('RGB')
    if bg_height > 2417:
        img = img.resize((1200, bg_height))
    else:
        img = img.crop((0, 0, 1200, bg_height))

    img.paste(info_title_img, (0, 0), info_title_img)
    img_draw = ImageDraw.Draw(img)
    img_draw.text((600, 96), '精灵状态', (255, 255, 255), rc_font_72, 'mm')

    title_bar = Image.new('RGBA', (960, 105), (218, 213, 194, 180))
    title_mask = Image.new('L', (960, 105), 0)
    ImageDraw.Draw(title_mask).rounded_rectangle((0, 0, 960, 105), radius=52, fill=255)
    img.paste(title_bar, (120, 205), title_mask)
    img_draw.text((600, 258), f'{home_name}的小屋', info_text_color, rc_font_44, 'mm')
    img_draw.text((1050, 281), f'UID{uid}', info_text_color, rc_font_30, 'rm')

    for pet_index, (gid, pet_info) in enumerate(pet_items):
        y0 = 350 + pet_index * card_h
        pet_base = await get_pet_info(pet_info.pet_id)
        pet_name = f'{pet_info.name}{gid}'
        name_bar = Image.new('RGBA', (250, 66), (218, 213, 194, 165))
        name_mask = Image.new('L', (250, 66), 0)
        ImageDraw.Draw(name_mask).rounded_rectangle((0, 0, 250, 66), radius=33, fill=255)
        img.paste(name_bar, (6, y0 + 10), name_mask)
        img_draw.text((131, y0 + 43), pet_name, info_text_color, rc_font_22, 'mm')

        pet_icon_name = pet_base['icon']
        if pet_info.mutation_type in [9, 1]:
            pet_icon_name = pet_base['icon'] + '_yise'
        pet_head_icon = ROCOM_ICON_PATH / f'{pet_icon_name}.png'
        if not os.path.exists(pet_head_icon):
            pet_head_icon = ROCOM_HEAD_PATH / 'dimo.png'
        first_attr = pet_base.get('unit_type_list', pet_base.get('unit_type', [2]))[0]
        pet_bg_img = Image.new('RGBA', (235, 235), _get_attr_draw_info(first_attr)[0])
        pet_bg_small = pet_bg_mask.resize((235, 235))
        img.paste(pet_bg_img, (18, y0 + 88), pet_bg_small)
        pokemon_img = Image.open(pet_head_icon).convert('RGBA').resize((230, 230))
        img.paste(pokemon_img, (20, y0 + 90), pokemon_img)
        voice_badge_text = _get_voice_badge_text(pet_info)
        if voice_badge_text:
            voice_badge = _draw_home_badge(voice_badge_text)
            img.paste(voice_badge, (10, y0 + 84), voice_badge)
        if pet_info.mutation_type in [1, 8, 9]:
            star_img = Image.open(TEXT_PATH / f'star_{pet_info.mutation_type}.png').convert('RGBA').resize((68, 68))
            img.paste(star_img, (198, y0 + 270), star_img)

        img.paste(home_title_small, (276, y0 + 4), home_title_small)
        img_draw.text((329, y0 + 27), '精灵属性', (255, 255, 255), rc_font_16, 'lm')
        table_small = table_img.resize((250, 174))
        img.paste(table_small, (273, y0 + 55), table_small)
        attribute_items = [
            pet_info.attribute_info.pethp,
            pet_info.attribute_info.petatk,
            pet_info.attribute_info.petspatk,
            pet_info.attribute_info.petdef,
            pet_info.attribute_info.petspdef,
            pet_info.attribute_info.petspd,
        ]
        attr_icon = ['HP', '物攻', '魔攻', '物防', '魔防', '速度']
        for i, sx_item in enumerate(attribute_items):
            row_y = y0 + 98 + i * 24
            img_draw.text((310, row_y), attr_icon[i], info_text_color, rc_font_18, 'lm')
            for j, key in enumerate(attribute_tag):
                tag_small = tags_img.resize((52, 20))
                x = 360 + j * 58
                tag_y = row_y - 11
                img.paste(tag_small, (x, tag_y), tag_small)
                img_draw.text((x + 26, tag_y + 10), f"{getattr(sx_item, key)}", (240, 236, 225), rc_font_18, 'mm')

        attr_badges = []
        seen_attr_names = set()
        for shuxing in pet_base['unit_type']:
            attr_color, attr_name, attr_icon = _get_attr_draw_info(shuxing)
            if attr_name in seen_attr_names:
                continue
            seen_attr_names.add(attr_name)
            attr_badges.append((attr_color, attr_name, TEXT_PATH / '属性' / f'{attr_icon}.png'))
        if pet_info.blood_id in XUEMAI_LIST_DRAW:
            blood_color, blood_name = XUEMAI_LIST_DRAW[pet_info.blood_id]
            if blood_name not in seen_attr_names:
                attr_badges.append((blood_color, blood_name, TEXT_PATH / '血脉' / f'{pet_info.blood_id}.png'))

        compact_attr_badges = len(attr_badges) >= 3
        attr_tag_w = 82 if compact_attr_badges else 92
        attr_tag_h = 25
        attr_tag_gap = 84 if compact_attr_badges else 96
        attr_icon_size = 23 if compact_attr_badges else 25
        attr_text_x = 50 if compact_attr_badges else 54
        attr_font = rc_font_16 if compact_attr_badges else rc_font_18
        for shul, (attr_color, attr_name, attr_icon_path) in enumerate(attr_badges):
            attr_tag_x = 283 + attr_tag_gap * shul
            shuxing_img = Image.new('RGBA', (attr_tag_w, attr_tag_h), attr_color)
            sx_image = Image.open(attr_icon_path).convert('RGBA').resize((attr_icon_size, attr_icon_size))
            shuxing_img.paste(sx_image, (-2, 0), sx_image)
            shuxing_temp = Image.new('RGBA', (attr_tag_w, attr_tag_h))
            shuxing_temp.paste(shuxing_img, (0, 0), mask_bar.resize((attr_tag_w, attr_tag_h)))
            ImageDraw.Draw(shuxing_temp).text((attr_text_x, 13), f'{attr_name}', (255, 255, 255), attr_font, 'mm')
            img.paste(shuxing_temp, (attr_tag_x, y0 + 238), shuxing_temp)

        img.paste(home_title_small, (276, y0 + 270), home_title_small)
        img_draw.text((329, y0 + 293), '精灵特性', (255, 255, 255), rc_font_16, 'lm')
        tx_icon = ROCOM_CHARACTER_PATH / f"{pet_info.feature.id}.png"
        if not os.path.exists(tx_icon):
            tx_icon = ROCOM_CHARACTER_PATH / '200191.png'
        tx_img = Image.open(tx_icon).convert('RGBA').resize((58, 58))
        skill_mask_small = skill_mask.resize((58, 58))
        img.paste(tx_img, (283, y0 + 322), skill_mask_small)
        img_draw.text((354, y0 + 332), f"{pet_info.feature.name}", (0, 0, 0), rc_font_18, 'lm')
        tx_lines = await get_text_line(f'{pet_info.feature.desc}', 14)
        for line_i, line in enumerate(tx_lines[:4]):
            img_draw.text((354, y0 + 353 + line_i * 16), line, info_text_color, rc_font_14, 'lm')

        skill_area_x = 545
        skill_title_x = skill_area_x - 5
        img.paste(home_title_small, (skill_title_x, y0 + 4), home_title_small)
        img_draw.text((skill_title_x + 53, y0 + 27), '装备技能', (255, 255, 255), rc_font_16, 'lm')
        equip_skills = sorted(pet_info.equip_skills, key=lambda item: item.pos)
        for i, skill in enumerate(equip_skills[:4]):
            skill_img = await _draw_home_skill(skill, 'equip')
            img.paste(skill_img, (skill_area_x + i * 160, y0 + 58), skill_img)

        img.paste(home_title_small, (skill_title_x, y0 + 128), home_title_small)
        img_draw.text((skill_title_x + 53, y0 + 151), '已学技能', (255, 255, 255), rc_font_16, 'lm')
        for i, skill in enumerate(pet_info.skills[:17]):
            row = math.floor(i / 5)
            col = i - row * 5
            skill_img = await _draw_home_skill(skill, 'small')
            img.paste(skill_img, (skill_area_x + col * 128, y0 + 176 + row * 60), skill_img)

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
        if pet_info.mutation_type in [9, 1]:
            overlay_img = copy.deepcopy(yise_overlay)
            pet_head_icon = ROCOM_HEAD_PATH / f'{pet_info.pet_id}_1.png'
        else:
            overlay_img = copy.deepcopy(xuancai_overlay)
            pet_head_icon = ROCOM_HEAD_PATH / f'{pet_info.pet_id}.png'
        if not os.path.exists(pet_head_icon):
            pet_head_icon = ROCOM_HEAD_PATH / '3004.png'
        head_img = Image.open(pet_head_icon).convert('RGBA').resize((130, 130))
        pet_base = await get_pet_info(pet_info.pet_id)
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
        xm_img = Image.open(TEXT_PATH / '血脉' / f'{pet_info.blood_id}.png').convert('RGBA').resize((45, 45))
        rocom_img.paste(xm_img, (110, -5), xm_img)
        #画标志
        if pet_info.mutation_type in [1, 8, 9]:
            star_img = Image.open(TEXT_PATH / f'star_{pet_info.mutation_type}.png')
            rocom_img.paste(star_img, (6, 110), star_img)
        #画等级
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
        rocom_img.paste(level_img, (69, 110), level_img)
        #画昵称
        rocom_draw = ImageDraw.Draw(rocom_img)
        rocom_draw.text(
            (75, 170),
            f'{pet_info.name}',
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
