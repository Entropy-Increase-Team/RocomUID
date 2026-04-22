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

class RocomUser(User, table=True):
    user_id: str = Field(default="", title="用户ID")
    bot_id: str = Field(default="", title="机器人ID")
    uid: str = Field(default="", title="洛克王国账号ID")
    cookie: str = Field(default="", title="Cookie")
    framework_token: str = Field(default="", title="framework_token")
    binding_id: str = Field(default="", title="binding_id")
    bind_time: int = Field(default=0, title="bind_time")
    login_type: str = Field(default="", title="login_type")
    
    exec_list.extend(
        [
            'ALTER TABLE RocomUser ADD COLUMN framework_token TEXT DEFAULT ""',
            'ALTER TABLE RocomUser ADD COLUMN binding_id TEXT DEFAULT ""',
            'ALTER TABLE RocomUser ADD COLUMN bind_time INT DEFAULT 0',
            'ALTER TABLE RocomUser ADD COLUMN login_type TEXT DEFAULT ""',
        ]
    )
    
    @classmethod
    async def insert_rocom_uid(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
        uid: str,
    ) -> int:
        if not uid:
            return -1

        # 第一次绑定
        if not await cls.select_data(user_id, bot_id):
            code = await cls.insert_data(
                user_id=user_id,
                bot_id=bot_id,
                **{"uid": uid},
            )
            return code

        result = await cls.select_data(user_id, bot_id)

        bind_uid = result.uid if result and result.uid else ''
        
        # 已经绑定了该UID
        res = 0 if uid != bind_uid else -2

        # 强制更新库表
        force_update = False
        if uid != bind_uid:
            force_update = True

        if force_update:
            await cls.update_data(
                user_id=user_id,
                bot_id=bot_id,
                **{"uid": uid},
            )
        return res
    
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