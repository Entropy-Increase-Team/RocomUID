from typing import Any, Dict, List, Optional, Union

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
    PetSkillDamType: Any
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