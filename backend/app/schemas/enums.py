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


class MaterialStatus(str, Enum):
    UPLOADING = "uploading"
    PARSING = "parsing"
    PARSED = "parsed"
    INDEXING = "indexing"
    INDEXED = "indexed"
    OUTLINING = "outlining"
    PENDING_REVIEW = "pending_review"
    READY = "ready"
    FAILED = "failed"


class KnowledgePointStatus(str, Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    LEARNING = "learning"
    MASTERED = "mastered"


class EventType(str, Enum):
    TIME_BASED = "time_based"
    CONDITION_BASED = "condition_based"
    RANDOM = "random"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"