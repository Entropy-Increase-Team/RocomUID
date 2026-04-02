import copy
import re
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from ..utils.map.rocom_map import rocom_name_list, rocom_group_list, rocom_list, rocom_skill_list, characteristic_list, skill_list
from .draw_info_image import draw_rocom_info
from ..utils.convert import get_rocom_name

sv_rc_rocom_info = SV('rc基础信息查询', priority=5)

@sv_rc_rocom_info.on_command('配种')
async def get_rocom_egg_info(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 2:
        return await bot.send('请输入需要查询配种信息的父母精灵名称[父母精灵请输入最终进化型进行查询]', at_sender=True)
    rocom_name1 = await get_rocom_name(args[0])
    if rocom_name1 == '':
        return await bot.send('精灵名不存在，请输入正确的精灵名称', at_sender=True)
    rocom_name2 = await get_rocom_name(args[1])
    if rocom_name2 == '':
        return await bot.send('精灵名不存在，请输入正确的精灵名称', at_sender=True)
        
    group1 = rocom_group_list[rocom_name1]
    group2 = rocom_group_list[rocom_name2]
    
    if group1[0] == '无' or group2[0] == '无':
        return await bot.send(f'{rocom_name1}与{rocom_name2}无法进行配种哦', at_sender=True)
    
    peizhong_flag = 0
    for item in group1:
        if item in group2:
            peizhong_flag = 1
    
    if peizhong_flag == 0:
        await bot.send(f'{rocom_name1}与{rocom_name2}无法进行配种哦', at_sender=True)
    else:
        await bot.send(f'{rocom_name1}与{rocom_name2}可以进行配种哦~', at_sender=True)
        
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
    rocom_name = await get_rocom_name(args[0])
    if rocom_name not in rocom_list.keys():
        return await bot.send('精灵名称不存在，请输入正确的精灵名称', at_sender=True)
    
    im = await draw_rocom_info(rocom_name)
    await bot.send(im, at_sender=True)
    
@sv_rc_rocom_info.on_command('查找精灵')
async def find_rocom_list_info(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        return await bot.send('请输入 查找精灵+查找条件[名字/属性/特性/技能/种族(生命、物攻、魔攻、物防、魔防、速度[小于/大于])] 不同的筛选条件用空格分开，类型与内容用逗号分开。\n举例：查找精灵 特性,最好的伙伴 技能,折射,光球 魔攻,大于,60', at_sender=True)
    find_tj_list = ['名字','特性','技能','生命','物攻','物防','魔攻','魔防','速度','属性']
    zhongzu_index_list = {
        '生命':0,
        '物攻':1,
        '魔攻':2,
        '物防':3,
        '魔防':4,
        '速度':5
    }
    rocom_find_list = list(rocom_name_list.keys())
    find_cocom_list = copy.deepcopy(rocom_find_list)
    for item in args:
        item = item.replace('，',',')
        iteminfo = re.split(',', item)
        #print(iteminfo)
        if iteminfo[0] not in find_tj_list:
            continue
        if len(rocom_find_list) <= 0:
            break
        if iteminfo[0] == '名字':
            for rocom_name in rocom_find_list:
                find_name_flag = 0
                for name_item in rocom_name_list[rocom_name]:
                    if str(iteminfo[1]) in str(name_item):
                        find_name_flag = 1
                if find_name_flag == 0:
                    find_cocom_list.remove(rocom_name) 
        if iteminfo[0] == '特性':
            for rocom_name in rocom_find_list:
                if str(iteminfo[1]) not in str(rocom_list[rocom_name][7]):
                    find_cocom_list.remove(rocom_name)
            #print(find_cocom_list)
        if iteminfo[0] == '属性':
            find_shux_list = []
            for shux_item in iteminfo:
                if shux_item != '属性':
                    find_shux_list.append(shux_item)
            for rocom_name in rocom_find_list:
                find_list_info = []
                for shuxing_name in find_shux_list:
                    if shuxing_name in rocom_list[rocom_name][6]:
                        find_list_info.append(shuxing_name)
                if find_shux_list != find_list_info:
                    find_cocom_list.remove(rocom_name)
        if iteminfo[0] in ['生命','物攻','魔攻','物防','魔防','速度']:
            for rocom_name in rocom_find_list:
                if iteminfo[1] == '大于':
                    if int(rocom_list[rocom_name][zhongzu_index_list[iteminfo[0]]]) < int(iteminfo[2]):
                        find_cocom_list.remove(rocom_name)
                else:
                    if int(rocom_list[rocom_name][zhongzu_index_list[iteminfo[0]]]) > int(iteminfo[2]):
                        find_cocom_list.remove(rocom_name)
            #print(find_cocom_list)
        if iteminfo[0] == '技能':
            jineng_find_flag = 0
            find_jineng_list = []
            for jineng_item in iteminfo:
                if jineng_item != '技能':
                    find_jineng_list.append(jineng_item)
            #print(find_jineng_list)
            for rocom_name in rocom_find_list:
                find_list_info = []
                for jineng_name in find_jineng_list:
                    if jineng_name in rocom_skill_list[rocom_name][0] and jineng_name not in find_list_info:
                        find_list_info.append(jineng_name)
                    if jineng_name in rocom_skill_list[rocom_name][1] and jineng_name not in find_list_info:
                        find_list_info.append(jineng_name)
                    if jineng_name in rocom_skill_list[rocom_name][2] and jineng_name not in find_list_info:
                        find_list_info.append(jineng_name)
                if find_jineng_list != find_list_info:
                    find_cocom_list.remove(rocom_name)
            #print(find_cocom_list)
        rocom_find_list = copy.deepcopy(find_cocom_list)
    if len(find_cocom_list) > 0:
        mes = f"一共查找到{len(find_cocom_list)}只符合条件的精灵\n具体信息请输入rc图鉴【精灵名】查询\n"
        if len(find_cocom_list) > 750:
            mes += f"超过700只了，这不是到处都是吗"
        else:
            shuling = 1
            for rocomname in find_cocom_list:
                mes += f"{rocomname}"
                if shuling == 4:
                    shuling = 1
                    mes += '\n'
                else:
                    shuling = shuling + 1
                    if rocomname != find_cocom_list[len(find_cocom_list) - 1]:
                        mes += '、'
    else:
        mes = '没有查找到符合您输入条件的精灵'
    await bot.send(mes)