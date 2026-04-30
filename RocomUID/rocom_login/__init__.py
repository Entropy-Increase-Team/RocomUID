import re
import json
import time
import asyncio
import base64
import time
from async_timeout import timeout
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from ..utils.rocom_api import wegame_api
from gsuid_core.segment import MessageSegment
from ..utils.error_reply import get_error
from gsuid_core.logger import logger
from ..utils.database.model import RocomUser
from gsuid_core.utils.image.convert import convert_img
from ..rocom_config.rocom_config import RC_CONFIG
wegame_api_key: str = RC_CONFIG.get_config("RC_wegame_key").data

sv_user_login = SV('rc用户登录', priority=5)

@sv_user_login.on_command(('QQ登录','QQ扫码'))
async def rocom_qq_login(bot: Bot, ev: Event):
    if wegame_api_key == '':
        return await bot.send("未设置wegame_api_key，请联系机器人管理员设置后再次查询", at_sender=True)
    user_id = ev.user_id
    qr_data = await wegame_api.qq_qr_login(user_id)
    if not qr_data or "qr_image" not in qr_data:
        return await bot.send("获取 QQ 二维码失败。")
    fw_token = qr_data["frameworkToken"]
    qr_b64 = qr_data["qr_image"]
    img_data = base64.b64decode(qr_b64.split(",")[-1])
    res = await convert_img(img_data)
    mesg = []
    mesg.append(MessageSegment.image(res))
    mesg.append(MessageSegment.text("请使用 QQ 扫描二维码登录 (有效时间 2 分钟)\n⚠️ 注意需要双设备扫码！"))
    await bot.send(mesg)
    
    start_time = time.time()
    success = False
    while time.time() - start_time < 115:
        await asyncio.sleep(3)
        status = await wegame_api.qq_qr_status(fw_token, user_id)
        if not status:
            continue
        
        state = status.get("status")
        if state == "done":
            success = True
            break
        elif state in ["expired", "failed", "canceled"]:
            break
        
    if success:
        await bot.send("登录成功，正在调用绑定接口...")
        bind_res = await wegame_api.create_binding(fw_token, user_id)
        if not bind_res or not bind_res.get("binding"):
            return await bot.send("绑定接口调用失败，请稍后重试。")
        await bot.send("绑定成功，正在获取角色信息...")
        role_res = await wegame_api.get_role(fw_token)
        # 检查角色信息获取是否成功
        if not role_res or not role_res.get("role"):
            logger.warning(f"[Rocom] 获取角色信息失败，fw_token 可能无效或过期")
            return await bot.send("⚠️ 绑定成功，但获取角色信息失败（凭证可能无效或已过期）。请尝试重新登录。")
        
        role = role_res.get("role", {})
        binding_data = bind_res.get("binding", {})
        binding_id = binding_data.get("id", fw_token)
        binding = {
            "framework_token": fw_token,
            "binding_id": binding_id,
            "login_type": 'qq',
            "uid": role.get("id", "未知"),
            "nickname": role.get("name", "洛克"),
            "bind_time": int(time.time() * 1000),
            "is_primary": True
        }
        data = await RocomUser.insert_rocom_uid_qr(user_id, ev.bot_self_id, binding)
        await bot.send(f"✅ 绑定成功！当前账号：{binding['nickname']} (ID: {binding['uid']})")
        
    else:
        await bot.send("登录超时或失败，请重试。")


@sv_user_login.on_command(('WX登录','微信扫码'))
async def rocom_wx_login(bot: Bot, ev: Event):
    if wegame_api_key == '':
        return await bot.send("未设置wegame_api_key，请联系机器人管理员设置后再次查询", at_sender=True)
    user_id = ev.user_id
    qr_data = await wegame_api.wechat_qr_login(user_id)
    if not qr_data or "qr_image" not in qr_data:
        return await bot.send("获取微信登录链接失败。")
    fw_token = qr_data["frameworkToken"]
    qr_url = qr_data["qr_image"]
    mes = f"请使用微信打开以下链接扫码登录 (有效时间 2 分钟)\n⚠️ 注意需要双设备扫码！\n{qr_url}"
    await bot.send(mes)
    
    start_time = time.time()
    success = False
    while time.time() - start_time < 115:
        await asyncio.sleep(3)
        status = await wegame_api.wechat_qr_status(fw_token, user_id)
        if not status:
            continue
        
        state = status.get("status")
        if state == "done":
            success = True
            break
        elif state in ["expired", "failed", "canceled"]:
            break
        
    if success:
        await bot.send("登录成功，正在调用绑定接口...")
        bind_res = await wegame_api.create_binding(fw_token, user_id)
        if not bind_res or not bind_res.get("binding"):
            return await bot.send("绑定接口调用失败，请稍后重试。")
        await bot.send("绑定成功，正在获取角色信息...")
        role_res = await wegame_api.get_role(fw_token)
        # 检查角色信息获取是否成功
        if not role_res or not role_res.get("role"):
            logger.warning(f"[Rocom] 获取角色信息失败，fw_token 可能无效或过期")
            return await bot.send("⚠️ 绑定成功，但获取角色信息失败（凭证可能无效或已过期）。请尝试重新登录。")
        
        role = role_res.get("role", {})
        binding_data = bind_res.get("binding", {})
        binding_id = binding_data.get("id", fw_token)
        binding = {
            "framework_token": fw_token,
            "binding_id": binding_id,
            "login_type": 'wechat',
            "uid": role.get("id", "未知"),
            "nickname": role.get("name", "洛克"),
            "bind_time": int(time.time() * 1000),
        }
        data = await RocomUser.insert_rocom_uid_qr(user_id, ev.bot_self_id, binding)
        await bot.send(f"✅ 绑定成功！当前账号：{binding['nickname']} (ID: {binding['uid']})")
        
    else:
        await bot.send("登录超时或失败，请重试。")