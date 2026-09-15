import json
from typing import Dict
from pathlib import Path

import aiofiles
from PIL import Image
from gsuid_core.help.model import PluginHelp
from gsuid_core.sv import get_plugin_available_prefix
from gsuid_core.help.draw_new_plugin_help import get_new_help
from ..version import RocomUID_version
from ..utils.image.image_tools import get_footer, FOOTER_HELP

ICON = Path(__file__).parent.parent.parent / "ICON.png"
HELP_DATA = Path(__file__).parent / "help.json"
ICON_PATH = Path(__file__).parent / "icon_path"
TEXT_PATH = Path(__file__).parent / "texture2d"

PREFIX = get_plugin_available_prefix("RocomUID")

async def get_help_data() -> Dict[str, PluginHelp]:
    async with aiofiles.open(HELP_DATA, "rb") as file:
        return json.loads(await file.read())

async def get_help():
    return await get_new_help(
        plugin_name="RocomUID",
        plugin_info={f"v{RocomUID_version}": ""},
        plugin_icon=Image.open(ICON),
        plugin_help=await get_help_data(),
        plugin_prefix=PREFIX,
        help_mode="dark",
        banner_bg=Image.open(TEXT_PATH / "banner_bg.jpg"),
        banner_sub_text="携宠并肩战斗-魔法世界等你揭秘",
        help_bg=Image.open(TEXT_PATH / "bg.jpg"),
        cag_bg=Image.open(TEXT_PATH / "cag_bg.png"),
        item_bg=Image.open(TEXT_PATH / "item.png"),
        icon_path=ICON_PATH,
        footer=get_footer(FOOTER_HELP),
        enable_cache=True,
    )
