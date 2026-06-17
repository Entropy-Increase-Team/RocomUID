import re
import json
import time
import os
import asyncio
from pathlib import Path
from async_timeout import timeout
import pytz
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from datetime import datetime, timedelta
from ..utils.rocom_api import wegame_api,text_api
from gsuid_core.logger import logger
from ..utils.database.model import RocomUser
from gsuid_core.subscribe import gs_subscribe
from gsuid_core.aps import scheduler
from ..utils.error_reply import prefix as P
from ..utils.to_data import api_to_dict_pet_info, convert_pet_info_map
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from ..rocom_config.rocom_config import RC_CONFIG
from .draw_info_image import draw_pet_list,draw_pet_info

sv_pet_info = SV('rc精灵查询', priority=5)

async def get_my_pet_info_data(uid, refresh: bool = False):
    #优先获取本地缓存数据
    if not refresh:
        home_info_path = PLAYER_PATH / uid / 'pet_info.json'
        if os.path.exists(home_info_path):
            with Path.open(home_info_path, encoding='utf-8') as f:
                pet_data = json.load(f)
                return convert_pet_info_map(pet_data["pets_list"])
    pet_data = await api_to_dict_pet_info(uid, PLAYER_PATH)
    return pet_data

@sv_pet_info.on_command(('刷新精灵','强制刷新','刷新面板'))
async def get_my_pet_info_refresh(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
        if not uid:
            return await bot.send("你还没有绑定RC_UID哦!")
    else:
        uid = args[0]
    if uid and not uid.isdigit():
        return await bot.send("请输入正确的UID格式!")
    await bot.send(f"正在刷新[UID]{uid}的精灵信息，请稍后")
    pet_data = await get_my_pet_info_data(uid, refresh=True)
    if isinstance(pet_data, str):
        return await bot.send(pet_data)
    im = await draw_pet_list(uid, pet_data)
    await bot.send(im)

async def get_my_pet_list(uid, pet_find_id, pet_find_name):
    #查找本地缓存，是否有唯一指定精灵
    home_info_path = PLAYER_PATH / uid / 'pet_info.json'
    pet_list = {}
    if os.path.exists(home_info_path):
        with Path.open(home_info_path, encoding='utf-8') as f:
            pet_data = json.load(f)
            pet_list = convert_pet_info_map(pet_data["pets_list"])
    
    pet_id_list = {}
    if len(pet_list.keys()) > 0:
        #优先搜索精灵gid
        for gid in pet_list:
            if pet_find_id != 0 and pet_find_id == gid:
                #查找到唯一gid直接返回数据
                return {gid:pet_list[gid]}
            #查找同名精灵保存对应的gid以供用户选择
            if pet_find_name != '' and pet_list[gid].name == pet_find_name:
                pet_id_list[gid] = pet_list[gid]
        
    #本地缓存未找到，获取服务器数据并刷新
    if len(pet_id_list.keys()) == 0:
        pet_list = await get_my_pet_info_data(uid, refresh=True)
        if isinstance(pet_list, str):
            return await bot.send(pet_list)
    
    for gid in pet_list:
        if pet_find_id != 0 and pet_find_id == gid:
            #查找到唯一gid直接返回数据
            return {gid:pet_list[gid]}
        #查找同名精灵保存对应的gid以供用户选择
        if pet_find_name != '' and pet_list[gid].name == pet_find_name:
            pet_id_list[gid] = pet_list[gid]
    
    return pet_id_list
    
    
@sv_pet_info.on_command(('查询','查看','面板'))
async def get_my_pet_info(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 2:
        uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
        if not uid:
            return await bot.send("你还没有绑定RC_UID哦!")
    else:
        uid = args[1]
    if uid and not uid.isdigit():
        return await bot.send("请输入正确的UID格式!")
    pet_find_id = 0
    pet_find_name = args[0]
    #判断是否包含数字[精灵id]并提取
    if any(char.isdigit() for char in pet_find_name):
        pet_find_id = ''.join(re.findall(r'\d', pet_find_name))
        pet_find_name = re.sub(r'\d+', '', pet_find_name)
    
    find_pet_list = await get_my_pet_list(uid, pet_find_id, pet_find_name)
    if isinstance(find_pet_list, str):
        return await bot.send(find_pet_list)
    
    #没有获取到精灵数据
    if len(find_pet_list.keys()) == 0:
        return await bot.send(f"您的家园/缓存中没有保存{pet_find_name}{pet_find_id if pet_find_id != 0 else ''}的精灵数据\n请把需要查询的精灵放置家园宠物小窝中。等待5-10分钟后再次查询")
    
    #获取到多条数据，让用户选择需要查询的指定数据
    if len(find_pet_list.keys()) > 1:
        shul = 1
        xiabiao_list = []
        xuanze_list = list(find_pet_list.keys())
        mes = ''
        for gid in find_pet_list:
            mes += f"\n{shul}·{find_pet_list[gid].name}({gid}) Lv.{find_pet_list[gid].level}"
            xiabiao_list.append(str(shul))
            shul = shul + 1
        
        runmynum = 0
        pet_type_use = 0
        try:
            async with timeout(60):
                while pet_type_use == 0:
                    if runmynum == 0:
                        mesg = f"检测到您需要查到的精灵有多种选择\n请在60秒内选择您需要查询的指定精灵{mes}"
                        await bot.send(mesg)
                    myresp = await bot.receive_mutiply_resp()
                    if myresp is not None:
                        mys = myresp.text.strip()
                        user_id_my = myresp.user_id
                        if str(user_id_my) == str(ev.user_id):
                            if mys in xuanze_list or mys in xiabiao_list:
                                if mys in xuanze_list:
                                    pet_xuanze = mys
                                    pet_type_use = 1
                                else:
                                    mys_XB = int(mys)
                                    pet_xuanze = xuanze_list[mys_XB - 1]
                                    pet_type_use = 1
        except asyncio.TimeoutError:
            pet_xuanze = xuanze_list[0]
            pet_type_use = 1
        
        pet_gid = pet_xuanze
        pet_data = find_pet_list[pet_gid]
    
    #只有一条数据
    if len(find_pet_list.keys()) == 1:
        pet_gid = list(find_pet_list.keys())[0]
        pet_data = find_pet_list[pet_gid]
    im = await draw_pet_info(uid, pet_data)
    await bot.send(im)
