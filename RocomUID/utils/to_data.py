from pathlib import Path
import os
import json
from typing import Dict, List, Tuple, Union
from .rocom_api import wegame_api
from .convert import get_plant_info, get_skill_info
from msgspec import json as msgjson

async def api_to_dict_home_info(
    uid: Union[str, None] = None,
    save_path: Union[Path, None] = None,
):
    home_data = await wegame_api.get_home_info(uid)
    if home_data == None:
        return await wegame_api._get_last_error()
    homeinfo = home_data['home_info']
    home_info = {}
    home_info["home_info"] = {}
    if homeinfo.get('friend_home_brief_info', 0) == 0:
        return "没有获取到该用户的家园信息"
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
        if petinfo['home_pet_info']['pet_cfg_id'] == 0:
            continue
        pet_info = {}
        pet_info['pet_id'] = petinfo['home_pet_info']['pet_cfg_id']
        pet_info['name'] = petinfo['home_pet_info']['name']
        pet_info['gender'] = petinfo['display_info']['gender']
        pet_info['level'] = petinfo['display_info']['level']
        pet_info['mutation_type'] = petinfo['display_info']['mutation_type']
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
    home_return_date = {}
    home_return_date = home_info["home_info"]
    home_return_date['finished_at'] = home_info['meta']["finished_at"]
    return home_return_date

async def api_to_dict_pet_info(
    uid: Union[str, None] = None,
    save_path: Union[Path, None] = None,
):
    home_data = await wegame_api.get_home_info(uid)
    if home_data == None:
        return await wegame_api._get_last_error()
    pet_info_path = save_path / uid / 'pet_info.json'
    local_pet_info = {}
    if os.path.exists(pet_info_path):
        with Path.open(pet_info_path, encoding='utf-8') as f:
            local_pet_info = json.load(f)
    homeinfo = home_data['home_info']
    pet_info = local_pet_info
    if pet_info.get('pets_list', 0) == 0:
        pet_info['pets_list'] = {}
    #保存精灵信息
    home_pets = homeinfo['friend_cell_home_brief_info']['home_pets']
    for index, petinfo in enumerate(home_pets):
        #过滤无详细数据的护卫精灵
        if petinfo['home_pet_info']['pet_cfg_id'] == 0:
            continue
        #保存基础数据
        #已宠物实例id来记录宠物数据
        pet_gid = str(petinfo['home_pet_info']['pet_gid'])
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
            #保存可释放技能
            if item["type"] == 1:
                info_skill = await get_skill_info(item["id"])
                skill_info = {
                    "id" : item["id"], #技能id
                    "name" : info_skill["name"], #技能名称
                    "pos" : item["pos"], #技能位置
                    "is_equipped" : item["is_equipped"], #是否装备技能
                    "use_times" : item["use_times"] #技能释放次数
                }
                pet_skill.append(skill_info)
                if item["is_equipped"]:
                    pet_skill_equip.append(skill_info)
            if item["type"] == 2:
                pet_feature = await get_skill_info(item["id"])
            
        
        pet_info["pets_list"][pet_gid] = {
            "pet_id" : petinfo['display_info']['base_conf_id'],#宠物ID
            "name" : petinfo['display_info']['name'],#宠物昵称
            "level" : petinfo['display_info']['level'],#宠物等级
            "gender" : petinfo['display_info']['gender'],#宠物性别
            "energy" : petinfo['display_info']['energy'],#宠物性别
            "mutation_type" : petinfo['display_info']['mutation_type'],#宠物稀有类型
            "blood_id" : petinfo['display_info']['blood_id'],#宠物血脉属性
            "nature" : petinfo['display_info']['nature'],#宠物性格
            "attribute_info":{
                "pethp":{
                    "value" : pethp, #生命值
                    "talent" : petinfo['display_info']['attribute_info']["hp"]["talent"], #个体值
                    "effort_add" : petinfo['display_info']['attribute_info']["hp"]["effort_add"], #成长值
                },
                "petatk":{
                    "value" : petatk, #物攻
                    "talent" : petinfo['display_info']['attribute_info']["attack"]["talent"], #个体值
                    "effort_add" : petinfo['display_info']['attribute_info']["attack"]["effort_add"], #成长值
                },
                "petspatk":{
                    "value" : petspatk, #魔攻
                    "talent" : petinfo['display_info']['attribute_info']["special_attack"]["talent"], #个体值
                    "effort_add" : petinfo['display_info']['attribute_info']["special_attack"]["effort_add"], #成长值
                },
                "petdef":{
                    "value" : petdef, #物防
                    "talent" : petinfo['display_info']['attribute_info']["defense"]["talent"], #个体值
                    "effort_add" : petinfo['display_info']['attribute_info']["defense"]["effort_add"], #成长值
                },
                "petspdef":{
                    "value" : petspdef, #魔防
                    "talent" : petinfo['display_info']['attribute_info']["special_defense"]["talent"], #个体值
                    "effort_add" : petinfo['display_info']['attribute_info']["special_defense"]["effort_add"], #成长值
                },
                "petspd":{
                    "value" : petspd, #速度
                    "talent" : petinfo['display_info']['attribute_info']["speed"]["talent"], #个体值
                    "effort_add" : petinfo['display_info']['attribute_info']["speed"]["effort_add"], #成长值
                }
            },
            "equip_skills": pet_skill_equip, #已装备技能信息
            "skills": pet_skill, #技能信息
            "feature" : pet_feature, #特性信息
            "glass_info" : petinfo['display_info']['glass_info'],#宠物稀有类型
        }
        
    pet_info["meta"] = home_data["meta"]
    if save_path and uid:
        path = save_path / uid
        path.mkdir(parents=True, exist_ok=True)
        with Path.open(path / "pet_info.json", "wb") as file:
            _ = file.write(msgjson.format(msgjson.encode(pet_info), indent=4))
    return pet_info["pets_list"]
        