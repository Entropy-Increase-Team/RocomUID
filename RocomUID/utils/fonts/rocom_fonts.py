from pathlib import Path

from PIL import ImageFont

FONT_ORIGIN_PATH = Path(__file__).parent / "rocom_origin.ttf"
SKILL_FONT_ORIGIN_PATH = Path(__file__).parent / "skill_origin.ttf"

def rocom_font_origin(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_ORIGIN_PATH), size=size)

def skill_font_origin(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(SKILL_FONT_ORIGIN_PATH), size=size)

rc_font_12 = rocom_font_origin(12)
rc_font_14 = rocom_font_origin(14)
rc_font_15 = rocom_font_origin(15)
rc_font_18 = rocom_font_origin(18)
rc_font_20 = rocom_font_origin(20)
rc_font_22 = rocom_font_origin(22)
rc_font_23 = rocom_font_origin(23)
rc_font_24 = rocom_font_origin(24)
rc_font_25 = rocom_font_origin(25)
rc_font_26 = rocom_font_origin(26)
rc_font_28 = rocom_font_origin(28)
rc_font_30 = rocom_font_origin(30)
rc_font_32 = rocom_font_origin(32)
rc_font_34 = rocom_font_origin(34)
rc_font_36 = rocom_font_origin(36)
rc_font_38 = rocom_font_origin(38)
rc_font_40 = rocom_font_origin(40)
rc_font_42 = rocom_font_origin(42)
rc_font_44 = rocom_font_origin(44)
rc_font_50 = rocom_font_origin(50)
rc_font_58 = rocom_font_origin(58)
rc_font_60 = rocom_font_origin(60)
rc_font_62 = rocom_font_origin(62)
rc_font_64 = rocom_font_origin(64)
rc_font_70 = rocom_font_origin(70)
rc_font_72 = rocom_font_origin(72)
rc_font_84 = rocom_font_origin(84)

skill_font_20 = skill_font_origin(20)
skill_font_22 = skill_font_origin(22)
skill_font_24 = skill_font_origin(24)
skill_font_26 = skill_font_origin(26)