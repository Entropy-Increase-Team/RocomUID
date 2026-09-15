from fuzzywuzzy import process
import pygtrie
from pathlib import Path
import json

Excel_path = Path(__file__).parent
MAP_PATH = Excel_path / 'map'


def _load_json(name, default):
    """读取 map 目录下的 json，缺失或损坏时返回默认值，避免拖垮整个插件加载。"""
    try:
        with Path.open(MAP_PATH / name, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


# ------------------------------ 基础数据 ------------------------------
# pet_data.json        精灵基础数据（种族值 / 系别 / 蛋组 / 技能列表）
# skill_data.json      技能与特性数据
# pets_aux_lineage.json 进化链数据
_pet_raw = _load_json('pet_data.json', [])
_skill_raw = _load_json('skill_data.json', [])
_lineage_raw = _load_json('pets_aux_lineage.json', {})

_breeding_raw = _load_json('breeding.json', {})
rocom_egg_conf = _breeding_raw.get('pet_egg_conf', [])
nature_map = _load_json('nature_map.json', {})
rank_list = _load_json('rank_list.json', [])
home_plant_list = _load_json('home_item_list.json', {})
random_good_list = _load_json('RANDOM_GOODS_CONF.json', {}).get('RocoDataRows', [])

# ------------------------------ id 映射表 ------------------------------
# 系别 id(数据包编号) -> 系别名
UNIT_TYPE_NAME = {
    1: '普通',
    2: '草',
    3: '火',
    4: '水',
    5: '光',
    6: '地',
    7: '冰',
    8: '龙',
    9: '电',
    10: '毒',
    11: '虫',
    12: '武',
    13: '翼',
    14: '萌',
    15: '幽',
    16: '恶',
    17: '机械',
    18: '幻',
}

# 系别名 -> 绘图编号（与各绘图模块 SHUX_LIST_DRAW 的编号保持一致）
UNIT_TYPE_DRAW_ID = {
    name: draw_id for draw_id, name in {
        2: '普通',
        3: '草',
        4: '火',
        5: '水',
        6: '光',
        8: '地',
        9: '冰',
        10: '龙',
        11: '电',
        12: '毒',
        13: '虫',
        14: '武',
        15: '翼',
        16: '萌',
        17: '幽',
        18: '恶',
        19: '机械',
        20: '幻',
        23: '污染',
    }.items()
}

# 蛋组 id -> 蛋组名
EGG_GROUP_NAME = {
    1: '未发现',
    2: '巨灵组',
    3: '两栖组',
    4: '昆虫组',
    5: '天空组',
    6: '动物组',
    7: '妖精组',
    8: '植物组',
    9: '拟人组',
    10: '软体组',
    11: '岩石组',
    12: '魔力组',
    13: '海洋组',
    14: '巨龙组',
    15: '机械组',
}

# ------------------------------ 天赋 ------------------------------
# 随机天赋名称表，索引即天赋随机 id
TALENT_RANDOM_LIST = (
    '无', '奇袭', '亲密', '灵巧', '疾行', '同乘', '无畏', '爱分享', '家里蹲', '热心教', '慈悲为怀',
)
TALENT_RANDOM_LIST_NO_RIDE = tuple(t for t in TALENT_RANDOM_LIST if t != '同乘')

# 拥有“同乘”天赋的精灵 id（查蛋-同乘筛选使用），数据见 map/tongcheng_pet_ids.json
TONGCHENG_PET_IDS = frozenset(
    str(pet_id)
    for pet_id in _load_json('tongcheng_pet_ids.json', {}).get('pet_ids', [])
)


# ------------------------------ 技能 ------------------------------
def _family_name(families):
    families = str(families or '').strip()
    if families.isdigit():
        return UNIT_TYPE_NAME.get(int(families), '无')
    if families in ('', 'SDT_NONE'):
        return '无'
    return families


def _build_skill(skill_id):
    raw = _skill_raw_by_id.get(skill_id)
    if raw is None:
        return {
            'id': skill_id,
            'name': f'未知技能({skill_id})',
            'iconid': skill_id,
            'families': '未知',
            'cost': '0',
            'power': '0',
            'desc': '技能数据暂未收录',
        }
    return {
        'id': skill_id,
        'name': raw.get('name', ''),
        'iconid': raw.get('iconid', skill_id),
        'families': _family_name(raw.get('families')),
        'cost': str(raw.get('cost', '0')),
        'power': str(raw.get('power', '0')),
        'desc': raw.get('desc', ''),
    }


def _parse_id_list(value):
    ids = []
    for item in str(value or '').split(','):
        item = item.strip()
        if item.isdigit():
            ids.append(int(item))
    return ids


_skill_raw_by_id = {int(item['skill_id']): item for item in _skill_raw}

# 技能名 -> [系别, 消耗, 威力, 介绍]（同名技能取第一条）
skill_list = {}
for _item in _skill_raw:
    skill_list.setdefault(_item.get('name', ''), [
        _family_name(_item.get('families')),
        str(_item.get('cost', '0')),
        str(_item.get('power', '0')),
        _item.get('desc', ''),
    ])


# ------------------------------ 蛋/进化 ------------------------------
def _build_breeding_map():
    """按精灵 id 聚合 breeding.json 中的蛋数据（pet_id 形如 3001001 -> 精灵 3001）。"""
    result = {}
    for egg in rocom_egg_conf:
        key = str(egg.get('pet_id', 0) // 1000)
        result.setdefault(key, egg)
    return result


_breeding_map = _build_breeding_map()


def _build_evolution_list(pet_id):
    """从进化链数据还原完整进化链（与图鉴绘制的 3 个位置对应）。"""
    lineage = _lineage_raw.get(str(pet_id)) or {}
    lineages = lineage.get('lineages') or []
    if not lineages:
        return []
    nodes = sorted(lineages[0].get('nodes') or [], key=lambda item: item.get('stage', 0))
    evolution_list = []
    for node in nodes[:3]:
        target_id = node.get('pet_id')
        target = _pet_raw_by_id.get(str(target_id)) or {}
        form = node.get('form') or target.get('form') or ''
        if form == 'default':
            form = ''
        name = node.get('name', '')
        conditions = [
            str(text) for text in (node.get('conditions') or [])
            if '等级' not in str(text)
        ]
        evolution_list.append({
            'pet_id': target_id,
            'name': f'{name}({form})' if form else name,
            'level': node.get('level', 0),
            'icon': target.get('icon', ''),
            'evolution_need': ''.join(f'{text}；' for text in conditions),
        })
    return evolution_list


# ------------------------------ 精灵 ------------------------------
def _build_pet(entry):
    pet_id = entry.get('pet_id')
    unit_ids = _parse_id_list(entry.get('unit_type_list'))
    unit_names = [UNIT_TYPE_NAME.get(item, '无') for item in unit_ids]
    form = entry.get('form') or ''
    if form == 'default':
        form = ''

    return {
        'id': pet_id,
        'name': entry.get('name', ''),
        'form': form,
        'icon': entry.get('icon', ''),
        'shiny_icon': entry.get('shiny_icon', ''),
        'description': entry.get('description', ''),
        'weight_low': entry.get('weight_low', 0),
        'weight_high': entry.get('weight_high', 0),
        'height_low': entry.get('height_low', 0),
        'height_high': entry.get('height_high', 0),
        'unit_type': unit_names,
        'unit_type_list': [UNIT_TYPE_DRAW_ID.get(name, 23) for name in unit_names],
        'attribute': {
            'attr_hp': entry.get('attr_hp', 0),
            'attr_atk': entry.get('attr_atk', 0),
            'attr_spatk': entry.get('attr_spatk', 0),
            'attr_def': entry.get('attr_def', 0),
            'attr_spdef': entry.get('attr_spdef', 0),
            'attr_spd': entry.get('attr_spd', 0),
        },
        'feature': _build_skill(entry.get('feature')) if entry.get('feature') else {
            'id': 0, 'name': '', 'desc': '',
        },
        'egg_group': [
            EGG_GROUP_NAME.get(item, '未知组') for item in _parse_id_list(entry.get('egg_group'))
        ],
        'level_skill_list': [
            _build_skill(item) for item in _parse_id_list(entry.get('level_skill_list'))
        ],
        'machine_skill_list': [
            _build_skill(item) for item in _parse_id_list(entry.get('machine_skill_list'))
        ],
        'blood_skill_list': [
            _build_skill(item) for item in _parse_id_list(entry.get('blood_skill_list'))
        ],
        'evolution_list': _build_evolution_list(pet_id),
        'talent_random_list': list(
            TALENT_RANDOM_LIST if str(pet_id) in TONGCHENG_PET_IDS
            else TALENT_RANDOM_LIST_NO_RIDE
        ),
        'breeding': _breeding_map.get(str(pet_id)),
    }


_pet_raw_by_id = {str(item['pet_id']): item for item in _pet_raw if item.get('pet_id')}

pet_list = {pet_id: _build_pet(entry) for pet_id, entry in _pet_raw_by_id.items()}

# 精灵 id -> 精灵名
name_id_list = {pet_id: item['name'] for pet_id, item in pet_list.items()}


def _unknown_pet(pet_id):
    return {
        'id': pet_id,
        'name': f'未知精灵({pet_id})',
        'form': '',
        'icon': '',
        'shiny_icon': '',
        'description': '',
        'weight_low': 0,
        'weight_high': 0,
        'height_low': 0,
        'height_high': 0,
        'unit_type': ['无'],
        'unit_type_list': [23],
        'attribute': {
            'attr_hp': 0, 'attr_atk': 0, 'attr_spatk': 0,
            'attr_def': 0, 'attr_spdef': 0, 'attr_spd': 0,
        },
        'feature': {'id': 0, 'name': '', 'desc': ''},
        'egg_group': [],
        'level_skill_list': [],
        'machine_skill_list': [],
        'blood_skill_list': [],
        'evolution_list': [],
        'talent_random_list': list(TALENT_RANDOM_LIST_NO_RIDE),
        'breeding': None,
    }


class Roster:
    def __init__(self):
        self._roster = pygtrie.CharTrie()
        self._all_name_list = []
        self.update()

    def update(self):
        self._roster.clear()
        for idx, item in pet_list.items():
            from_name = item.get('form', '')
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
    return _build_skill(int(skillid)) if str(skillid).isdigit() else _build_skill(skillid)


async def get_pet_info(petid):
    return pet_list.get(str(petid)) or _unknown_pet(petid)


def get_pet_name(petid):
    """精灵 id -> 精灵名，未收录时返回 None。"""
    item = pet_list.get(str(petid))
    if item is None:
        return None
    return item.get('name') or None
