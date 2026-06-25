from typing import Any, Dict, List, Union

from msgspec import Struct


################
# 用户信息 #
################
class UserAward(Struct):
    nickname: str
    level: int
    avatar: str
    registerDate: str


class BattleInfo(Struct):
    matches: int
    wins: int
    rank: str


class ElvesInfo(Struct):
    totalElves: int
    colorfulElves: int
    shinyElves: int
    amazingElves: int


class CollectionInfo(Struct):
    pokedexCount: int
    costumeCount: int


class UserItemsInfo(Struct):
    elfEgg: int
    elfFruit: int


class UserInfo(Struct):
    basic: UserAward
    battle: BattleInfo
    elves: ElvesInfo
    collection: CollectionInfo
    items: UserItemsInfo


################
# 精灵详细列表 #
################
class PetListDetail(Struct):
    SerialNum: str
    PetBaseId: int
    PetSkillDamType: List[int]
    PetTalentRank: int
    SpiritLevel: int
    PetBlood: int
    PetMutation: int


class PetList(Struct):
    list: List[PetListDetail]
    total: int
    page: int
    pageSize: int
    totalPages: int


################
# 家园信息 #
################
class HomePetInfo(Struct):
    pet_id: int
    name: str
    gender: int
    level: int
    mutation_type: int
    time_cost: int
    pet_rip_time: int
    have_egg: bool
    predicted_egg_time: int = 0
    status: int = 0      # 喂食状态：1700尚未喂食/1701喂养中/1702可收集/1704空闲
    nature: int = 0      # 性格 id
    blood_id: int = 0    # 属性/血脉 id（→ filters bloodList / 出图血脉卡片）


class HomePlantStaticInfo(Struct):
    iconid: Union[int, str]
    name: str


class HomePlantInfo(Struct):
    plant_info: HomePlantStaticInfo
    plant_rip_time: int
    plant_tab_id: int


class HomeInfo(Struct):
    home_name: str
    home_experience: int
    home_level: int
    room_level: int
    home_comfort_level: int
    home_pets: List[HomePetInfo]
    home_plants: List[HomePlantInfo]
    finished_at: Union[int, str]


################
# 精灵面板信息 #
################
class PetAttributeItem(Struct):
    value: int
    talent: int
    effort_add: int


class PetAttributeInfo(Struct):
    pethp: PetAttributeItem
    petatk: PetAttributeItem
    petspatk: PetAttributeItem
    petdef: PetAttributeItem
    petspdef: PetAttributeItem
    petspd: PetAttributeItem


class PetSkillInfo(Struct):
    id: int
    name: str
    iconid: int
    pos: int
    is_equipped: bool
    use_times: int


class PetFeatureInfo(Struct):
    id: int
    name: str
    desc: str


class PetPanelInfo(Struct):
    pet_id: int
    name: str
    level: int
    gender: int
    energy: int
    mutation_type: int
    blood_id: int
    nature: Any
    attribute_info: PetAttributeInfo
    equip_skills: List[PetSkillInfo]
    skills: List[PetSkillInfo]
    feature: PetFeatureInfo
    glass_info: Any


PetInfoMap = Dict[str, PetPanelInfo]
