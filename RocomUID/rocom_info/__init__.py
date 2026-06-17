import copy
import re
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from ..utils.map.rocom_map import rocom_name_list, rocom_group_list, rocom_list, rocom_skill_list, characteristic_list, skill_list, rocom_egg_build
from .draw_info_image import draw_rocom_info
from ..utils.error_reply import prefix as P
from ..utils.convert import get_rocom_name, rocom_egg_conf,get_pet_info,pet_list

async def is_numeric(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

sv_rc_rocom_info = SV('rc基础信息查询', priority=5)

@sv_rc_rocom_info.on_command(('精灵蛋', '查蛋'))
async def get_rocom_egg_name(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 2:
        return await bot.send('请输入需要查询精灵蛋的尺寸与重量', at_sender=True)
    length = args[0]
    if not await is_numeric(length):
        return await bot.send('请输入正确的尺寸信息', at_sender=True)
    weight = args[1]
    if not await is_numeric(weight):
        return await bot.send('请输入正确的重量信息', at_sender=True)
    egg_type = '随机'
    if len(args) == 3:
        egg_type = args[2]
    is_glass_flag = False
    if '炫彩' in egg_type:
        is_glass_flag = True
    is_tongcheng_flag = False
    if '同乘' in egg_type:
        is_tongcheng_flag = True
    find_list = []
    for pet_id, item in pet_list.items():
        if item.get('breeding',None) is None:
            continue
        if item['breeding'].get('random_eggs_group', '') == '':
            continue
        if is_tongcheng_flag and '同乘' not in item.get('talent_random_list',[]):
            continue
        find_flag = 0
        if item['breeding']['height_low'] <= float(length) * 100 and float(length) * 100 <= item['breeding']['height_high']:
            find_flag = find_flag + 1
        if item['breeding']['weight_low'] <= float(weight) * 1000 and float(weight) * 1000 <= item['breeding']['weight_high']:
            find_flag = find_flag + 1
        if find_flag == 2 and item["name"] not in find_list:
            find_list.append(item["name"])
    if len(find_list) == 0:
        mes = "暂时没有找到该精灵蛋的匹配信息"
    else:
        mes = f"【查找条件】 \n尺寸：{length}m 重量：{weight}kg\n类型【{egg_type}精灵蛋】\n该精灵蛋有可能出生的精灵为\n"
        shuling = 1
        for rocomname in find_list:
            mes += f"{rocomname}"
            if shuling == 4:
                shuling = 1
                mes += '\n'
            else:
                shuling = shuling + 1
                if rocomname != find_list[len(find_list) - 1]:
                    mes += '、'
        mes += f"\n范围还在更新中，结果仅供参考\n可输入{P}查蛋 [尺寸] [重量] [炫彩/同乘(可选)]查询精灵蛋信息"
    return await bot.send(mes, at_sender=True)

@sv_rc_rocom_info.on_command('配种')
async def get_rocom_egg_info(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 2:
        return await bot.send('请输入需要查询配种信息的父母精灵名称', at_sender=True)
    rocom_id1 = await get_rocom_name(args[0])
    if rocom_id1 == 0:
        return await bot.send('精灵名不存在，请输入正确的精灵名称', at_sender=True)
    rocom_id2 = await get_rocom_name(args[1])
    if rocom_id2 == 0:
        return await bot.send('精灵名不存在，请输入正确的精灵名称', at_sender=True)
        
    group1 = pet_list[str(rocom_id1)]["egg_group"]
    group2 = pet_list[str(rocom_id2)]["egg_group"]
    danzu_str1 = ' '.join(group1)
    danzu_str2 = ' '.join(group2)
    peizhong_flag = 0
    for item in group1:
        if item in group2:
            peizhong_flag = 1
    mes = f"{pet_list[str(rocom_id1)]['name']}的蛋组为\n{danzu_str1}\n{pet_list[str(rocom_id2)]['name']}的蛋组为\n{danzu_str2}"
    if peizhong_flag == 0:
        await bot.send(f'{mes}\n双方没有相同的蛋组，无法进行配种哦', at_sender=True)
    else:
        await bot.send(f'{mes}\n双方拥有相同的蛋组，可以进行配种哦~', at_sender=True)
        
@sv_rc_rocom_info.on_command('技能信息')
async def get_rocom_skill_info(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        return await bot.send('请输入需要查询的技能名称', at_sender=True)
    skill_name = args[0]
    if skill_name not in skill_list.keys():
        return await bot.send('技能名不存在，请输入正确的技能名称', at_sender=True)
    
    skill_info = skill_list[skill_name]
    weili = '--' if skill_info[2] == '0' else skill_info[2]
    mes = f"技能名称：{skill_name}\n技能属性：{skill_info[0]}\n技能消耗：{skill_info[1]}cost\n技能威力：{weili}\n技能介绍：{skill_info[3]}"
    await bot.send(mes, at_sender=True)
    
@sv_rc_rocom_info.on_command('图鉴')
async def get_rocom_info_img(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        return await bot.send('请输入需要查询的精灵名称', at_sender=True)
    pet_id = await get_rocom_name(args[0])
    if pet_id == 0:
        return await bot.send('精灵名称不存在，请输入正确的精灵名称', at_sender=True)
    pet_info = await get_pet_info(pet_id)
    im = await draw_rocom_info(pet_info)
    await bot.send(im, at_sender=True)
    
@sv_rc_rocom_info.on_command('查找精灵')
async def find_rocom_list_info(bot: Bot, ev: Event):
    args = ev.text.split()
    help_msg = '请输入 查找精灵+查找条件[名字/属性/蛋组/特性/技能/种族(生命、物攻、魔攻、物防、魔防、速度[小于/大于])] 不同的筛选条件用空格分开，类型与内容用逗号分开。\n举例：查找精灵 犬\n举例：查找精灵 特性,最好的伙伴 技能,折射,光球 魔攻,大于,60'
    if len(args) < 1:
        return await bot.send(help_msg, at_sender=True)
    find_tj_list = ['名字', '特性', '技能', '生命', '物攻', '物防', '魔攻', '魔防', '速度', '属性', '蛋组']
    zhongzu_index_list = {
        '生命': 'attr_hp',
        '物攻': 'attr_atk',
        '魔攻': 'attr_spatk',
        '物防': 'attr_def',
        '魔防': 'attr_spdef',
        '速度': 'attr_spd'
    }

    find_args = []
    for item in args:
        item = item.replace('，', ',').strip()
        iteminfo = [info.strip() for info in re.split(',', item)]
        if iteminfo[0] == '':
            return await bot.send('查找条件不能为空', at_sender=True)

        if iteminfo[0] not in find_tj_list:
            find_args.append(['名字', item])
            continue

        if iteminfo[0] in ['名字', '特性', '蛋组']:
            if len(iteminfo) < 2 or iteminfo[1] == '':
                return await bot.send(f'请输入{iteminfo[0]}的查询内容', at_sender=True)
        elif iteminfo[0] in ['属性', '技能']:
            if len(iteminfo) < 2 or any(info == '' for info in iteminfo[1:]):
                return await bot.send(f'请输入{iteminfo[0]}的查询内容', at_sender=True)
        elif iteminfo[0] in ['生命', '物攻', '魔攻', '物防', '魔防', '速度']:
            if len(iteminfo) < 3 or iteminfo[1] == '' or iteminfo[2] == '':
                return await bot.send(f'请输入{iteminfo[0]}的比较方式和数值，例如：{iteminfo[0]},大于,60', at_sender=True)
            if iteminfo[1] not in ['大于', '小于']:
                return await bot.send(f'{iteminfo[0]}的比较方式只能为“大于”或“小于”', at_sender=True)
            if not await is_numeric(iteminfo[2]):
                return await bot.send(f'{iteminfo[0]}的比较数值请输入数字', at_sender=True)

        find_args.append(iteminfo)

    rocom_find_list = list(pet_list.keys())
    find_cocom_list = copy.deepcopy(rocom_find_list)
    for rocom_id in rocom_find_list:
        if pet_list[rocom_id]["feature"].get("name", '') == '' and rocom_id in find_cocom_list:
            find_cocom_list.remove(rocom_id)
        if len(pet_list[rocom_id]["level_skill_list"]) == 0 and rocom_id in find_cocom_list:
            find_cocom_list.remove(rocom_id)
        if len(pet_list[rocom_id]["machine_skill_list"]) == 0 and rocom_id in find_cocom_list:
            find_cocom_list.remove(rocom_id)
        if len(pet_list[rocom_id]["blood_skill_list"]) == 0 and rocom_id in find_cocom_list:
            find_cocom_list.remove(rocom_id)
    rocom_find_list = copy.deepcopy(find_cocom_list)

    for iteminfo in find_args:
        if len(rocom_find_list) <= 0:
            break
        if iteminfo[0] == '名字':
            for rocom_id in rocom_find_list:
                if str(iteminfo[1]) not in str(pet_list[rocom_id].get('name', '')):
                    find_cocom_list.remove(rocom_id)
        if iteminfo[0] == '特性':
            for rocom_id in rocom_find_list:
                if str(iteminfo[1]) not in str(pet_list[rocom_id]["feature"].get("name", '')):
                    find_cocom_list.remove(rocom_id)
            # print(find_cocom_list)
        if iteminfo[0] == '蛋组':
            for rocom_id in rocom_find_list:
                if str(iteminfo[1]) not in str(pet_list[rocom_id]["egg_group"]):
                    find_cocom_list.remove(rocom_id)
        if iteminfo[0] == '属性':
            find_shux_list = []
            for shux_item in iteminfo:
                if shux_item != '属性':
                    find_shux_list.append(shux_item)
            for rocom_id in rocom_find_list:
                find_list_info = []
                for shuxing_name in find_shux_list:
                    if shuxing_name in pet_list[rocom_id]['unit_type']:
                        find_list_info.append(shuxing_name)
                if find_shux_list != find_list_info:
                    find_cocom_list.remove(rocom_id)
        if iteminfo[0] in ['生命', '物攻', '魔攻', '物防', '魔防', '速度']:
            for rocom_id in rocom_find_list:
                if iteminfo[1] == '大于':
                    if int(pet_list[rocom_id]["attribute"][zhongzu_index_list[iteminfo[0]]]) < int(iteminfo[2]):
                        find_cocom_list.remove(rocom_id)
                else:
                    if int(pet_list[rocom_id]["attribute"][zhongzu_index_list[iteminfo[0]]]) > int(iteminfo[2]):
                        find_cocom_list.remove(rocom_id)
            # print(find_cocom_list)
        if iteminfo[0] == '技能':
            find_jineng_list = []
            for jineng_item in iteminfo:
                if jineng_item != '技能':
                    find_jineng_list.append(jineng_item)
            # print(find_jineng_list)
            for rocom_id in rocom_find_list:
                find_list_info = []
                for jineng_name in find_jineng_list:
                    level_skills = []
                    if len(pet_list[rocom_id]["level_skill_list"]) > 0:
                        level_skills = [skill["name"] for skill in pet_list[rocom_id]["level_skill_list"]]
                    if jineng_name in level_skills and jineng_name not in find_list_info:
                        find_list_info.append(jineng_name)
                    machine_skills = []
                    if len(pet_list[rocom_id]["machine_skill_list"]) > 0:
                        machine_skills = [skill["name"] for skill in pet_list[rocom_id]["machine_skill_list"]]
                    if jineng_name in machine_skills and jineng_name not in find_list_info:
                        find_list_info.append(jineng_name)
                    blood_skills = []
                    if len(pet_list[rocom_id]["blood_skill_list"]) > 0:
                        blood_skills = [skill["name"] for skill in pet_list[rocom_id]["blood_skill_list"]]
                    if jineng_name in blood_skills and jineng_name not in find_list_info:
                        find_list_info.append(jineng_name)
                if find_jineng_list != find_list_info:
                    find_cocom_list.remove(rocom_id)
            # print(find_cocom_list)
        rocom_find_list = copy.deepcopy(find_cocom_list)
    if len(find_cocom_list) > 0:
        find_name_list = []
        for rocom_id in find_cocom_list:
            if pet_list[rocom_id]['name'] not in find_name_list:
                find_name_list.append(pet_list[rocom_id]['name'])

        mes = f"一共查找到{len(find_name_list)}只符合条件的精灵\n具体信息请输入rc图鉴【精灵名】查询\n"
        if len(find_name_list) > 100:
            mes += "超过700只了，这不是到处都是吗"
        else:
            shuling = 1
            for index, rocom_name in enumerate(find_name_list):
                mes += f"{rocom_name}"
                if shuling == 4:
                    shuling = 1
                    mes += '\n'
                else:
                    shuling = shuling + 1
                    if index != len(find_name_list) - 1:
                        mes += '、'
    else:
        mes = '没有查找到符合您输入条件的精灵'
    await bot.send(mes)
