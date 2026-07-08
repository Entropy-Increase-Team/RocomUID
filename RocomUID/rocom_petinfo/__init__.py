import json
import os
from pathlib import Path
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from ..utils.database.model import RocomUser
from ..utils.to_data import api_to_dict_pet_info, convert_pet_info_map
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from .draw_info_image import draw_pet_home

sv_pet_info = SV('家园精灵', priority=5)

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

def get_home_name(uid: str) -> str:
    pet_info_path = PLAYER_PATH / uid / 'pet_info.json'
    if os.path.exists(pet_info_path):
        with Path.open(pet_info_path, encoding='utf-8') as f:
            pet_data = json.load(f)
            return pet_data.get('home_name') or '未命名家园'
    return '未命名家园'

async def get_my_pet_info(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
        if not uid:
            return await bot.send("你还没有绑定RC_UID哦!")
    else:
        uid = args[0]
    if uid and not uid.isdigit():
        return await bot.send("请输入正确的UID格式!")
    await bot.send(f'正在获取[UID]{uid}的家园精灵信息，请稍后')
    pet_data = await get_my_pet_info_data(uid, refresh=True)
    if isinstance(pet_data, str):
        return await bot.send(pet_data)
    if len(pet_data.keys()) == 0:
        return await bot.send("您的家园中没有可显示的精灵数据。")
    im = await draw_pet_home(uid, pet_data, get_home_name(uid))
    await bot.send(im)
