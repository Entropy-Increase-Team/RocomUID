import re
import math
from pathlib import Path
import os
import time
from PIL import Image, ImageDraw
from ..utils.image.image_tools import get_text_line
from gsuid_core.utils.image.convert import convert_img
from ..utils.resource.RESOURCE_PATH import ROCOM_ICON_PATH, ROCOM_SKILL_PATH
from ..utils.map.rocom_map import rocom_group_list, rocom_list, rocom_skill_list, characteristic_list, skill_list
from ..utils.fonts.rocom_fonts import rc_font_15, rc_font_18, rc_font_26, rc_font_28, rc_font_32, rc_font_40
from gsuid_core.utils.image.image_tools import draw_pic_with_ring

TEXT_PATH = Path(__file__).parent / 'texture2D'
mask_bar = Image.open(TEXT_PATH / 'mask_bar.png')
# info_top_img = Image.open(TEXT_PATH / 'bg_top.jpg')
# info_bottom_img = Image.open(TEXT_PATH / 'bg_bottom.jpg')
info_title_img = Image.open(TEXT_PATH / 'title.png')
poro_bar = Image.open(TEXT_PATH / 'poro_bar.png')
skill_title = Image.open(TEXT_PATH / 'skill_title.png')
# up_title = Image.open(TEXT_PATH / 'up_title.png')
info_text_color = (232, 222, 179)
black_color = (0, 0, 0)

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

