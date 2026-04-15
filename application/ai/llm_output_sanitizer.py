"""LLM 原始输出净化与节拍续写辅助。"""

from __future__ import annotations

import re


_THINK_BLOCK_RE = re.compile(r"<think\b[^>]*>.*?</think>", re.IGNORECASE | re.DOTALL)
_OPEN_THINK_SUFFIX_RE = re.compile(r"<think\b[^>]*>.*$", re.IGNORECASE | re.DOTALL)
_EXCESS_BLANK_LINES_RE = re.compile(r"\n{3,}")


def sanitize_llm_output(text: str) -> str:
    """移除模型泄露的思考块，并压缩多余空行。"""
    if not text:
        return ""

    cleaned = text.replace("\r\n", "\n")
    cleaned = _THINK_BLOCK_RE.sub("", cleaned)
    cleaned = _OPEN_THINK_SUFFIX_RE.sub("", cleaned)
    cleaned = cleaned.replace("<think>", "").replace("</think>", "")
    cleaned = _EXCESS_BLANK_LINES_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def build_continuation_excerpt(content: str, max_chars: int = 220) -> str:
    """截取上一节拍末尾，供下一节拍续写承接。"""
    cleaned = sanitize_llm_output(content)
    if not cleaned:
        return ""
    return cleaned[-max_chars:].lstrip()


def extract_visible_delta(raw_content: str, emitted_content: str) -> tuple[str, str]:
    """从原始流式内容中提取当前应展示的新文本。"""
    visible_content = sanitize_llm_output(raw_content)

    if not visible_content:
        return visible_content, ""
    if emitted_content and visible_content.startswith(emitted_content):
        return visible_content, visible_content[len(emitted_content):]
    if visible_content == emitted_content:
        return visible_content, ""
    return visible_content, visible_content
