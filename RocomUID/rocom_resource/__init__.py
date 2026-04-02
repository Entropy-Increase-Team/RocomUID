from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.resource.download_all_file import check_use

sv_rc_download_config = SV('rc下载资源', pm=1)


@sv_rc_download_config.on_fullmatch('下载全部资源')
async def send_download_resource_msg(bot: Bot, ev: Event):
    await bot.send('rc正在开始下载~可能需要较久的时间!')
    im = await check_use()
    await bot.send(im)


async def startup():
    await check_use()
