import os
import chardet
from app.parsers.base import BaseParser, ParseResult, ParseErrorCode


class TextParser(BaseParser):
    supported_extensions = [".txt", ".md", ".markdown"]
    supported_mime_types = ["text/plain", "text/markdown"]

    async def parse(self, file_path: str) -> ParseResult:
        if not os.path.exists(file_path):
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.UNKNOWN_ERROR,
                error_message=f"文件不存在: {file_path}",
            )

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.FILE_EMPTY,
                error_message="文件内容为空",
            )

        encoding = await self._detect_encoding(file_path)
        if not encoding:
            encoding = "utf-8"

        try:
            content = self._read_with_fallback(file_path, encoding)
        except Exception as e:
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.ENCODING_FAILED,
                error_message=f"无法识别文件编码: {str(e)}",
                suggestion="请将文件保存为 UTF-8 编码后重新上传",
            )

        char_count = len(content)
        if char_count < 50:
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.TEXT_TOO_SHORT,
                error_message=f"文件内容过少（仅{char_count}字）",
                suggestion="请上传包含更多内容的文件",
                char_count=char_count,
            )

        ext = os.path.splitext(file_path)[1].lower()
        fmt = "markdown" if ext in (".md", ".markdown") else "text"

        front_matter = self._extract_front_matter(content, fmt)

        return ParseResult(
            success=True,
            text=content,
            page_count=1,
            char_count=char_count,
            format=fmt,
            encoding=encoding,
        )

    async def _detect_encoding(self, file_path: str) -> str | None:
        try:
            with open(file_path, "rb") as f:
                raw = f.read(10240)
            result = chardet.detect(raw)
            confidence = result.get("confidence", 0)
            encoding = result.get("encoding")
            if confidence > 0.7 and encoding:
                return encoding
            return None
        except Exception:
            return None

    def _read_with_fallback(self, file_path: str, encoding: str) -> str:
        encodings_to_try = [encoding, "utf-8", "gbk", "gb2312", "gb18030", "latin-1"]
        seen = set()
        for enc in encodings_to_try:
            if enc in seen:
                continue
            seen.add(enc)
            try:
                with open(file_path, "r", encoding=enc, errors="strict") as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _extract_front_matter(self, content: str, fmt: str) -> dict | None:
        if fmt != "markdown":
            return None
        if not content.startswith("---"):
            return None
        end = content.find("---", 3)
        if end == -1:
            return None
        try:
            import yaml
            yaml_str = content[3:end].strip()
            return yaml.safe_load(yaml_str)
        except Exception:
            return None