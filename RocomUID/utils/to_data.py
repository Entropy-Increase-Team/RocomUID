from pathlib import Path
import os
import json
from typing import Dict, Union

import msgspec
from msgspec import json as msgjson

from .rocom_api import wegame_api
from .convert import get_plant_info, get_skill_info
from .models import HomeInfo, PetInfoMap, PetPanelInfo

PET_NAME_MAP_PATH = Path(__file__).parent / "map" / "pet_name_map.json"
_pet_name_map: Dict[str, Dict[str, object]] = {}
_pet_name_map_loaded = False


def convert_home_info(data: Dict) -> HomeInfo:
    return msgspec.convert(data, type=HomeInfo)


def convert_pet_info_map(data: Dict) -> PetInfoMap:
    return msgspec.convert(data, type=PetInfoMap)


def get_pet_name_from_map(pet_id: Union[int, str]) -> Union[str, None]:
    global _pet_name_map_loaded, _pet_name_map

    if not _pet_name_map_loaded:
        try:
            with Path.open(PET_NAME_MAP_PATH, encoding='utf-8') as f:
                _pet_name_map = json.load(f)
        except Exception:
            _pet_name_map = {}
        _pet_name_map_loaded = True

    pet_info = _pet_name_map.get(str(pet_id), {})
    pet_name = pet_info.get('name') if isinstance(pet_info, dict) else None
    return pet_name if isinstance(pet_name, str) and pet_name else None


async def api_to_dict_home_info(
    uid: Union[str, None] = None,
    save_path: Union[Path, None] = None,
):
    home_data = await wegame_api.get_home_info(uid)
    if home_data is None:
        return await wegame_api._get_last_error()

    homeinfo = home_data['home_info']
    friend_home_brief_info = homeinfo.get('friend_home_brief_info') or {}
    if not isinstance(friend_home_brief_info, dict):
        return "没有获取到该用户的家园信息"

    home_info: dict = {
        "home_name": friend_home_brief_info.get('home_name') or '未命名家园',
        "home_experience": friend_home_brief_info.get('home_experience', 0),
        "home_level": friend_home_brief_info.get('home_level', 0),
        "room_level": friend_home_brief_info.get('room_level', 0),
        "home_comfort_level": friend_home_brief_info.get('home_comfort_level', 0),
        "home_pets": [],
        "home_plants": [],
        "finished_at": int(home_data["meta"]["finished_at"]),
    }

    home_pets = homeinfo['friend_cell_home_brief_info']['home_pets']
    for petinfo in home_pets:
        if petinfo['home_pet_info']['pet_cfg_id'] == 0:
            continue

        pet_record = {
            'pet_id': petinfo['home_pet_info']['pet_cfg_id'],
            'name': get_pet_name_from_map(petinfo['home_pet_info']['pet_cfg_id'])
            or f"未知精灵({petinfo['home_pet_info']['pet_cfg_id']})",
            'gender': petinfo['display_info']['gender'],
            'level': petinfo['display_info']['level'],
            'mutation_type': petinfo['display_info']['mutation_type'],
            'time_cost': 0,
            'pet_rip_time': 0,
            'have_egg': petinfo['have_egg'],
            'predicted_egg_time': petinfo.get('predicted_egg_time', 0),
            'status': petinfo['home_pet_info'].get('status', 0),
            'nature': petinfo['display_info'].get('nature', 0),
            'blood_id': petinfo['display_info'].get('blood_id', 0),
        }

        if petinfo['home_pet_info'].get('feed_info', 0) != 0:
            begin_time = int(petinfo['home_pet_info']['feed_info']['begin_time'])
            time_cost = int(petinfo['home_pet_info']['feed_info']['time_cost'])
            pet_record["time_cost"] = time_cost // 1000000
            pet_record['pet_rip_time'] = (
                begin_time // 1000000
                + time_cost // 1000000
            )

        home_info["home_pets"].append(pet_record)

    home_plants = homeinfo['friend_cell_home_brief_info']['home_plant_info']['home_plant_land_list'][0]['home_plant_list']
    for plantinfo in home_plants:
        if plantinfo['plant_seed_id'] == 0:
            continue

        plant_record = {
            'plant_info': await get_plant_info(plantinfo['plant_seed_id']),
            'plant_rip_time': plantinfo['plant_rip_time'],
            'plant_tab_id': plantinfo['plant_tab_id'],
        }
        home_info['home_plants'].append(plant_record)

    home_model = convert_home_info(home_info)

    if save_path and uid:
        path = save_path / uid
        path.mkdir(parents=True, exist_ok=True)
        with Path.open(path / "home_info.json", "wb") as file:
            _ = file.write(msgjson.format(msgjson.encode(msgspec.to_builtins(home_model)), indent=4))

    return home_model


