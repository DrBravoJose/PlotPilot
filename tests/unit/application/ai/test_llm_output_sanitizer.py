from application.ai.llm_output_sanitizer import (
    build_continuation_excerpt,
    sanitize_llm_output,
)


def test_sanitize_llm_output_removes_complete_think_block():
    raw = "<think>先分析要求</think>\n正文第一句。"

    assert sanitize_llm_output(raw) == "正文第一句。"


def test_sanitize_llm_output_drops_unclosed_think_suffix():
    raw = "正文第一句。\n<think>还在分析"

    assert sanitize_llm_output(raw) == "正文第一句。"


def test_build_continuation_excerpt_keeps_tail_only():
    content = "甲" * 50 + "掏出来一看，是一条来自未知号码的短信，只有一行字："

    excerpt = build_continuation_excerpt(content, max_chars=20)

    assert excerpt.endswith("只有一行字：")
    assert len(excerpt) <= 20
