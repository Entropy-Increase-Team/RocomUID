import copy
import re
import os
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from PIL import Image, ImageDraw
from gsuid_core.utils.image.convert import convert_img
from ..utils.resource.RESOURCE_PATH import ROCOM_ICON_PATH
from ..utils.map.rocom_map import rocom_name_list, rocom_group_list, rocom_list, rocom_skill_list, characteristic_list, skill_list, rocom_egg_build, rocom_evolution_list
from .draw_info_image import draw_rocom_info
from gsuid_core.segment import MessageSegment, _image_to_local_url
from ..utils.convert import get_rocom_name, rocom_egg_conf

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
        return await bot.send('请输入需要查询精灵蛋的尺寸与重量')
    length = args[0]
    if not await is_numeric(length):
        return await bot.send('请输入正确的尺寸信息')
    weight = args[1]
    if not await is_numeric(weight):
        return await bot.send('请输入正确的重量信息')
    egg_list = copy.deepcopy(rocom_egg_build)
    find_list = []
    for item in rocom_egg_conf:
        if item.get('precious_egg_type', 0) > 0:
            continue
        find_flag = 0
        if item['height_low'] <= float(length) * 100 and float(length) * 100 <= item['height_high']:
            find_flag = find_flag + 1
        if item['weight_low'] <= float(weight) * 1000 and float(weight) * 1000 <= item['weight_high']:
            find_flag = find_flag + 1
        if find_flag == 2 and item["name"] not in find_list:
            find_list.append(item["name"])
    if len(find_list) == 0:
        mes = "暂时没有找到该精灵蛋的匹配信息"
    else:
        mes = f"【查找条件】 尺寸：{length}m 重量：{weight}kg\n该精灵蛋有可能出生的精灵为\n"
        shuling = 1
        for rocomname in find_list:
            icon_src = ROCOM_ICON_PATH / f'{rocomname}.png'
            if not os.path.exists(icon_src):
                continue
            rocom_img = Image.open(icon_src).convert('RGBA').resize((500, 500))
            im = Image.new("RGB", (500, 500), (255, 255, 255))
            dtbox = (0, 0)
            im.paste(rocom_img, dtbox, mask=rocom_img)
            im = await convert_img(im)
            url = await _image_to_local_url(im)
            img_url = url[0].data.replace("link://", "")
            mes += f"\n![图片 #36px #36px]({img_url})"
            mes += f" [{rocomname}](mqqapi://aio/inlinecmd?command=rc图鉴{rocomname}&reply=false&enter=true)"
        mes += "\n范围还在更新中，结果仅供参考"
    mes += "\n[再次查询](mqqapi://aio/inlinecmd?command=rc精灵蛋&reply=false)"
    await bot.send(MessageSegment.markdown(mes))

@sv_rc_rocom_info.on_command('配种')
async def get_rocom_egg_info(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 2:
        return await bot.send('请输入需要查询配种信息的父母精灵名称[父母精灵请输入最终进化型进行查询]')
    rocom_name1 = await get_rocom_name(args[0])
    if rocom_name1 == '':
        return await bot.send('精灵名不存在，请输入正确的精灵名称')
    rocom_name2 = await get_rocom_name(args[1])
    if rocom_name2 == '':
        return await bot.send('精灵名不存在，请输入正确的精灵名称')
        
    group1 = rocom_group_list[rocom_name1]
    group2 = rocom_group_list[rocom_name2]
    
    if group1[0] == '无' or group2[0] == '无':
        return await bot.send(f'{rocom_name1}与{rocom_name2}无法进行配种哦')
    
    peizhong_flag = 0
    for item in group1:
        if item in group2:
            peizhong_flag = 1
    
    if peizhong_flag == 0:
        await bot.send(f'{rocom_name1}与{rocom_name2}无法进行配种哦')
    else:
        await bot.send(f'{rocom_name1}与{rocom_name2}可以进行配种哦~')
        
@sv_rc_rocom_info.on_command('技能信息')
async def get_rocom_skill_info(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        return await bot.send('请输入需要查询的技能名称')
    skill_name = args[0]
    if skill_name not in skill_list.keys():
        return await bot.send('技能名不存在，请输入正确的技能名称')
    
    skill_info = skill_list[skill_name]
    weili = '--' if skill_info[2] == '0' else skill_info[2]
    mes = f"技能名称：{skill_name}\n技能属性：{skill_info[0]}\n技能消耗：{skill_info[1]}cost\n技能威力：{weili}\n技能介绍：{skill_info[3]}"
    await bot.send(mes)
    
@sv_rc_rocom_info.on_command('图鉴')
async def get_rocom_info_img(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        return await bot.send('请输入需要查询的精灵名称')
    rocom_name = await get_rocom_name(args[0])
    if rocom_name not in rocom_list.keys():
        return await bot.send('精灵名称不存在，请输入正确的精灵名称')
    
    im = await draw_rocom_info(rocom_name)
    url = await _image_to_local_url(im)
    img_url = url[0].data.replace("link://", "")
    size = url[1].data
    mes = f"![图片 #{size[0]}px #{size[1]}px]({img_url})"
    if len(rocom_evolution_list[rocom_name][0]) > 1:
        mes += f"\n查询图鉴："
        for name in rocom_evolution_list[rocom_name][0]:
            if name != rocom_name:
                mes += f"[{name}](mqqapi://aio/inlinecmd?command=rc图鉴{name}&reply=false&enter=true) "
    if len(rocom_group_list[rocom_name]) > 0:
        mes += f"\n查询蛋组："
        for groupname in rocom_group_list[rocom_name]:
            mes += f"[{groupname}](mqqapi://aio/inlinecmd?command=rc查找精灵蛋组,{groupname}&reply=false&enter=true) "
    await bot.send(MessageSegment.markdown(mes))
    
@sv_rc_rocom_info.on_command('查找精灵')
async def find_rocom_list_info(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        return await bot.send('请输入 查找精灵+查找条件[名字/属性/蛋组/特性/技能/种族(生命、物攻、魔攻、物防、魔防、速度[小于/大于])] 不同的筛选条件用空格分开，类型与内容用逗号分开。\n举例：查找精灵 特性,最好的伙伴 技能,折射,光球 魔攻,大于,60')
    find_tj_list = ['名字','特性','技能','生命','物攻','物防','魔攻','魔防','速度','属性','蛋组']
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
        if iteminfo[0] == '蛋组':
            for rocom_name in rocom_find_list:
                if str(iteminfo[1]) not in str(rocom_group_list[rocom_name]):
                    find_cocom_list.remove(rocom_name)
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
                mes += f"[{rocomname}](mqqapi://aio/inlinecmd?command=rc图鉴{rocomname}&reply=false&enter=true)"
                if shuling == 4:
                    shuling = 1
                    mes += '\n'
                else:
                    shuling = shuling + 1
                    if rocomname != find_cocom_list[len(find_cocom_list) - 1]:
                        mes += '、'
    else:
        mes = '没有查找到符合您输入条件的精灵'
    await bot.send(MessageSegment.markdown(mes))