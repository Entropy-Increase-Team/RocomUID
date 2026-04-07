from gsuid_core.utils.download_resource.download_core import download_all_file

from .RESOURCE_PATH import ROCOM_ICON_PATH, ROCOM_SKILL_PATH, ROCOM_CHARACTER_PATH, ROCOM_HEAD_PATH


async def check_use():
    await download_all_file(
        "RocomUID",
        {
            "resource/rocomicon": ROCOM_ICON_PATH,
            "resource/skillicon": ROCOM_SKILL_PATH,
            "resource/characteristicicon": ROCOM_CHARACTER_PATH,
            "resource/headicon": ROCOM_HEAD_PATH,
        },
    )
    return "rc全部资源下载完成!"
