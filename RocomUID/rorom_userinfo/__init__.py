import re
import json
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from ..utils.convert import get_rocom_name
from ..utils.rocom_api import rocom_api
from ..utils.error_reply import UID_HINT
from gsuid_core.logger import logger
from ..utils.database.model import RocomUser
from ..utils.message import send_diff_msg
from ..utils.api_client import APIClient

sv_user_info = SV('rc用户信息查询', priority=5)

@sv_user_info.on_command('我的信息')
async def get_my_user_info(bot: Bot, ev: Event):
    token = await RocomUser.get_rocom_token(ev.user_id, ev.bot_self_id)
    if not token:
        return await bot.send("用户token不存在，请绑定后再查询!")
    data = await rocom_api.get_game_info(token=token)
    await bot.send(str(data))

# @sv_user_info.on_command('查询信息')
# async def get_my_rocom_info(bot: Bot, ev: Event):
    # api_client = APIClient(
        # use_miniapp_auth=False,  # Cookie池不使用小程序验证
        # miniapp_auth='',
        # miniapp_data="",  # Cookie池不需要data参数,仅用于兑换
        # web_cookie="",
        # timeout=5,
        # use_proxy=False,
        # proxy_host="",
        # proxy_port=0
    # )
    # data = api_client._get_announcement_list_no_auth()
    # print(str(data))
    # #await bot.send(str(data))

@sv_user_info.on_command(("绑定token","绑定openid"))
async def add_my_user_token(bot: Bot, ev: Event):
    args = ev.text.split()
    if len(args) < 1:
        return await bot.send("请输入您需要绑定的token，用空格隔开!\n例rc绑定token xxtokenxx xxopenidxx\ntoken：用户authorization字段")
    bind_uid = await RocomUser.select_rocom_user(ev.user_id, ev.bot_self_id)
    if not bind_uid:
        return await bot.send("你还没有绑定RC_UID哦!")
    token = args[0]
    data = await RocomUser.update_rocom_token(ev.user_id, ev.bot_self_id, token)
    await send_diff_msg(
        bot,
        data,
        {
            0: f"✅[洛克王国]绑定token成功!",
            -1: f"❌[洛克王国]绑定token失败!",
        },
    )
    

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

