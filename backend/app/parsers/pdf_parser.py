import os
from typing import Optional
from app.parsers.base import BaseParser, ParseResult, ParseErrorCode


class PDFParser(BaseParser):
    supported_extensions = [".pdf"]
    supported_mime_types = ["application/pdf"]

    async def parse(self, file_path: str) -> ParseResult:
        if not os.path.exists(file_path):
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.PDF_CORRUPTED,
                error_message=f"文件不存在: {file_path}",
            )

        try:
            import pdfplumber
        except ImportError:
            return await self._parse_with_pypdf(file_path)

        try:
            text_parts = []
            page_count = 0
            image_page_count = 0

            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_parts.append(page_text)
                    else:
                        image_page_count += 1

            content = "\n\n".join(text_parts)
            char_count = len(content)

            if page_count > 0 and image_page_count / page_count > 0.8:
                return ParseResult(
                    success=False,
                    error_code=ParseErrorCode.PDF_SCANNED,
                    error_message="此PDF为扫描件，需要OCR支持才能提取文字",
                    suggestion="请提供文字版PDF，或使用OCR工具处理后重新上传",
                    page_count=page_count,
                )

            if char_count < 500 and page_count > 0:
                return ParseResult(
                    success=False,
                    error_code=ParseErrorCode.TEXT_TOO_SHORT,
                    error_message=f"仅提取到{char_count}字，可能为图片文档",
                    suggestion="请确认PDF包含可选择的文字内容",
                    page_count=page_count,
                    char_count=char_count,
                )

            return ParseResult(
                success=True,
                text=content,
                page_count=page_count,
                char_count=char_count,
                format="pdf",
            )

        except Exception as e:
            error_str = str(e).lower()
            if "encrypted" in error_str or "password" in error_str:
                return ParseResult(
                    success=False,
                    error_code=ParseErrorCode.PDF_ENCRYPTED,
                    error_message="PDF已加密，无法提取文本内容",
                    suggestion="请使用 Adobe Acrobat 或在线工具移除密码保护",
                )
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.PDF_CORRUPTED,
                error_message=f"PDF解析失败: {str(e)}",
                suggestion="请尝试重新导出PDF文件",
            )

    async def _parse_with_pypdf(self, file_path: str) -> ParseResult:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            page_count = len(reader.pages)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            content = "\n\n".join(text_parts)
            return ParseResult(
                success=True,
                text=content,
                page_count=page_count,
                char_count=len(content),
                format="pdf",
            )
        except Exception as e:
            return ParseResult(
                success=False,
                error_code=ParseErrorCode.PDF_CORRUPTED,
                error_message=f"PDF解析失败: {str(e)}",
            )