import re
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.subscribe import Subscribe, gs_subscribe
from gsuid_core.sv import SV
from ..utils.error_reply import prefix as P

sv_self_config = SV("洛克王国配置")

PRIV_MAP = {
    '推送': None,
    '远行商人': None,
}

# 开启 自动签到 和 推送树脂提醒 功能
@sv_self_config.on_prefix(("开启", "关闭"))
async def open_switch_func(bot: Bot, ev: Event):
    user_id = ev.user_id
    config_name = ev.text
    if config_name.startswith(('体力')):
        config_name = config_name.replace('推送', '')

    if config_name not in PRIV_MAP:
        return await bot.send(
            f'🔨 [洛克王国服务]\n❌ 请输入正确的功能名称...\n🚩 例如: {P}开启远行商人'
        )
    
    if ev.group_id:
        open_type = '群'
        uid = ev.group_id
    else:
        open_type = '用户'
        uid = ev.user_id
    
    command = str(getattr(ev, 'command', '')).strip()
    action = '开启' if '开启' in command else '关闭' if '关闭' in command else command
    logger.info(
        f'[洛克王国服务] [{user_id}]尝试[{action}]了[{ev.text}]功能'
    )

    c_name = f'[洛克王国] {config_name}'

    if action == '开启':
        im = f'🔨 [洛克王国服务]\n✅ 已为[{open_type}{uid}]开启{config_name}功能。'

        if await gs_subscribe.get_subscribe(c_name, uid=uid):
            await Subscribe.update_data_by_data(
                {
                    'task_name': c_name,
                    'uid': uid,
                },
                {
                    'user_id': ev.user_id,
                    'bot_id': ev.bot_id,
                    'group_id': ev.group_id,
                    'bot_self_id': ev.bot_self_id,
                    'user_type': ev.user_type,
                    'extra_message': PRIV_MAP[config_name],
                    'WS_BOT_ID': ev.WS_BOT_ID,
                    'msg_id': ev.msg_id,
                },
            )
        else:
            await gs_subscribe.add_subscribe(
                'single',
                c_name,
                ev,
                extra_message=PRIV_MAP[config_name],
                uid=uid,
            )

        if PRIV_MAP[config_name]:
            im += f'\n🔧 并设置了触发阈值为{PRIV_MAP[config_name]}!'
            if not await gs_subscribe.get_subscribe('[洛克王国] 推送', uid=uid):
                im += '\n⚠ 警告: 由于未打开推送总开关, 所以此项设置可能无效！'
                im += f'如需打开总开关, 请发送命令开启推送: {P}开启推送！'
    else:
        data = await gs_subscribe.get_subscribe(c_name, uid=uid)
        if data:
            await Subscribe.delete_row(
                task_name=c_name,
                uid=uid,
            )
            im = f'🔨 [洛克王国服务]\n✅ 已为[{open_type}{uid}]关闭{config_name}功能。'
        else:
            im = f'🔨 [洛克王国服务]\n❌ 未找到[{open_type}{uid}]的{config_name}功能配置, 该功能可能未开启。'

    await bot.send(im)
