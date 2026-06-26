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
    "RC_merchant_render_style": GsStrConfig(
        "远行商人渲染样式",
        "用于选择远行商人图片渲染样式",
        "简约",
        options=[
            "简约",
            "大字版",
            "远区商人",
        ],
    ),
    "RC_egg_render_style": GsStrConfig(
        "查蛋渲染样式",
        "选择查蛋结果以图片或文字呈现",
        "图片版",
        options=[
            "图片版",
            "文字版",
        ],
    ),
    "RC_garden_render_style": GsStrConfig(
        "家园/菜园渲染样式",
        "选择家园/菜园信息渲染模板：新版 或 旧版",
        "新版",
        options=[
            "新版",
            "旧版",
        ],
    ),
    "RC_home_use_qq_avatar": GsBoolConfig(
        "家园信息使用用户头像",
        "开启后家园信息头像使用查询者头像；关闭后固定使用默认头像",
        False,
    ),
    "RC_home_separate_garden": GsBoolConfig(
        "家园隐藏菜园显示",
        "开启后家园命令只显示精灵信息；关闭后家园命令精灵和菜园一起显示",
        False,
    ),
    "RC_home_cache_enable": GsBoolConfig(
        "家园信息缓存开关",
        "开启后家园信息会优先读取本地缓存，缓存超时后重新请求API；关闭后每次查询都请求API",
        False,
    ),
    "RC_home_cache_minutes": GsStrConfig(
        "家园信息缓存时间（分钟）",
        "家园信息本地缓存有效时间，超过该时间后重新请求API",
        "5",
    ),
}
