from typing import Any, Dict, List, Type, TypeVar, Optional, Union
from sqlmodel import Field, col, select
from gsuid_core.utils.database.base_models import (
    Bind,
    User,
    BaseIDModel,
    BaseModel,
    with_session,
)

T_RocomUser = TypeVar("T_RocomUser", bound="RocomUser")

class RocomUser(User, table=True):
    user_id: str = Field(default="", title="用户ID")
    bot_id: str = Field(default="", title="机器人ID")
    uid: str = Field(default="", title="洛克王国账号ID")
    cookie: str = Field(default="", title="Cookie")
    token: str = Field(default="", title="token")
    openid: str = Field(default="", title="openid")
    
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
    async def update_rocom_token(
        cls: Type[T_RocomUser],
        user_id: str,
        bot_id: str,
        token: str,
        openid: str,
    ) -> Union[str, int]:
        res = await cls.update_data(
            user_id=user_id,
            bot_id=bot_id,
            **{"token": token, "openid": openid},
        )
        return res
    
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
        result = await cls.select_data(user_id, bot_id)
        token = result.token if result and result.token else None
        openid = result.openid if result and result.openid else None
        return token, openid