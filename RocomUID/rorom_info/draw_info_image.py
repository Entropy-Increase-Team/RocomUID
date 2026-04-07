import re
import math
from pathlib import Path
import os
import time
from PIL import Image, ImageDraw
from ..utils.image.image_tools import get_text_line
from gsuid_core.utils.image.convert import convert_img
from ..utils.resource.RESOURCE_PATH import ROCOM_ICON_PATH, ROCOM_SKILL_PATH, ROCOM_CHARACTER_PATH
from ..utils.map.rocom_map import rocom_group_list, rocom_list, rocom_skill_list, characteristic_list, skill_list, rocom_evolution_list
from ..utils.fonts.rocom_fonts import rc_font_28, rc_font_30, rc_font_32, rc_font_34, rc_font_40, rc_font_64, rc_font_72, skill_font_22, skill_font_32

TEXT_PATH = Path(__file__).parent / 'texture2D'
mask_bar = Image.open(TEXT_PATH / 'mask_bar.png')
skill_bg = Image.open(TEXT_PATH / 'skill_bg.png')
table_img = Image.open(TEXT_PATH / 'table.png')
tags_img = Image.open(TEXT_PATH / 'tags.png')
info_title_img = Image.open(TEXT_PATH / 'title.png')
poro_bar = Image.open(TEXT_PATH / 'poro_bar.png')
pet_bg_mask = Image.open(TEXT_PATH / 'pet_bg.png').convert('RGBA').resize((575, 575))
rocom_title = Image.open(TEXT_PATH / 'a_title.png')
right_jinhua = Image.open(TEXT_PATH / 'right_jinhua.png')
up_title = Image.open(TEXT_PATH / 'up_title.png')
jinhua_bg = Image.open(TEXT_PATH / 'jinhua_bg.png')
skill_mask = Image.open(TEXT_PATH / 'skill_mask.png')
cost_star = Image.open(TEXT_PATH / 'star.png')
footer = Image.open(TEXT_PATH / 'footer.png')
info_text_color = (100, 92, 79)

