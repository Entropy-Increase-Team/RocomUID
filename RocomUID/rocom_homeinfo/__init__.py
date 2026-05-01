import re
import json
import time
import os
import asyncio
from pathlib import Path
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
from ..utils.to_data import api_to_dict_home_info
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from ..rocom_config.rocom_config import RC_CONFIG

sv_home_info = SV('rc家园事件', priority=5)

async def get_my_home_info(uid):
    #优先获取本地缓存数据
    home_info_path = PLAYER_PATH / uid / 'home_info.json'
    if os.path.exists(home_info_path):
        now_time = time.time()
        with Path.open(home_info_path, encoding='utf-8') as f:
            home_data = json.load(f)
            return_local_flag = 0
            min_pet_rip_time = now_time + 604800
            if len(home_data["home_info"]["home_pets"]) > 0:
                for petinfo in home_data["home_info"]["home_pets"]:
                    pet_rip_time = petinfo["pet_rip_time"]
                    if pet_rip_time > 0 and pet_rip_time < min_pet_rip_time:
                        min_pet_rip_time = pet_rip_time
            min_plant_rip_time = now_time + 604800
            if len(home_data["home_info"]["home_plants"]) > 0:
                for plantinfo in home_data["home_info"]["home_plants"]:
                    plant_rip_time = plantinfo["plant_rip_time"]
                    if plant_rip_time > 0 and plant_rip_time < min_plant_rip_time:
                        min_plant_rip_time = plant_rip_time
            if (int(min_pet_rip_time) - int(now_time)) >= 7200 and  (int(min_plant_rip_time) - int(now_time)) >= 7200:
                return_local_flag = 1
            if (int(now_time) - int(home_data['meta']['created_at'])) <= 1800:
                return_local_flag = 1
            if return_local_flag == 1:
                return home_data["home_info"]
    print("正在获取服务器数据")
    home_data = await api_to_dict_home_info(uid, PLAYER_PATH)
    return home_data

@sv_home_info.on_command(('刷新家园','rehome'))
async def get_my_home_info_refresh(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
        if not uid:
            return await bot.send("你还没有绑定RC_UID哦!")
    else:
        uid = args[0]
    await bot.send(f"正在刷新[UID]{uid}的家园信息，请稍后")
    home_data = await text_api.get_home_info(uid)
    await bot.send(f"[UID]{uid}的家园信息已刷新，请输入{P}家园{uid}进行查询")

@sv_home_info.on_command(('家园','home'))
async def get_my_home_info_wegame(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
        if not uid:
            return await bot.send("你还没有绑定RC_UID哦!")
    else:
        uid = args[0]
    await bot.send(f"正在获取[UID]{uid}的家园信息，请稍后")
    
    home_info = await get_my_home_info(uid)
    
    #保存家园信息
    mes = f"{home_info['home_name']}的小屋信息"
    mes += f"\n小屋等级{home_info['room_level']}"
    mes += f"\n家园等级{home_info['home_level']}"
    mes += f"\n家园经验{home_info['home_experience']}"
    mes += f"\n舒适度{home_info['home_comfort_level']}"
    #保存宠物信息
    mes += f"\n\n家园精灵信息"
    now_time = int(time.time())
    for index, petinfo in enumerate(home_info['home_pets']):
        mes += f"\n{petinfo['name']} "
        if petinfo['gender'] == 2:
            mes += "已生蛋" if petinfo['have_egg'] else "未生蛋"
        if petinfo['pet_rip_time'] != 0:
            pet_rip_time = petinfo['pet_rip_time']
            if now_time >= pet_rip_time:
                mes += '\n灵感已收集完成'
            else:
                dt1 = datetime.utcfromtimestamp(now_time)
                dt2 = datetime.utcfromtimestamp(pet_rip_time)
                # 计算两个时间点之间的差异
                delta = dt2 - dt1
                # 提取小时和分钟
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                mes += f'\n灵感剩余{hours}时{minutes}分'
        else:
            mes += '\n未喂食'
    #保存种植信息
    mes += f"\n\n家园种植信息"
    for index, plantinfo in enumerate(home_info['home_plants']):
        mes += f"\n{plantinfo['plant_info']['name']} "
        plant_rip_time = plantinfo['plant_rip_time']
        if now_time >= plant_rip_time:
            mes += '已成熟'
        else:
            dt1 = datetime.utcfromtimestamp(now_time)
            dt2 = datetime.utcfromtimestamp(plant_rip_time)
            # 计算两个时间点之间的差异
            delta = dt2 - dt1
            # 提取小时和分钟
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            mes += f'剩余{hours}时{minutes}分成熟'
    await bot.send(mes)
