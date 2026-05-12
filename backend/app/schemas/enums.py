from enum import Enum


class TeachingMode(str, Enum):
    SOCRATIC = "socratic"
    EXPLANATION = "explanation"
    MIXED = "mixed"


class AvatarType(str, Enum):
    EMOJI = "emoji"
    IMAGE = "image"


class BackgroundType(str, Enum):
    COLOR = "color"
    IMAGE = "image"


class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DASHSCOPE = "dashscope"
    ZHIPU = "zhipu"
    DOUBAO = "doubao"
    WENXIN = "wenxin"
    HUNYUAN = "hunyuan"
    MOONSHOT = "moonshot"
    GEMINI = "gemini"
    MINIMAX = "minimax"
    CUSTOM = "custom"