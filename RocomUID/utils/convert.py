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

class Roster:
    def __init__(self):
        self._roster = pygtrie.CharTrie()
        self.update()

    def update(self):
        self._roster.clear()
        for idx, names in rocom_name_list.items():
            for n in names:
                if n not in self._roster:
                    self._roster[n] = idx
        self._all_name_list = self._roster.keys()

    async def get_name(self, name):
        return self._roster[name] if name in self._roster else ''
    
    async def guess_name(self, name):
        """@return: id, name, score"""
        name, score = process.extractOne(name, self._roster.keys())
        return self._roster[name], score

roster = Roster()

async def get_rocom_name(name):
    rocom_name = await roster.get_name(name)
    confi = 100
    guess = False
    if rocom_name != '':
        return rocom_name
    if rocom_name == '':
        rocom_name, confi = await roster.guess_name(name)
        guess = True
    if confi < 60:
        return 0
    if guess:
        return rocom_name
    return ''
    
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