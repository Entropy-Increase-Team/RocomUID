import re
import json
import time
import asyncio
from async_timeout import timeout
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from ..utils.rocom_api import rocom_api,wegame_api
from ..utils.error_reply import get_error
from gsuid_core.logger import logger
from ..utils.database.model import RocomUser
from ..utils.message import send_diff_msg
from ..utils.api_client import APIClient
from ..utils.error_reply import prefix as P
from ..utils.convert import get_rocom_name2id
from .draw_info_image import draw_user_info, draw_user_info_wegame

sv_user_info = SV('rc用户信息查询', priority=5)

# @sv_user_info.on_command(('我的信息','uid'))
# async def get_my_user_info(bot: Bot, ev: Event):
    # bind_uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
    # if not bind_uid:
        # return await bot.send("你还没有绑定RC_UID哦!")
    # token, account_type = await RocomUser.get_rocom_token(ev.user_id, ev.bot_self_id)
    # if not token:
        # return await bot.send("用户token不存在，请绑定后再查询!")
    # data_user = await rocom_api.get_user_info(token=token, account_type = account_type)
    # #print(data_user)
    # if isinstance(data_user, int):
        # return await bot.send(get_error(data_user))
    # data_pet = await rocom_api.get_rocom_pet_list_star(token=token, account_type = account_type)
    # #print(data_pet)
    # im = await draw_user_info(ev, bind_uid, data_user, data_pet)
    # await bot.send(im, at_sender=True)

@sv_user_info.on_command(('档案','洛克档案','uid','我的信息'))
async def get_my_user_info_wegame(bot: Bot, ev: Event):
    fw_token = await RocomUser.select_rocom_fw_token(ev.user_id, ev.bot_self_id)
    if not fw_token:
        return await bot.send(f"没有获取到您的登录状态，请输入{P}QQ登录/{P}WX登录，进行绑定后再查询")
    await bot.send("正在获取洛克王国数据...")
    role_task = wegame_api.get_role(fw_token)
    coll_task = wegame_api.get_collection(fw_token)
    battle_overview_task = wegame_api.get_battle_overview(fw_token)
    results = await asyncio.gather(role_task, coll_task, battle_overview_task, return_exceptions=True)
    role_res, coll_res, bo_res = results
    #print(results)
    if isinstance(role_res, Exception) or not role_res or not role_res.get("role"):
        err_msg = str(role_res) if isinstance(role_res, Exception) else (role_res.get("message") if isinstance(role_res, dict) else "未知错误")
        if "401" in err_msg or "403" in err_msg:
            err_hint = "【凭据过期】请尝试重新通过 QQ/微信 登录绑定。"
        else:
            err_hint = f"接口返回错误: {err_msg}"
        return await bot.send(f"获取角色档案失败。\n{err_hint}")
    role = role_res["role"]
    coll_res = coll_res if isinstance(coll_res, dict) else {}
    bo_res = bo_res if isinstance(bo_res, dict) else {}
    # 组装数据
    data = {
        "userName": role.get("name", "洛克"),
        "userLevel": role.get("level", 1),
        "userUid": role.get("id", ""),
        "create_time": time.strftime("%Y-%m-%d", time.localtime(int(role.get("create_time", time.time())))),
        "enrollDays": role.get("enroll_days", 0),
        "starName": role.get("star_name", "魔法学徒"),
        
        "currentCollectionCount": coll_res.get("current_collection_count", 0),
        "totalCollectionCount": f"{coll_res.get('total_collection_count', 0)}",
        "amazingSpriteCount": coll_res.get("amazing_sprite_count", 0),
        "shinySpriteCount": coll_res.get("shiny_sprite_count", 0),
        "colorfulSpriteCount": coll_res.get("colorful_sprite_count", 0),
        "fashionCollectionCount": coll_res.get("fashion_collection_count", 0),
        "itemCount": coll_res.get("item_count", 0),
        
        "hasBattleData": bo_res.get("total_match", 0) > 0,
        "BattleRank": f"{bo_res.get('tier', 0)}",
        "winRate": f"{bo_res.get('win_rate', 0)}%",
        "totalMatch": bo_res.get("total_match", 0),
    }
    pets_list = []
    #获取异色数据
    if coll_res.get("shiny_sprite_count", 0) > 0:
        pet_res = await wegame_api.get_pets(fw_token, pet_subset=2, page_no=1, page_size=coll_res.get("shiny_sprite_count", 0))
        for pet in pet_res.get("pets", []):
            element_list = []
            for t in pet.get("pet_types_info", []):
                if t.get("id"):
                    element_list.append(t.get("id", ""))
            full_name = pet.get("pet_name", "")
            if "&" in full_name:
                name_parts = full_name.split("&", 1)
                p_name = name_parts[0]
            else:
                p_name = full_name
            pets_list.append({
                "PetBaseId": pet.get("pet_base_id", 3011),
                "name": p_name,
                "PetMutation": pet.get("pet_mutation", 0),
                "SpiritLevel": pet.get("pet_level", 1),
                "PetSkillDamType": element_list,
            })
    #获取炫彩数据
    if coll_res.get("colorful_sprite_count", 0) > 0:
        pet_res = await wegame_api.get_pets(fw_token, pet_subset=3, page_no=1, page_size=coll_res.get("colorful_sprite_count", 0))
        for pet in pet_res.get("pets", []):
            if pet.get("pet_mutation", 0) not in [1,9]:
                element_list = []
                for t in pet.get("pet_types_info", []):
                    if t.get("id"):
                        element_list.append(t.get("id", ""))
                full_name = pet.get("pet_name", "")
                if "&" in full_name:
                    name_parts = full_name.split("&", 1)
                    p_name = name_parts[0]
                else:
                    p_name = full_name
                pets_list.append({
                    "PetBaseId": pet.get("pet_base_id", 3011),
                    "name": p_name,
                    "PetMutation": pet.get("pet_mutation", 0),
                    "SpiritLevel": pet.get("pet_level", 1),
                    "PetSkillDamType": element_list,
                })
    data['pets_list'] = pets_list
    #print(data)
    im = await draw_user_info_wegame(ev, data)
    await bot.send(im, at_sender=True)

