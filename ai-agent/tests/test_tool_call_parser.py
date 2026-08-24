import pytest
import json
from unittest.mock import MagicMock, patch
from app.agent import _extract_text_tool_calls, _sanitize_response_text, run_agent_loop
from app.schemas import AskResponse

def test_extract_xml_pseudo_tags_from_screenshot():
    raw_text = """
<tool_call>
<function=get_db_schema>
<parameter=table_name>
zones
<parameter/>
<function/>
<tool_call/>
"""
    calls = _extract_text_tool_calls(raw_text)
    assert len(calls) == 1
    assert calls[0]["name"] == "get_db_schema"
    assert calls[0]["arguments"] == {"table_name": "zones"}

def test_extract_xml_with_standard_closing_tags():
    raw_text = """
<tool_call>
<function=run_read_only_query>
<parameter=sql_query>
SELECT * FROM departments WHERE active_flag = 1
</parameter>
</function>
</tool_call>
"""
    calls = _extract_text_tool_calls(raw_text)
    assert len(calls) == 1
    assert calls[0]["name"] == "run_read_only_query"
    assert calls[0]["arguments"] == {"sql_query": "SELECT * FROM departments WHERE active_flag = 1"}

def test_extract_xml_named_attribute_style():
    raw_text = """
<tool_call>
<function name="list_incidents">
<parameter name="status">OPEN</parameter>
<parameter name="limit">5</parameter>
</function>
</tool_call>
"""
    calls = _extract_text_tool_calls(raw_text)
    assert len(calls) == 1
    assert calls[0]["name"] == "list_incidents"
    assert calls[0]["arguments"] == {"status": "OPEN", "limit": 5}

def test_extract_json_in_tool_call():
    raw_text = """
<tool_call>
{"name": "get_employee_info", "arguments": {"query": "Ahmed"}}
</tool_call>
"""
    calls = _extract_text_tool_calls(raw_text)
    assert len(calls) == 1
    assert calls[0]["name"] == "get_employee_info"
    assert calls[0]["arguments"] == {"query": "Ahmed"}

def test_extract_markdown_code_block_tool_call():
    raw_text = """```tool_call
{"name": "list_chemicals", "arguments": {"limit": 10}}
```"""
    calls = _extract_text_tool_calls(raw_text)
    assert len(calls) == 1
    assert calls[0]["name"] == "list_chemicals"
    assert calls[0]["arguments"] == {"limit": 10}

def test_sanitize_response_text_all_tags():
    raw = """
<think>
Evaluating user query for zones schema.
</think>
<tool_call>
<function=get_db_schema>
<parameter=table_name>
zones
<parameter/>
<function/>
<tool_call/>
Here is the final summary:
- Zone A: Production
- Zone B: Warehouse
"""
    clean = _sanitize_response_text(raw)
    assert "<think>" not in clean
    assert "<tool_call>" not in clean
    assert "<function" not in clean
    assert "<parameter" not in clean
    assert "Here is the final summary:" in clean
    assert "- Zone A: Production" in clean

def test_sanitize_pure_tool_call_returns_empty():
    raw = """<tool_call><function=get_db_schema><parameter=table_name>zones<parameter/><function/><tool_call/>"""
    clean = _sanitize_response_text(raw)
    assert clean == ""

def test_run_agent_loop_with_xml_tool_call():
    # Mock db session
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = [
        ("zone_id", "varchar(50)", "NO", "PRI"),
        ("zone_name_ar", "varchar(100)", "YES", ""),
    ]

    # Turn 0: Model returns XML tool call for get_db_schema
    msg_0 = MagicMock()
    msg_0.tool_calls = None
    msg_0.content = """<tool_call>
<function=get_db_schema>
<parameter=table_name>
zones
<parameter/>
<function/>
<tool_call/>"""
    res_0 = MagicMock()
    res_0.choices = [MagicMock(message=msg_0)]

    # Turn 1: Model sees tool result and returns final synthesized markdown
    msg_1 = MagicMock()
    msg_1.tool_calls = None
    msg_1.content = "جدول المناطق `zones` يحتوي على الأعمدة: `zone_id` و `zone_name_ar`."
    res_1 = MagicMock()
    res_1.choices = [MagicMock(message=msg_1)]

    with patch("app.agent.chat_completion", side_effect=[(res_0, "Groq (qwen/qwen3.6-27b)"), (res_1, "Groq (qwen/qwen3.6-27b)")]):
        resp = run_agent_loop(
            question="ما هي أعمدة جدول المناطق zones؟",
            db=mock_db,
            session_id="test-xml-session",
            model_mode="groq"
        )
        assert isinstance(resp, AskResponse)
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].tool_name == "get_db_schema"
        assert "<tool_call>" not in resp.answer
        assert "<function" not in resp.answer
        assert "جدول المناطق" in resp.answer
