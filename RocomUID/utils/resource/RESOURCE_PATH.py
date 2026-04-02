import sys
from gsuid_core.data_store import get_res_path


MAIN_PATH = get_res_path() / 'RocomUID'
sys.path.append(str(MAIN_PATH))

PLAYER_PATH = MAIN_PATH / 'players'
RESOURCE_PATH = MAIN_PATH / 'resource'

ROCOM_ICON_PATH = RESOURCE_PATH / 'rocomicon'
ROCOM_SKILL_PATH = RESOURCE_PATH / 'skillicon'


def init_dir():
    for i in [
        MAIN_PATH,
        PLAYER_PATH,
        RESOURCE_PATH,
        ROCOM_ICON_PATH,
        ROCOM_SKILL_PATH,
    ]:
        i.mkdir(parents=True, exist_ok=True)


init_dir()
