import os
from typing import Optional
from app.parsers.base import BaseParser, ParseResult, ParseErrorCode
from app.parsers.pdf_parser import PDFParser
from app.parsers.docx_parser import DocxParser
from app.parsers.text_parser import TextParser
from app.core.logging_config import get_logger

logger = get_logger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class ParserRegistry:
    EXTENSION_MAP = {
        ".pdf": PDFParser,
        ".docx": DocxParser,
        ".txt": TextParser,
        ".md": TextParser,
        ".markdown": TextParser,
    }

    MIME_MAP = {
        "application/pdf": PDFParser,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser,
        "text/plain": TextParser,
        "text/markdown": TextParser,
    }

    MAGIC_NUMBERS = {
        b"%PDF": ".pdf",
        b"PK\x03\x04": ".docx",
    }

    def __init__(self):
        self._parsers = {}
        for ext, parser_cls in self.EXTENSION_MAP.items():
            self._parsers[ext] = parser_cls()

    def _detect_extension_by_magic(self, file_path: str) -> Optional[str]:
        try:
            with open(file_path, "rb") as f:
                header = f.read(8)
            for magic, ext in self.MAGIC_NUMBERS.items():
                if header.startswith(magic):
                    return ext
        except Exception:
            pass
        return None

    async def parse(self, file_path: str) -> ParseResult:
        if not os.path.exists(file_path):
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.UNKNOWN_ERROR,
                error_message=f"文件不存在: {file_path}",
            )

        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.FILE_TOO_LARGE,
                error_message=f"文件大小({file_size // 1024 // 1024}MB)超过50MB限制",
                suggestion="请压缩文件或拆分后重新上传",
            )

        ext = os.path.splitext(file_path)[1].lower()

        magic_ext = self._detect_extension_by_magic(file_path)
        if magic_ext and magic_ext != ext:
            logger.warning(f"Extension mismatch: file extension is {ext}, but magic number suggests {magic_ext}")
            ext = magic_ext

        parser = self._parsers.get(ext)
        if not parser:
            supported = ", ".join(sorted(self.EXTENSION_MAP.keys()))
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.FORMAT_UNSUPPORTED,
                error_message=f"不支持的文件格式: {ext}",
                suggestion=f"支持的格式: {supported}",
            )

        return await parser.parse(file_path)


parser_registry = ParserRegistry()