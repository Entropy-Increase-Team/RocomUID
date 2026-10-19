import json
from typing import Any, Dict, List, Type, TypeVar, Optional, Union
from sqlmodel import Field, col, select
from gsuid_core.utils.database.base_models import (
    Bind,
    User,
    BaseIDModel,
    BaseModel,
    with_session,
)
from gsuid_core.utils.database.startup import exec_list

T_RocomUser = TypeVar("T_RocomUser", bound="RocomUser")

UID_MIN_LENGTH = 6
HOME_UID_MAX_COUNT = 19

ROCOM_USER_MIGRATIONS = [
    'ALTER TABLE RocomUser ADD COLUMN framework_token TEXT DEFAULT ""',
    'ALTER TABLE RocomUser ADD COLUMN binding_id TEXT DEFAULT ""',
    'ALTER TABLE RocomUser ADD COLUMN bind_time INT DEFAULT 0',
    'ALTER TABLE RocomUser ADD COLUMN login_type TEXT DEFAULT ""',
    'ALTER TABLE RocomUser ADD COLUMN home_uids TEXT DEFAULT "[]"',
]

for migration_sql in ROCOM_USER_MIGRATIONS:
    if migration_sql not in exec_list:
        exec_list.append(migration_sql)


class RocomUser(User, table=True):
    __table_args__ = {"extend_existing": True}

    user_id: str = Field(default="", title="用户ID")
    bot_id: str = Field(default="", title="机器人ID")
    uid: str = Field(default="", title="洛克王国账号ID")
    home_uids: str = Field(default="[]", title="家园UID列表")
    cookie: str = Field(default="", title="Cookie")
    framework_token: str = Field(default="", title="framework_token")
    binding_id: str = Field(default="", title="binding_id")
    bind_time: int = Field(default=0, title="bind_time")
    login_type: str = Field(default="", title="login_type")

    @classmethod
    async def insert_rocom_uid(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
        uid: str,
    ) -> int:
        if not uid or not uid.isdigit() or len(uid) < UID_MIN_LENGTH:
            return -1

        result = await cls.select_data(user_id, bot_id)
        home_uids = cls._load_home_uids(result.home_uids if result else "[]")
        bind_uid = result.uid if result and result.uid else ''

        if not bind_uid:
            if uid in home_uids:
                promoted_home_uids = [
                    None if home_uid == uid else home_uid for home_uid in home_uids
                ]
                await cls.update_data(
                    user_id=user_id,
                    bot_id=bot_id,
                    **{
                        "uid": uid,
                        "home_uids": json.dumps(promoted_home_uids, ensure_ascii=False),
                    },
                )
                return 1
            if not result:
                return await cls.insert_data(
                    user_id=user_id,
                    bot_id=bot_id,
                    **{"uid": uid},
                )
            await cls.update_data(
                user_id=user_id,
                bot_id=bot_id,
                **{"uid": uid},
            )
            return 0

        if uid == bind_uid or uid in home_uids:
            return -2

        insert_index = -1
        for index in range(HOME_UID_MAX_COUNT):
            if index >= len(home_uids):
                home_uids.append(None)
            if home_uids[index] is None and insert_index == -1:
                insert_index = index

        if insert_index == -1:
            return -3

        home_uids[insert_index] = uid
        await cls.update_data(
            user_id=user_id,
            bot_id=bot_id,
            **{"home_uids": json.dumps(home_uids, ensure_ascii=False)},
        )
        return insert_index + 2
    
    @classmethod
    async def insert_rocom_uid_qr(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
        binding: str,
    ) -> int:
        uid = binding.get('uid')
        framework_token = binding.get('framework_token')
        binding_id = binding.get('binding_id')
        bind_time = binding.get('bind_time')
        login_type = binding.get('login_type')
        # 第一次绑定
        if not await cls.select_data(user_id, bot_id):
            code = await cls.insert_data(
                user_id=user_id,
                bot_id=bot_id,
                **{"uid": uid, "framework_token": framework_token, "binding_id": binding_id, "bind_time": bind_time, "login_type":login_type},
            )
            return code
        await cls.update_data(
            user_id=user_id,
            bot_id=bot_id,
            **{"uid": uid, "framework_token": framework_token, "binding_id": binding_id, "bind_time": bind_time, "login_type":login_type},
        )
        return True
        
    @classmethod
    async def update_rocom_token(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
        token: str,
    ) -> Union[str, int]:
        res = await cls.update_data(
            user_id=user_id,
            bot_id=bot_id,
            **{"cookie": token},
        )
        return res
        
    
    @classmethod
    async def update_rocom_stoken(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
        account_type: str,
    ) -> Union[str, int]:
        res = await cls.update_data(
            user_id=user_id,
            bot_id=bot_id,
            **{"stoken": account_type},
        )
        return res
    
    @classmethod
    async def select_rocom_fw_token(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
    ) -> Union[str, int]:
        result = await cls.select_data(user_id, bot_id)
        fw_token = result.framework_token if result and result.framework_token else None
        return fw_token
    
    @classmethod
    async def select_rocom_user(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
    ) -> Union[str, int]:
        result = await cls.select_data(user_id, bot_id)
        bind_uid = result.uid if result and result.uid else None
        return bind_uid

    @staticmethod
    def _load_home_uids(home_uids: str) -> List[Optional[str]]:
        try:
            data = json.loads(home_uids or "[]")
        except (json.JSONDecodeError, TypeError):
            data = []
        if not isinstance(data, list):
            data = []
        uid_list: List[Optional[str]] = []
        for item in data[:HOME_UID_MAX_COUNT]:
            if item is None:
                uid_list.append(None)
                continue
            uid = str(item).strip()
            uid_list.append(
                uid if uid.isdigit() and len(uid) >= UID_MIN_LENGTH else None
            )
        return uid_list

    @classmethod
    async def select_home_uids(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
    ) -> List[Optional[str]]:
        result = await cls.select_data(user_id, bot_id)
        return cls._load_home_uids(result.home_uids if result else "[]")

    @classmethod
    async def select_all_bound_uids(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
    ) -> List[str]:
        """默认 UID + 全部家园 UID（去重、保序）。"""
        result = await cls.select_data(user_id, bot_id)
        if not result:
            return []
        bind_uid = str(result.uid or '').strip()
        all_uids = [bind_uid, *cls._load_home_uids(result.home_uids)]
        return list(dict.fromkeys(
            str(uid).strip() for uid in all_uids if uid
        ))

    @classmethod
    async def delete_rocom_uid(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
        uid: str = "",
    ) -> int:
        """删除 UID"""
        if uid and (not uid.isdigit() or len(uid) < UID_MIN_LENGTH):
            return -1

        result = await cls.select_data(user_id, bot_id)
        if not result:
            return -3

        bind_uid = str(result.uid or '').strip()
        if not uid or uid == bind_uid:
            if not bind_uid:
                return -3
            await cls.update_data(
                user_id=user_id,
                bot_id=bot_id,
                **{"uid": ""},
            )
            return 0

        home_uids = cls._load_home_uids(result.home_uids)
        if uid not in home_uids:
            return -3

        index = home_uids.index(uid)
        home_uids[index] = None
        await cls.update_data(
            user_id=user_id,
            bot_id=bot_id,
            **{"home_uids": json.dumps(home_uids, ensure_ascii=False)},
        )
        return index + 2
    
    @classmethod
    async def get_rocom_token(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
    ) -> Union[str, int]:
        token = await cls.get_user_cookie_by_user_id(user_id, bot_id)
        stoken = await cls.get_user_stoken_by_user_id(user_id, bot_id)
        if stoken is None:
            stoken = 'qq'
        return token, stoken
