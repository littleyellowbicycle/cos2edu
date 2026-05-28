from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class ParseErrorCode(str, Enum):
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FORMAT_UNSUPPORTED = "FORMAT_UNSUPPORTED"
    MAGIC_MISMATCH = "MAGIC_MISMATCH"
    PDF_ENCRYPTED = "PDF_ENCRYPTED"
    PDF_SCANNED = "PDF_SCANNED"
    PDF_CORRUPTED = "PDF_CORRUPTED"
    DOC_OLD_FORMAT = "DOC_OLD_FORMAT"
    FILE_EMPTY = "FILE_EMPTY"
    ENCODING_FAILED = "ENCODING_FAILED"
    TEXT_TOO_SHORT = "TEXT_TOO_SHORT"
    PARSE_TIMEOUT = "PARSE_TIMEOUT"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class ParseResult:
    success: bool
    text: str = ""
    page_count: int = 0
    char_count: int = 0
    format: str = ""
    encoding: str = "utf-8"
    error_code: Optional[str] = None
    error_message: str = ""
    suggestion: str = ""


class BaseParser(ABC):
    supported_extensions: list[str] = []
    supported_mime_types: list[str] = []

    @abstractmethod
    async def parse(self, file_path: str) -> ParseResult:
        pass

    def can_parse(self, extension: str, mime_type: str = "") -> bool:
        if extension.lower() in self.supported_extensions:
            return True
        if mime_type and mime_type in self.supported_mime_types:
            return True
        return False