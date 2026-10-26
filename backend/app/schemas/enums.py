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
    QUALITY_CHECK = "quality_check"
    PENDING_REVIEW = "pending_review"
    READY = "ready"
    FAILED = "failed"
    REVIEW_REJECTED = "review_rejected"


class QualityCheckErrorCode(str, Enum):
    EMPTY_OUTLINE = "EMPTY_OUTLINE"
    NO_MODULES = "NO_MODULES"
    INVALID_MODULE = "INVALID_MODULE"
    MISSING_KP_ID = "MISSING_KP_ID"
    MISSING_KP_NAME = "MISSING_KP_NAME"
    NO_KNOWLEDGE_POINTS = "NO_KNOWLEDGE_POINTS"
    DUPLICATE_KP_ID = "DUPLICATE_KP_ID"
    UNDECLARED_PREREQUISITE = "UNDECLARED_PREREQUISITE"
    SELF_PREREQUISITE = "SELF_PREREQUISITE"
    CYCLIC_PREREQUISITE = "CYCLIC_PREREQUISITE"
    INVALID_PREREQUISITE_TYPE = "INVALID_PREREQUISITE_TYPE"


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