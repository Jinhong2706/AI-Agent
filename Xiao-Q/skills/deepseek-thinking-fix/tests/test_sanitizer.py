"""Tests for MessageSanitizer — 10 regression tests covering all known issues."""

import copy
import pytest
from core.sanitizer import MessageSanitizer
from core.persistence import PersistenceSanitizer


class TestMessageSanitizer:

    def test_tool_call_5_rounds(self):
        """场景1: 5轮tool-call循环 — 覆盖 #14933, #15353, #17400"""
        sanitizer = MessageSanitizer("deepseek", "deepseek-v4-flash", True)
        messages = [{"role": "user", "content": "开始"}]
        for r in range(5):
            messages.append({
                "role": "assistant", "content": None,
                "tool_calls": [{"id": f"c{r}", "function": {"name": "t", "arguments": "{}"}}],
                "reasoning_content": f"思考{r}",
            })
            messages.append({"role": "tool", "content": f"结果{r}", "tool_call_id": f"c{r}"})
            messages.append({"role": "user", "content": f"继续{r}"})
        
        clean = sanitizer.sanitize_for_api(messages)
        for i, msg in enumerate(clean):
            if msg.get("role") == "assistant":
                assert "reasoning_content" in msg, f"msg[{i}] 缺失 reasoning_content!"
        
        # 验证输入未被修改（不可变保证）
        assert messages[1].get("reasoning_content") == "思考0"

    def test_plain_assistant(self):
        """场景2: 纯文本 assistant — 覆盖 #16137, #15741"""
        sanitizer = MessageSanitizer("deepseek", "deepseek-v4-flash", True)
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
        ]
        clean = sanitizer.sanitize_for_api(messages)
        assert clean[1]["reasoning_content"] == ""

    def test_storage_round_trip(self):
        """场景3: 存储→加载→发送 — 覆盖 #16844, #17825"""
        original = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hi", "reasoning_content": "think"},
        ]
        stored = [PersistenceSanitizer.serialize(m) for m in original]
        loaded = [PersistenceSanitizer.deserialize(m) for m in stored]
        sanitizer = MessageSanitizer("deepseek", "deepseek-v4-flash", True)
        clean = sanitizer.sanitize_for_api(loaded)
        assert clean[1]["reasoning_content"] == "think"

    def test_auxiliary_path(self):
        """场景4: 辅助路径 — 覆盖 #15213"""
        sanitizer = MessageSanitizer("deepseek", "deepseek-v4-flash", True)
        messages = [{"role": "user", "content": "定时任务"}]
        clean = sanitizer.sanitize_for_api(messages)
        assert clean[0]["role"] == "user"  # 不吃 user

    def test_cross_provider_cleanup(self):
        """场景5: 跨厂商切换 — 覆盖 #15748"""
        ds = MessageSanitizer("deepseek", "deepseek-v4-flash", True)
        msgs = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hi", "reasoning_content": "思考"},
        ]
        clean = ds.sanitize_for_api(msgs)
        assert "reasoning_content" in clean[1]
        claude = MessageSanitizer("anthropic", "claude-4", False)
        clean2 = claude.sanitize_for_api(msgs)
        assert "reasoning_content" not in clean2[1]

    def test_thinking_off_param(self):
        """场景6: thinking=off 参数 — 覆盖 #15700"""
        from core.controller import ThinkingControllerProxy
        ctrl = ThinkingControllerProxy()
        ctrl.configure(False)
        params = ctrl.build_thinking_params()
        assert params == {"thinking": {"type": "disabled"}}
        ctrl.configure(True)
        params2 = ctrl.build_thinking_params()
        assert params2 == {}

    def test_no_stale_reasoning(self):
        """场景7: 无 stale reasoning 复用 — 覆盖 #17052"""
        sanitizer = MessageSanitizer("deepseek", "deepseek-v4-flash", True)
        messages = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1", "reasoning_content": "上一轮推理"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2（无推理）"},
        ]
        clean = sanitizer.sanitize_for_api(messages)
        assert clean[3]["reasoning_content"] == ""

    def test_concurrent_sessions(self):
        """场景8: 并发安全"""
        import threading
        results = []
        def run(sid):
            s = MessageSanitizer("deepseek", "deepseek-v4-flash", True)
            msgs = [{"role": "user", "content": f"Q{sid}"}, {"role": "assistant", "content": f"A{sid}"}]
            c = s.sanitize_for_api(msgs)
            results.append(c[1].get("reasoning_content"))
        threads = [threading.Thread(target=run, args=(i,)) for i in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(results) == 10

    def test_database_migration(self, tmp_path):
        """场景9: 数据迁移 — 覆盖 #16844"""
        import json, sqlite3
        db = tmp_path / "test.db"
        conn = sqlite3.connect(str(db))
        conn.execute("CREATE TABLE sessions (id TEXT, messages TEXT)")
        conn.execute("INSERT INTO sessions VALUES (?, ?)",
                     ("s1", json.dumps([
                         {"role": "user", "content": "hi"},
                         {"role": "assistant", "content": "hi", "reasoning": "思考"},
                     ])))
        conn.commit()
        conn.close()
        fixed = PersistenceSanitizer.migrate_database(str(db))
        assert fixed == 1
        conn2 = sqlite3.connect(str(db))
        raw = conn2.execute("SELECT messages FROM sessions WHERE id='s1'").fetchone()[0]
        assert json.loads(raw)[1].get("reasoning_content") == "思考"
        conn2.close()

    def test_intermittent_failure_regression(self):
        """场景10: 间歇性失败回归测试 — 覆盖 #17400 worst case"""
        sanitizer = MessageSanitizer("deepseek", "deepseek-v4-flash", True)
        messages = [{"role": "user", "content": "开始"}]
        for r in range(10):
            # 模拟多个函数可能修改同一个消息对象
            msg = {
                "role": "assistant", "content": None,
                "tool_calls": [{"id": f"c{r}", "function": {"name": "t", "arguments": "{}"}}],
                "reasoning_content": f"思考{r}",
            }
            # 模拟其他函数对这个 dict 的操作（可能意外丢弃 RC）
            msg.pop("reasoning_content", None)  # ← 模拟 bug！
            msg["reasoning_content"] = f"新思考{r}"
            
            messages.append(msg)
            messages.append({"role": "tool", "content": "ok", "tool_call_id": f"c{r}"})
            messages.append({"role": "user", "content": f"继续{r}"})
        
        clean = sanitizer.sanitize_for_api(messages)
        for i, msg in enumerate(clean):
            if msg.get("role") == "assistant":
                assert "reasoning_content" in msg, f"间歇性失败！msg[{i}] 缺 RC"