@sv_user_info.on_command('我的精灵')
async def get_my_user_info(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        return await bot.send('请输入需要查询的精灵名称', at_sender=True)
    baseid = await get_rocom_name2id(args[0])
    if baseid == 0:
        return await bot.send('精灵名称不存在，请输入正确的精灵名称', at_sender=True)
    token, account_type = await RocomUser.get_rocom_token(ev.user_id, ev.bot_self_id)
    if not token:
        return await bot.send("用户token不存在，请绑定后再查询!")
    data = await rocom_api.get_rocom_pet_list(token=token, baseid=baseid, account_type=account_type)
    await bot.send(str(data))

@sv_user_info.on_command("绑定token")
async def add_my_user_token(bot: Bot, ev: Event):
    user_id = ev.user_id
    args = ev.text.split()
    if len(args) < 1:
        return await bot.send("请输入您需要绑定的token，用空格隔开!\n例rc绑定token xxtokenxx xxopenidxx\ntoken：用户authorization字段。\ntoken获取方式请输入【rctoken帮助】查询")
    bind_uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
    if not bind_uid:
        return await bot.send("你还没有绑定RC_UID哦!")
    token = args[0]
    data = await RocomUser.update_rocom_token(ev.user_id, ev.bot_self_id, token)
    shul = 1
    citiaobuttons = []
    xiabiao_list = []
    xuanze_list = ['手机QQ', '电脑QQ', '手机微信', '电脑微信']
    xuanze_name_list = [
        '手机QQ：QQ账号，手机获取的token',
        '电脑QQ：QQ账号，电脑获取的token',
        '手机微信：微信账号，手机获取的token',
        '电脑微信：微信账号，电脑获取的token'
    ]
    mes = ''
    for item_ct in xuanze_name_list:
        mes += f"\n{shul}·{item_ct}"
        xiabiao_list.append(str(shul))
        shul = shul + 1
    token_type_use = 0
    runmynum = 0
    try:
        async with timeout(60):
            while token_type_use == 0:
                if runmynum == 0:
                    mesg = f"token绑定成功{mes}\n请在60秒内选择您的token获取类型，默认为电脑QQ"
                    await bot.send(mesg)
                myresp = await bot.receive_mutiply_resp()
                if myresp is not None:
                    mys = myresp.text.strip()
                    user_id_my = myresp.user_id
                    if str(user_id_my) == str(user_id):
                        if mys in xuanze_list or mys in xiabiao_list:
                            if mys in xuanze_list:
                                tongken_xuanze = mys
                                token_type_use = 1
                            else:
                                mys_XB = int(mys)
                                tongken_xuanze = xuanze_list[mys_XB - 1]
                                token_type_use = 1
    except asyncio.TimeoutError:
        tongken_xuanze = '电脑QQ'
        token_type_use = 1
    account_type_list = {
        '手机QQ': 'qqmini',
        '电脑QQ': 'qq',
        '手机微信': 'wxmini',
        '电脑微信': 'wx'
    }
    account_type = account_type_list[tongken_xuanze]
    data = await RocomUser.update_rocom_stoken(ev.user_id, ev.bot_self_id, account_type)
    await bot.send('账号token绑定成功')

@sv_user_info.on_fullmatch("token帮助")
async def send_bind_card(bot: Bot, ev: Event):
    mes = "token为洛克王国小程序的Authorization字段\n1·准备好常用的抓包软件(如Fiddler)\n2·打开洛克王国小程序，点击我的，打开个人信息页面\n3·在抓包软件中找到数据的链接(通常为morefun·game·qq·com/)\n4·选中后进入查看抓包信息，在信息中找到Authorization字段复制\n5·返回机器人，输入rc绑定token+你获取到的Authorization完成绑定"
    await bot.send(mes)

@sv_user_info.on_fullmatch("绑定信息")
async def send_bind_card(bot: Bot, ev: Event):
    bind_uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
    if not bind_uid:
        return await bot.send("你还没有绑定RC_UID哦!")
    await bot.send(f"您绑定的RC_UID为{bind_uid}")

@sv_user_info.on_command(
    (
        "绑定uid",
        "绑定UID",
    )
)
async def send_link_uid_msg(bot: Bot, ev: Event):
    qid = ev.user_id
    rc_uid = ev.text.strip()
    if rc_uid and not rc_uid.isdigit():
        return await bot.send("你输入了错误的格式!")
    #print(rc_uid)
    #print(ev.bot_self_id)
    data = await RocomUser.insert_rocom_uid(qid, ev.bot_self_id, rc_uid)
    await send_diff_msg(
        bot,
        data,
        {
            0: f"✅[洛克王国]绑定UID{rc_uid}成功!",
            -1: f"❌RC_UID{rc_uid}的位数不正确!",
            -2: f"❌RC_UID{rc_uid}已经绑定过了!",
            -3: "❌你输入了错误的格式!",
        },
    )

