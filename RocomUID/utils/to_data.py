from pathlib import Path
from typing import Dict, List, Tuple, Union
from .rocom_api import wegame_api
from .convert import get_plant_info
from msgspec import json as msgjson

async def api_to_dict_home_info(
    uid: Union[str, None] = None,
    save_path: Union[Path, None] = None,
):
    home_data = await wegame_api.get_home_info(uid)
    homeinfo = home_data['home_info']
    home_info = {}
    home_info["home_info"] = {}
    #保存家园信息
    home_info["home_info"]['home_name'] = homeinfo['friend_home_brief_info']['home_name']
    home_info["home_info"]['home_experience'] = homeinfo['friend_home_brief_info']['home_experience']
    home_info["home_info"]['home_level'] = homeinfo['friend_home_brief_info']['home_level']
    home_info["home_info"]['room_level'] = homeinfo['friend_home_brief_info']['room_level']
    home_info["home_info"]['home_comfort_level'] = homeinfo['friend_home_brief_info']['home_comfort_level']
    #保存精灵信息
    home_info["home_info"]["home_pets"] = []
    home_pets = homeinfo['friend_cell_home_brief_info']['home_pets']
    for index, petinfo in enumerate(home_pets):
        if index == 0:
            continue
        pet_info = {}
        pet_info['pet_id'] = petinfo['home_pet_info']['pet_cfg_id']
        pet_info['name'] = petinfo['home_pet_info']['name']
        pet_info['gender'] = petinfo['display_info']['gender']
        pet_info['level'] = petinfo['display_info']['level']
        pet_info['mutation_type'] = petinfo['display_info']['mutation_type']
        pet_info['feed_info'] = {}
        if petinfo['home_pet_info'].get('feed_info', 0) != 0:
            pet_info["time_cost"] = int(petinfo['home_pet_info']['feed_info']['time_cost']/1000000)
            pet_info['pet_rip_time'] = int(petinfo['home_pet_info']['feed_info']['begin_time']/1000000) + int(petinfo['home_pet_info']['feed_info']['time_cost']/1000000)
        else:
            pet_info["time_cost"] = 0
            pet_info['pet_rip_time'] = 0
        pet_info['have_egg'] = petinfo['have_egg']
        home_info["home_info"]["home_pets"].append(pet_info)
    
    #保存种植信息
    home_plants = homeinfo['friend_cell_home_brief_info']['home_plant_info']['home_plant_land_list'][0]['home_plant_list']
    home_info["home_info"]['home_plants'] = []
    for index, plantinfo in enumerate(home_plants):
        plant_info = {}
        if plantinfo['plant_seed_id'] == 0:
            continue
        plant_info['plant_info'] = await get_plant_info(plantinfo['plant_seed_id'])
        plant_info['plant_rip_time'] = plantinfo['plant_rip_time']
        plant_info['plant_tab_id'] = plantinfo['plant_tab_id']
        home_info["home_info"]['home_plants'].append(plant_info)
    home_info["meta"] = home_data["meta"]
    if save_path and uid:
        path = save_path / uid
        path.mkdir(parents=True, exist_ok=True)
        with Path.open(path / "home_info.json", "wb") as file:
            _ = file.write(msgjson.format(msgjson.encode(home_info), indent=4))
    return home_info["home_info"]