async def get_max_shuxing_num(zhongzu, shuxing_type = ''):
    #计算基础属性 (种族值 + 个体值/2)/2 + 10
    jichu_num = (zhongzu + 30)/2 + 10
    #计算洛克系数 (种族值 + 个体值/2)/100
    xishu = (zhongzu + 30)/100
    #生命系数计算翻倍((种族值 + 个体值/2)/100) * 2 + 1
    if shuxing_type == 'HP':
        xishu = xishu * 2 + 1
    #计算属性最大值向上取整
    shuxing_num = math.ceil((jichu_num + (xishu * 60)) * 1.2 + 50)
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
    bg_height = 600
    kuandu_lie = 180
    shul_lie = 4
    skill_level_list = rocom_skill_list[rocomname][0]
    skill_level_num = len(skill_level_list)
    if skill_level_num > 0:
        bg_height += math.ceil(skill_level_num / 4) * 45 + 130
    
    skill_blood_list = rocom_skill_list[rocomname][1]
    if len(skill_blood_list) > 0:
        skill_blood_num = len(skill_blood_list)
        if skill_blood_num > 0:
            bg_height += math.ceil(skill_blood_num / 4) * 45 + 100
    
    skill_stone_list = rocom_skill_list[rocomname][2]
    if len(skill_stone_list) > 0:
        skill_stone_num = len(skill_stone_list)
        if skill_stone_num > 0:
            bg_height += math.ceil(skill_stone_num / 4) * 45 + 100
    
    tx_line_height = 0
    txname = rocom_list[rocomname][7]
    txname_para = await get_text_line(f'{txname}：{characteristic_list[txname]}', 25)
    tx_line_height += len(txname_para) * 40
    
    bg_height += tx_line_height + 110
    
    miaoshu = rocom_list[rocomname][9]
    miaoshu_para = await get_text_line(miaoshu, 25)
    miaoshu_height = len(miaoshu_para) * 40
    if rocom_group_list.get(rocomname, 0) != 0:
        if rocom_group_list[rocomname][0] != '无':
            miaoshu_height = miaoshu_height + 80
    
    bg_height += miaoshu_height
    bg_height = max(bg_height, 1376)
    
    bg_img = Image.open(TEXT_PATH / 'bg.jpg').convert('RGB').resize((980, bg_height + 204))
    
    img = Image.new('RGBA', (900, bg_height + 124), (231, 225, 203, 180))
    # img.paste(info_top_img, (0, 0))
    # bg_center = Image.open(TEXT_PATH / 'bg_center.jpg').resize(
        # (900, bg_height)
    # )
    # img.paste(bg_center, (0, 62))
    # img.paste(info_bottom_img, (0, bg_height + 62))
    img.paste(info_title_img, (0, 41), info_title_img)
    img_draw = ImageDraw.Draw(img)
    # 画名称标题
    
    img_draw.text(
        (285, 121),
        f'{rocomname}',
        info_text_color,
        rc_font_40,
        'mm',
    )
    img_draw.text(
        (516, 132),
        '种族',
        info_text_color,
        rc_font_32,
        'mm',
    )
    img_draw.text(
        (630, 132),
        '最小值',
        info_text_color,
        rc_font_32,
        'mm',
    )
    img_draw.text(
        (750, 132),
        '最大值',
        info_text_color,
        rc_font_32,
        'mm',
    )
    # 画形象
    pokemon_img = (
        Image.open(ROCOM_ICON_PATH / f'{rocomname}.png')
        .convert('RGBA')
        .resize((300, 300))
    )
    img.paste(pokemon_img, (70, 168), pokemon_img)
    
    # 画属性
    img.paste(poro_bar, (454, 170), poro_bar)
    img.paste(poro_bar, (454, 225), poro_bar)
    img.paste(poro_bar, (454, 280), poro_bar)
    img.paste(poro_bar, (454, 335), poro_bar)
    img.paste(poro_bar, (454, 390), poro_bar)
    img.paste(poro_bar, (454, 445), poro_bar)
    img_draw.text((413, 193), 'HP', (53, 77, 105), rc_font_28, 'mm')
    for shul, shux in enumerate(SHUX_LIST_XX):
        sx_color = (53, 77, 105)
        img_draw.text((413, 55 * shul + 248), shux, sx_color, rc_font_28, 'mm')
    # 种族
    img_draw.text((516, 193), f'{rocom_info[0]}', (0, 0, 0), rc_font_28, 'mm')
    img_draw.text((516, 248), f'{rocom_info[1]}', (0, 0, 0), rc_font_28, 'mm')
    img_draw.text((516, 303), f'{rocom_info[2]}', (0, 0, 0), rc_font_28, 'mm')
    img_draw.text((516, 358), f'{rocom_info[3]}', (0, 0, 0), rc_font_28, 'mm')
    img_draw.text((516, 413), f'{rocom_info[4]}', (0, 0, 0), rc_font_28, 'mm')
    img_draw.text((516, 468), f'{rocom_info[5]}', (0, 0, 0), rc_font_28, 'mm')
    # 最小属性
    MIN_HP = await get_min_shuxing_num(rocom_info[0], 'HP')
    img_draw.text(
        (630, 193), f'{MIN_HP}', (0, 0, 0), rc_font_28, 'mm'
    )
    MIN_atk = await get_min_shuxing_num(rocom_info[1])
    img_draw.text(
        (630, 248), f'{MIN_atk}', (0, 0, 0), rc_font_28, 'mm'
    )
    MIN_spatk = await get_min_shuxing_num(rocom_info[2])
    img_draw.text(
        (630, 303), f'{MIN_spatk}', (0, 0, 0), rc_font_28, 'mm'
    )
    MIN_def = await get_min_shuxing_num(rocom_info[3])
    img_draw.text(
        (630, 358), f'{MIN_def}', (0, 0, 0), rc_font_28, 'mm'
    )
    MIN_spdef = await get_min_shuxing_num(rocom_info[4])
    img_draw.text(
        (630, 413), f'{MIN_spdef}', (0, 0, 0), rc_font_28, 'mm'
    )
    MIN_spd = await get_min_shuxing_num(rocom_info[5])
    img_draw.text(
        (630, 468), f'{MIN_spd}', (0, 0, 0), rc_font_28, 'mm'
    )
    # 最大属性
    MAX_HP = await get_max_shuxing_num(rocom_info[0], 'HP')
    img_draw.text(
        (750, 193), f'{MAX_HP}', (0, 0, 0), rc_font_28, 'mm'
    )
    MAX_atk = await get_max_shuxing_num(rocom_info[1])
    img_draw.text(
        (750, 248), f'{MAX_atk}', (0, 0, 0), rc_font_28, 'mm'
    )
    MAX_spatk = await get_max_shuxing_num(rocom_info[2])
    img_draw.text(
        (750, 303), f'{MAX_spatk}', (0, 0, 0), rc_font_28, 'mm'
    )
    MAX_def = await get_max_shuxing_num(rocom_info[3])
    img_draw.text(
        (750, 358), f'{MAX_def}', (0, 0, 0), rc_font_28, 'mm'
    )
    MAX_spdef = await get_max_shuxing_num(rocom_info[4])
    img_draw.text(
        (750, 413), f'{MAX_spdef}', (0, 0, 0), rc_font_28, 'mm'
    )
    MAX_spd = await get_max_shuxing_num(rocom_info[5])
    img_draw.text(
        (750, 468), f'{MAX_spd}', (0, 0, 0), rc_font_28, 'mm'
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
            rc_font_28,
            'mm',
        )
        img.paste(shuxing_temp, (150 * shul + 82, 520), shuxing_temp)
    miaoshu_h = 0
    if rocom_group_list[rocomname][0] != '无':
        danzu_str = ' '.join(rocom_group_list[rocomname])
        img_draw.text(
            (91, 600),
            f"蛋组：{danzu_str}",
            black_color,
            rc_font_28,
            'lm',
        )
        miaoshu_h = 40
    for line in miaoshu_para:
        img_draw.text(
            (91, 600 + miaoshu_h),
            line,
            black_color,
            rc_font_28,
            'lm',
        )
        miaoshu_h += 40
    start_height = 600 + miaoshu_h + 10
    
    img.paste(skill_title, (77, start_height), skill_title)
    img_draw.text(
        (274, start_height + 37),
        '精灵特性',
        info_text_color,
        rc_font_40,
        'mm',
    )
    tx_line_h = 0
    for line in txname_para:
        img_draw.text(
            (91, start_height + tx_line_h + 110),
            line,
            black_color,
            rc_font_28,
            'lm',
        )
        tx_line_h += 40

    start_height = start_height + tx_line_h + 110
    
    djjn_height = 0
    jineng_bar_mask = mask_bar.copy()
    jineng_bar_mask = jineng_bar_mask.resize((kuandu_lie, 38))
    
    if len(skill_level_list) > 0:
        img.paste(skill_title, (77, start_height), skill_title)
        img_draw.text(
            (274, start_height + 37),
            '等级技能',
            info_text_color,
            rc_font_40,
            'mm',
        )
        jn_y = 0
        for shul, jineng in enumerate(skill_level_list):
            jn_y = math.floor(shul / shul_lie)
            jn_x = shul - (shul_lie * jn_y)
            jineng_img = Image.new(
                'RGBA', (kuandu_lie, 38), SHUX_LIST_DRAW[skill_list[jineng][0]]
            )
            sx_image = Image.open(ROCOM_SKILL_PATH / f'{jineng}.png').convert('RGBA').resize((38, 38))
            jineng_img.paste(
                sx_image, (0, 0), sx_image
            )
            jineng_temp = Image.new('RGBA', (kuandu_lie, 38))
            jineng_temp.paste(jineng_img, (0, 0), jineng_bar_mask)
            jineng_draw = ImageDraw.Draw(jineng_temp)
            jineng_draw.text(
                (int((kuandu_lie + 20)/2), 19),
                f'{jineng}',
                (255, 255, 255),
                rc_font_28,
                'mm',
            )
            img.paste(
                jineng_temp, ((kuandu_lie + 7) * jn_x + 82, jn_y * 45 + start_height + 90), jineng_temp
            )
        djjn_height = djjn_height + 160 + (jn_y * 45)
    start_height = start_height + djjn_height
    jn_y = 0
    if len(skill_blood_list) > 0:
        img.paste(skill_title, (77, start_height), skill_title)
        img_draw.text(
            (274, start_height + 37),
            '血脉技能',
            info_text_color,
            rc_font_40,
            'mm',
        )
        for shul, jineng in enumerate(skill_blood_list):
            jn_y = math.floor(shul / shul_lie)
            jn_x = shul - (shul_lie * jn_y)
            jineng_img = Image.new(
                'RGBA', (kuandu_lie, 38), SHUX_LIST_DRAW[skill_list[jineng][0]]
            )
            sx_image = Image.open(ROCOM_SKILL_PATH / f'{jineng}.png').convert('RGBA').resize((38, 38))
            jineng_img.paste(
                sx_image, (0, 0), sx_image
            )
            jineng_temp = Image.new('RGBA', (kuandu_lie, 38))
            jineng_temp.paste(jineng_img, (0, 0), jineng_bar_mask)
            jineng_draw = ImageDraw.Draw(jineng_temp)
            jineng_draw.text(
                (int((kuandu_lie + 20)/2), 19),
                f'{jineng}',
                (255, 255, 255),
                rc_font_28,
                'mm',
            )
            img.paste(
                jineng_temp, ((kuandu_lie + 7) * jn_x + 82, jn_y * 45 + start_height + 90), jineng_temp
            )
        jn_y = jn_y + 1
    start_height = jn_y * 45 + start_height
    yc_y = 0
    if len(skill_stone_list) > 0:
        start_height = start_height + 110
        img.paste(skill_title, (77, start_height), skill_title)
        img_draw.text(
            (274, start_height + 37),
            '技能石技能',
            info_text_color,
            rc_font_40,
            'mm',
        )
        for shul, jineng in enumerate(skill_stone_list):
            yc_y = math.floor(shul / shul_lie)
            jn_x = shul - (shul_lie * yc_y)
            jineng_img = Image.new(
                'RGBA', (kuandu_lie, 38), SHUX_LIST_DRAW[skill_list[jineng][0]]
            )
            sx_image = Image.open(ROCOM_SKILL_PATH / f'{jineng}.png').convert('RGBA').resize((38, 38))
            jineng_img.paste(
                sx_image, (0, 0), sx_image
            )
            jineng_temp = Image.new('RGBA', (kuandu_lie, 38))
            jineng_temp.paste(jineng_img, (0, 0), jineng_bar_mask)
            jineng_draw = ImageDraw.Draw(jineng_temp)
            jineng_draw.text(
                (int((kuandu_lie + 20)/2), 19),
                f'{jineng}',
                (255, 255, 255),
                rc_font_28,
                'mm',
            )
            img.paste(
                jineng_temp, ((kuandu_lie + 7) * jn_x + 82, yc_y * 45 + start_height + 90), jineng_temp
            )
        yc_y = yc_y + 1
    img_draw.text(
        (450, bg_height + 108),
        'Created by GsCore & RocomUID & jiluoQAQ',
        (140, 140, 140),
        rc_font_15,
        'mm',
    )
    bg_img.paste(img, (40, 40), img)
    res = await convert_img(bg_img)
    return res