async def api_to_dict_pet_info(
    uid: Union[str, None] = None,
    save_path: Union[Path, None] = None,
    include_home_name: bool = False,
):
    home_data = await wegame_api.get_home_pet_data(uid)
    if home_data is None:
        return await wegame_api._get_last_error()

    homeinfo = home_data['home_info']
    pet_info: Dict[str, object] = {'pets_list': {}}
    friend_home_brief_info = homeinfo.get('friend_home_brief_info') or {}
    pet_info['home_name'] = friend_home_brief_info.get('home_name') or '未命名家园'

    npc_pet_map = {
        str(item.get('pet_gid')): item
        for item in home_data.get('npc_pets', [])
        if item.get('pet_gid') is not None
    }

    home_pets = homeinfo['friend_cell_home_brief_info']['home_pets']
    for petinfo in home_pets:
        if petinfo['home_pet_info']['pet_cfg_id'] == 0:
            continue

        pet_gid = str(petinfo['home_pet_info']['pet_gid'])
        npc_pet_info = npc_pet_map.get(pet_gid, {})
        pethp = petatk = petspatk = petdef = petspdef = petspd = 0
        for item in petinfo['display_info']['attribute_new_info']['addi_attr_data']:
            if item['type'] == 1:
                pethp = item['addi_attr']
            if item['type'] == 2:
                petatk = item['addi_attr']
            if item['type'] == 3:
                petspatk = item['addi_attr']
            if item['type'] == 4:
                petdef = item['addi_attr']
            if item['type'] == 5:
                petspdef = item['addi_attr']
            if item['type'] == 6:
                petspd = item['addi_attr']

        pet_skill = []
        pet_skill_equip = []
        pet_feature = {}
        for item in petinfo['display_info']['skill']['skill_data']:
            if item["type"] == 1:
                info_skill = await get_skill_info(item["id"])
                iconid = (
                    item.get("iconid")
                    or item.get("icon_id")
                    or item.get("icon")
                    or info_skill.get("iconid")
                    or item["id"]
                )
                if not iconid:
                    iconid = item["id"]
                try:
                    iconid = int(iconid)
                except (TypeError, ValueError):
                    iconid = int(item["id"])
                skill_info = {
                    "id": item["id"],
                    "name": info_skill["name"],
                    "iconid": iconid,
                    "pos": item["pos"],
                    "is_equipped": item["is_equipped"],
                    "use_times": item["use_times"],
                }
                pet_skill.append(skill_info)
                if item["is_equipped"]:
                    pet_skill_equip.append(skill_info)
            if item["type"] == 2:
                pet_feature = await get_skill_info(item["id"])
                pet_feature['id'] = item["id"]

        pet_model = {
            "pet_id": petinfo['display_info']['base_conf_id'],
            "name": petinfo['display_info'].get('name', ''),
            "level": petinfo['display_info']['level'],
            "gender": petinfo['display_info']['gender'],
            "energy": petinfo['display_info']['energy'],
            "mutation_type": petinfo['display_info']['mutation_type'],
            "blood_id": petinfo['display_info']['blood_id'],
            "nature": petinfo['display_info']['nature'],
            "attribute_info": {
                "pethp": {
                    "value": pethp,
                    "talent": petinfo['display_info']['attribute_info']["hp"]["talent"],
                    "effort_add": petinfo['display_info']['attribute_info']["hp"]["effort_add"],
                },
                "petatk": {
                    "value": petatk,
                    "talent": petinfo['display_info']['attribute_info']["attack"]["talent"],
                    "effort_add": petinfo['display_info']['attribute_info']["attack"]["effort_add"],
                },
                "petspatk": {
                    "value": petspatk,
                    "talent": petinfo['display_info']['attribute_info']["special_attack"]["talent"],
                    "effort_add": petinfo['display_info']['attribute_info']["special_attack"]["effort_add"],
                },
                "petdef": {
                    "value": petdef,
                    "talent": petinfo['display_info']['attribute_info']["defense"]["talent"],
                    "effort_add": petinfo['display_info']['attribute_info']["defense"]["effort_add"],
                },
                "petspdef": {
                    "value": petspdef,
                    "talent": petinfo['display_info']['attribute_info']["special_defense"]["talent"],
                    "effort_add": petinfo['display_info']['attribute_info']["special_defense"]["effort_add"],
                },
                "petspd": {
                    "value": petspd,
                    "talent": petinfo['display_info']['attribute_info']["speed"]["talent"],
                    "effort_add": petinfo['display_info']['attribute_info']['speed']['effort_add'],
                },
            },
            "equip_skills": pet_skill_equip,
            "skills": pet_skill,
            "feature": pet_feature,
            "glass_info": petinfo['display_info']['glass_info'],
            "voice": (
                npc_pet_info
                .get('npc_pet', {})
                .get('pet', {})
                .get('voice')
            ),
        }

        pet_info["pets_list"][pet_gid] = msgspec.to_builtins(
            msgspec.convert(pet_model, type=PetPanelInfo)
        )

    if save_path and uid:
        path = save_path / uid
        path.mkdir(parents=True, exist_ok=True)
        with Path.open(path / "pet_info.json", "wb") as file:
            _ = file.write(msgjson.format(msgjson.encode(msgspec.to_builtins(pet_info)), indent=4))

    pet_info_map = convert_pet_info_map(pet_info["pets_list"])
    if include_home_name:
        return pet_info_map, pet_info['home_name']
    return pet_info_map