SHUX_LIST_XX = ['物攻', '魔攻', '物防', '魔防', '速度']
SHUX_LIST_DRAW = {
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

jinhua_icon_list = {
    '1_0':220,
    '2_0':70,
    '2_1':290,
    '3_0':0,
    '3_1':220,
    '3_2':440,
}

tag_w_add = [0, 132, 143]

tag_title = ['HP', '物攻', '魔攻', '物防', '魔防', '速度']

async def get_max_shuxing_num(zhongzu, shuxing_type = ''):
    #计算基础属性 (种族值 + 个体值/2)/2 + 10
    jichu_num = (zhongzu + 30)/2 + 10
    #计算洛克系数 (种族值 + 个体值/2)/100
    xishu = (zhongzu + 30)/100
    #生命系数计算翻倍((种族值 + 个体值/2)/100) * 2 + 1
    if shuxing_type == 'HP':
        xishu = xishu * 2 + 1
    #计算属性最大值向上取整
    shuxing_num = math.floor((jichu_num + (xishu * 60)) * 1.2 + 50)
    return shuxing_num

async def get_min_shuxing_num(zhongzu, shuxing_type = ''):
    #计算基础属性 (种族值 + 个体值/2)/2 + 10
    jichu_num = zhongzu/2 + 10
    #计算洛克系数 (种族值 + 个体值/2)/100
    xishu = zhongzu/100
    #生命系数计算翻倍((种族值 + 个体值/2)/100) * 2 + 1
    if shuxing_type == 'HP':
        xishu = xishu * 2 + 1
    #计算属性最小值向下取整
    shuxing_num = math.floor((jichu_num + (xishu * 60)) * 0.9 + 50)
    return shuxing_num

async def draw_rocom_info(rocomname):
    rocom_info = rocom_list[rocomname]
    bg_height = 1030
    skill_level_list = rocom_skill_list[rocomname][0]
    skill_level_num = len(skill_level_list)
    if skill_level_num > 0:
        bg_height += math.ceil(skill_level_num / 5) * 99 + 80
    
    skill_blood_list = rocom_skill_list[rocomname][1]
    if len(skill_blood_list) > 0:
        skill_blood_num = len(skill_blood_list)
        if skill_blood_num > 0:
            bg_height += math.ceil(skill_blood_num / 5) * 99 + 80
    
    skill_stone_list = rocom_skill_list[rocomname][2]
    if len(skill_stone_list) > 0:
        skill_stone_num = len(skill_stone_list)
        if skill_stone_num > 0:
            bg_height += math.ceil(skill_stone_num / 5) * 99 + 80
    
    tx_line_height = 0
    txname = rocom_list[rocomname][7]
    tx_content = characteristic_list.get(txname, '')
    txname_para = await get_text_line(f'{tx_content}', 28)
    tx_line_height += len(txname_para) * 40
    tx_line_height += 120
    tx_line_height = max(210, tx_line_height)
    
    bg_height += tx_line_height + 80
    miaoshu = rocom_list[rocomname][9]
    miaoshu_para = await get_text_line(miaoshu, 31)
    miaoshu_height = len(miaoshu_para) * 40
    if rocom_group_list.get(rocomname, 0) != 0:
        if rocom_group_list[rocomname][0] != '无':
            miaoshu_height = miaoshu_height + 40
    bg_height += miaoshu_height
    bg_height += 80
    
    img = Image.open(TEXT_PATH / 'bg.jpg').convert('RGB').resize((1200, bg_height))
    
    # img = Image.new('RGBA', (900, bg_height + 124), (231, 225, 203, 180))
    # img.paste(info_top_img, (0, 0))
    # bg_center = Image.open(TEXT_PATH / 'bg_center.jpg').resize(
        # (900, bg_height)
    # )
    # img.paste(bg_center, (0, 62))
    # img.paste(info_bottom_img, (0, bg_height + 62))
    img.paste(info_title_img, (0, 0), info_title_img)
    img_draw = ImageDraw.Draw(img)
    # 画名称标题
    
    img_draw.text(
        (600, 96),
        f'精灵图鉴',
        (255, 255, 255),
        rc_font_72,
        'mm',
    )
    img_draw.text(
        (600, 260),
        f'{rocomname}',
        info_text_color,
        rc_font_64,
        'mm',
    )
    pet_bg_img = Image.new('RGBA', (575, 575), SHUX_LIST_DRAW[rocom_info[6][0]])
    
    img.paste(pet_bg_img, (-6, 359), pet_bg_mask)
    # 画形象
    pokemon_img = (
        Image.open(ROCOM_ICON_PATH / f'{rocomname}.png')
        .convert('RGBA')
        .resize((552, 552))
    )
    img.paste(pokemon_img, (0, 371), pokemon_img)
    img.paste(rocom_title, (565, 334), rocom_title)
    img_draw.text(
        (631, 363),
        f'精灵种族',
        (255, 255, 255),
        rc_font_28,
        'lm',
    )
    img.paste(table_img, (550, 405), table_img)
    
    
    # 画种族
    x_num = 730
    y_num = 483
    for index_x in range(0, 3):
        x_num = x_num + tag_w_add[index_x]
        for index_y in range(0, 6):
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
                    f'{rocom_info[index_y]}',
                    (240, 236, 225),
                    rc_font_32,
                    'mm',
                )
            elif index_x == 1:
                if index_y == 0:
                    min_num = await get_min_shuxing_num(rocom_info[index_y], 'HP')
                else:
                    min_num = await get_min_shuxing_num(rocom_info[index_y])
                img_draw.text(
                    (tag_x + 58, tag_y + 22),
                    f'{min_num}',
                    (240, 236, 225),
                    rc_font_32,
                    'mm',
                )
            else:
                if index_y == 0:
                    max_num = await get_max_shuxing_num(rocom_info[index_y], 'HP')
                else:
                    max_num = await get_max_shuxing_num(rocom_info[index_y])
                img_draw.text(
                    (tag_x + 58, tag_y + 22),
                    f'{max_num}',
                    (240, 236, 225),
                    rc_font_32,
                    'mm',
                )
    
    # 画进化链
    x_num = 565
    y_num = 820
    # +166 863 905
    jinhua_num = len(rocom_evolution_list[rocomname][0])
    for index, jinhua_name in enumerate(rocom_evolution_list[rocomname][0]):
        icon_x = x_num + jinhua_icon_list[f'{jinhua_num}_{index}']
        img.paste(jinhua_bg, (icon_x, y_num), jinhua_bg)
        pokemon_img = Image.open(ROCOM_ICON_PATH / f'{jinhua_name}.png').convert('RGBA').resize((150, 150))
        img.paste(pokemon_img, (icon_x - 5, y_num + 10), pokemon_img)
        img_draw.text(
            (icon_x + 70, y_num + 180),
            f'{jinhua_name}',
            (60, 60, 60),
            rc_font_28,
            'mm',
        )
        if jinhua_num > 1 and index > 0:
            img.paste(right_jinhua, (icon_x - 54, 863), right_jinhua)
            img_draw.text(
                (icon_x - 54, 905),
                f'{rocom_evolution_list[rocomname][1][index - 1]}',
                info_text_color,
                rc_font_28,
                'mm',
            )
    if rocom_evolution_list[rocomname][2] != '':
        img_draw.text(
            (861, 1040),
            f'{rocom_evolution_list[rocomname][2]}',
            info_text_color,
            rc_font_34,
            'mm',
        )
    
    # 画属性类型
    for shul, shuxing in enumerate(rocom_info[6]):
        shuxing_img = Image.new('RGBA', (142, 38), SHUX_LIST_DRAW[shuxing])
        sx_image = Image.open(TEXT_PATH / f'{shuxing}.png').convert('RGBA').resize((42, 42))
        shuxing_img.paste(sx_image, (-2, -2), sx_image)
        shuxing_temp = Image.new('RGBA', (142, 38))
        shuxing_temp.paste(shuxing_img, (0, 0), mask_bar)
        shuxing_draw = ImageDraw.Draw(shuxing_temp)
        shuxing_draw.text(
            (91, 19),
            f'{shuxing}',
            (255, 255, 255),
            rc_font_32,
            'mm',
        )
        img.paste(shuxing_temp, (150 * shul + 90, 970), shuxing_temp)
    
    start_height = 1030
    img.paste(rocom_title, (68, start_height), rocom_title)
    img_draw.text(
        (134, start_height + 30),
        f'精灵信息',
        (255, 255, 255),
        rc_font_28,
        'lm',
    )
    start_height += 80
    miaoshu_h = 0
    if rocom_group_list[rocomname][0] != '无':
        danzu_str = ' '.join(rocom_group_list[rocomname])
        img_draw.text(
            (90, start_height),
            f"蛋组：{danzu_str}",
            info_text_color,
            rc_font_34,
            'lm',
        )
        start_height += 40
    for line in miaoshu_para:
        img_draw.text(
            (90, start_height),
            line,
            info_text_color,
            skill_font_32,
            'lm',
        )
        start_height += 40
    start_height += 15
    img.paste(rocom_title, (68, start_height), rocom_title)
    img_draw.text(
        (134, start_height + 30),
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
    #skill_bg
    if len(skill_level_list) > 0:
        img.paste(rocom_title, (68, start_height), rocom_title)
        img_draw.text(
            (134, start_height + 30),
            f'等级技能',
            (255, 255, 255),
            rc_font_28,
            'lm',
        )
        start_height += 70
        jn_y = 0
        for shul, jineng in enumerate(skill_level_list):
            jn_y = math.floor(shul / 5)
            jn_x = shul - (5 * jn_y)
            jineng_img = Image.new(
                'RGBA', (207, 99), SHUX_LIST_DRAW[skill_list[jineng][0]]
            )
            skill_image = Image.open(ROCOM_SKILL_PATH / f'{jineng}.png').convert('RGBA').resize((67, 67))
            jineng_temp = Image.new('RGBA', (207, 99))
            jineng_temp.paste(jineng_img, (0, 0), skill_bg)
            jineng_temp.paste(skill_image, (15, 16), skill_image)
            sx_image = Image.open(TEXT_PATH / f'{skill_list[jineng][0]}.png').convert('RGBA').resize((45, 45))
            jineng_temp.paste(sx_image, (-5, -5), sx_image)
            jineng_draw = ImageDraw.Draw(jineng_temp)
            jineng_draw.text(
                (94, 35),
                f'{jineng}',
                (255, 255, 255),
                skill_font_22,
                'lm',
            )
            jineng_temp.paste(cost_star, (92, 52), cost_star)
            jineng_draw.text(
                (120, 65),
                f'{skill_list[jineng][1]}',
                (255, 255, 255),
                skill_font_22,
                'lm',
            )
            img.paste(
                jineng_temp, (208 * jn_x + 82, jn_y * 99 + start_height), jineng_temp
            )
        start_height += (jn_y + 1) * 99 + 10
    
    if len(skill_blood_list) > 0:
        img.paste(rocom_title, (68, start_height), rocom_title)
        img_draw.text(
            (134, start_height + 30),
            f'血脉技能',
            (255, 255, 255),
            rc_font_28,
            'lm',
        )
        start_height += 70
        jn_y = 0
        for shul, jineng in enumerate(skill_blood_list):
            jn_y = math.floor(shul / 5)
            jn_x = shul - (5 * jn_y)
            jineng_img = Image.new(
                'RGBA', (207, 99), SHUX_LIST_DRAW[skill_list[jineng][0]]
            )
            skill_image = Image.open(ROCOM_SKILL_PATH / f'{jineng}.png').convert('RGBA').resize((67, 67))
            jineng_temp = Image.new('RGBA', (207, 99))
            jineng_temp.paste(jineng_img, (0, 0), skill_bg)
            jineng_temp.paste(skill_image, (15, 16), skill_image)
            sx_image = Image.open(TEXT_PATH / f'{skill_list[jineng][0]}.png').convert('RGBA').resize((45, 45))
            jineng_temp.paste(sx_image, (-5, -5), sx_image)
            jineng_draw = ImageDraw.Draw(jineng_temp)
            jineng_draw.text(
                (94, 35),
                f'{jineng}',
                (255, 255, 255),
                skill_font_22,
                'lm',
            )
            jineng_temp.paste(cost_star, (92, 52), cost_star)
            jineng_draw.text(
                (120, 65),
                f'{skill_list[jineng][1]}',
                (255, 255, 255),
                skill_font_22,
                'lm',
            )
            img.paste(
                jineng_temp, (208 * jn_x + 82, jn_y * 99 + start_height), jineng_temp
            )
        
        start_height += (jn_y + 1) * 99 + 10
    
    yc_y = 0
    if len(skill_stone_list) > 0:
        img.paste(rocom_title, (68, start_height), rocom_title)
        img_draw.text(
            (134, start_height + 30),
            f'技能石技能',
            (255, 255, 255),
            rc_font_28,
            'lm',
        )
        start_height += 70
        jn_y = 0
        for shul, jineng in enumerate(skill_stone_list):
            jn_y = math.floor(shul / 5)
            jn_x = shul - (5 * jn_y)
            jineng_img = Image.new(
                'RGBA', (207, 99), SHUX_LIST_DRAW[skill_list[jineng][0]]
            )
            skill_image = Image.open(ROCOM_SKILL_PATH / f'{jineng}.png').convert('RGBA').resize((67, 67))
            jineng_temp = Image.new('RGBA', (207, 99))
            jineng_temp.paste(jineng_img, (0, 0), skill_bg)
            jineng_temp.paste(skill_image, (15, 16), skill_image)
            sx_image = Image.open(TEXT_PATH / f'{skill_list[jineng][0]}.png').convert('RGBA').resize((45, 45))
            jineng_temp.paste(sx_image, (-5, -5), sx_image)
            jineng_draw = ImageDraw.Draw(jineng_temp)
            jineng_draw.text(
                (94, 35),
                f'{jineng}',
                (255, 255, 255),
                skill_font_22,
                'lm',
            )
            jineng_temp.paste(cost_star, (92, 52), cost_star)
            jineng_draw.text(
                (120, 65),
                f'{skill_list[jineng][1]}',
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