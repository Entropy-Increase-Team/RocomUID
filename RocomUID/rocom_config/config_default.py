from typing import Dict

from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsStrConfig,
    GsBoolConfig,
    GsListStrConfig,
)

CONFIG_DEFAULT: Dict[str, GSC] = {
    "RCPrefix": GsStrConfig(
        "插件命令前缀（确认无冲突再修改）",
        "用于设置RocomUID前缀的配置",
        "rc",
    ),
    "RC_wegame_key": GsStrConfig(
        "wegame后台数据key",
        "使用wegame获取数据的key",
        "",
    ),
    "RC_merchant_cd": GsStrConfig(
        "远行商人推送伦查间隔（s）",
        "远行商人推送未获取到信息时再次查询间隔时间",
        "30",
        options=[
            "10",
            "20",
            "30",
            "40",
            "50",
            "60",
            "70",
            "80",
            "90",
        ],
    ),
    "RC_home_use_qq_avatar": GsBoolConfig(
        "家园信息使用QQ头像",
        "开启后家园信息头像使用查询者QQ头像；关闭后固定使用默认头像",
        False,
    ),
}
