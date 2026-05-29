from fuzzywuzzy import process
import pygtrie
from .map.rocom_map import rocom_name_list
from pathlib import Path
import json

Excel_path = Path(__file__).parent
with Path.open(Excel_path / 'map' /'name-map.json', encoding='utf-8') as f:
    name_id_list = json.load(f)

with Path.open(Excel_path / 'map' /'breeding.json', encoding='utf-8') as f:
    breeding = json.load(f)
    rocom_egg_conf = breeding["pet_egg_conf"]

with Path.open(Excel_path / 'map' /'rank_list.json', encoding='utf-8') as f:
    rank_list = json.load(f)

with Path.open(Excel_path / 'map' /'RANDOM_GOODS_CONF.json', encoding='utf-8') as f:
    random_goods = json.load(f)
    random_good_list = random_goods['RocoDataRows']

with Path.open(Excel_path / 'map' /'home_item_list.json', encoding='utf-8') as f:
    home_plant_list = json.load(f)

with Path.open(Excel_path / 'map' /'mini-map.json', encoding='utf-8') as f:
    pet_skill_list = json.load(f)

with Path.open(Excel_path / 'map' /'pet_list.json', encoding='utf-8') as f:
    pet_list = json.load(f)

class Roster:
    def __init__(self):
        self._roster = pygtrie.CharTrie()
        self.update()

    def update(self):
        self._roster.clear()
        for idx, item in pet_list.items():
            from_name = item.get('form','')
            if from_name != '':
                if from_name not in self._roster:
                    self._roster[from_name] = idx
            pet_name = f"{item['name']}{from_name}"
            if pet_name not in self._roster:
                self._roster[pet_name] = idx
            if f"{from_name}{item['name']}" not in self._roster:
                self._roster[f"{from_name}{item['name']}"] = idx
        self._all_name_list = self._roster.keys()

    async def get_name(self, name):
        return self._roster[name] if name in self._roster else 0
    
    async def guess_name(self, name):
        """@return: id, name, score"""
        name, score = process.extractOne(name, self._roster.keys())
        return self._roster[name], score

roster = Roster()

async def get_rocom_name(name):
    rocom_name = await roster.get_name(name)
    confi = 100
    guess = False
    if rocom_name != 0:
        return rocom_name
    if rocom_name == 0:
        rocom_name, confi = await roster.guess_name(name)
        guess = True
    if confi < 60:
        return 0
    if guess:
        return rocom_name
    return 0
    
async def get_rocom_name2id(name):
    rocom_name = await get_rocom_name(name)
    if rocom_name == '':
        return 0
    for rocomid in name_id_list:
        if name_id_list[rocomid] == rocom_name:
            return int(rocomid)
    return 0
    
async def get_rankid2name(rankid):
    for item in rank_list:
        if str(rankid) == item['id']:
            return item['name']
    return '————'

async def get_plant_info(plantid):
    plant_info = home_plant_list[str(plantid)]
    return plant_info

async def get_skill_info(skillid):
    skill_info = pet_skill_list[str(skillid)]
    return skill_info
    
async def get_pet_info(petid):
    pet_info = pet_list[str(petid)]
    return pet_info