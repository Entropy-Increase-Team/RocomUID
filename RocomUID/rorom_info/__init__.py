from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from ..utils.map.rocom_map import rocom_group_list, rocom_list, rocom_skill_list, characteristic_list, skill_list
from .draw_info_image import draw_rocom_info

sv_rc_rocom_info = SV('rc基础信息查询', priority=5)

@sv_rc_rocom_info.on_command('配种')
async def get_rocom_egg_info(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 2:
        return await bot.send('请输入需要查询配种信息的父母精灵名称[父母精灵请输入最终进化型进行查询]', at_sender=True)
    name1 = args[0]
    if name1 not in rocom_group_list.keys():
        return await bot.send('精灵名不存在，请输入正确的精灵名称', at_sender=True)
    name2 = args[1]
    if name2 not in rocom_group_list.keys():
        return await bot.send('精灵名不存在，请输入正确的精灵名称', at_sender=True)
        
    group1 = rocom_group_list[name1]
    group2 = rocom_group_list[name2]
    
    if group1[0] == '无' or group2[0] == '无':
        return await bot.send(f'{name1}与{name2}无法进行配种哦[父母精灵请输入最终进化型进行查询]', at_sender=True)
    
    peizhong_flag = 0
    for item in group1:
        if item in group2:
            peizhong_flag = 1
    
    if peizhong_flag == 0:
        await bot.send(f'{name1}与{name2}无法进行配种哦[父母精灵请输入最终进化型进行查询]', at_sender=True)
    else:
        await bot.send(f'{name1}与{name2}可以进行配种哦~', at_sender=True)
        
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
    rocom_name = args[0]
    if rocom_name not in rocom_list.keys():
        return await bot.send('精灵名称不存在，请输入正确的精灵名称', at_sender=True)
    
    im = await draw_rocom_info(rocom_name)
    await bot.send(im, at_sender=True)