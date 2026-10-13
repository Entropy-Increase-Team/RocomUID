import re
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.subscribe import Subscribe, gs_subscribe
from gsuid_core.sv import SV
from ..utils.error_reply import prefix as P

sv_self_config = SV("洛克王国配置")

# 开启 / 关闭 远行商人推送功能。
@sv_self_config.on_command(('开启远行商人', '关闭远行商人'))
async def open_switch_func(bot: Bot, ev: Event):
    user_id = ev.user_id
    command = str(getattr(ev, 'command', '')).strip()
    action = '开启' if command.startswith('开启') else '关闭'
    config_name = command.removeprefix(action)

    arg = str(getattr(ev, 'text', '') or '').strip()
    at_all = config_name == '远行商人' and arg == '艾特'
    if arg and not at_all:
        return await bot.send(
            f'🔨 [洛克王国服务]\n❌ 未知参数「{arg}」\n'
            f'🚩 例如: {P}开启远行商人艾特'
        )

    if at_all and not ev.group_id:
        return await bot.send('🔨 [洛克王国服务]\n❌ 推送艾特全体仅群聊可用。')

    if ev.group_id:
        open_type = '群'
        uid = ev.group_id
    else:
        open_type = '用户'
        uid = ev.user_id
    
    logger.info(
        f'[洛克王国服务] [{user_id}]尝试[{action}]了'
        f'[{config_name}{"艾特" if at_all else ""}]功能'
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
                    'WS_BOT_ID': ev.WS_BOT_ID,
                },
            )
        else:
            from msgspec.structs import replace as _struct_replace

            await gs_subscribe.add_subscribe(
                'single',
                c_name,
                _struct_replace(ev, msg_id=''),
                uid=uid,
            )

        if at_all:
            from ..rocom_merchant import set_merchant_at_all

            await set_merchant_at_all(uid, True)
            im += '\n🔔 推送时会@全体成员。'

    elif at_all:
        from ..rocom_merchant import set_merchant_at_all

        if await set_merchant_at_all(uid, False):
            im = (
                f'🔨 [洛克王国服务]\n✅ 已为[{open_type}{uid}]'
                f'关闭{config_name}推送的@全体成员。'
            )
        else:
            im = f'🔨 [洛克王国服务]\n❌ 未找到[{open_type}{uid}]的{config_name}功能配置, 该功能可能未开启。'
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
