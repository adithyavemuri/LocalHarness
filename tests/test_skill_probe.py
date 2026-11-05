"""Regression checks for the pinned runtime's required-tool API contract."""
import unittest
from unittest.mock import patch

from examples import smoke_test_skills
from local_skills import read_skill


class SkillProbeTests(unittest.TestCase):
    def test_required_mode_uses_supported_string_and_returns_actual_skill_text(self):
        requests = []

        def completion(base, body, timeout):
            requests.append(body["tool_choice"])
            if len(requests) == 1:
                self.assertEqual(body["tool_choice"], "required")
                return {"role": "assistant", "tool_calls": [{"id": "skill-1", "type": "function",
                        "function": {"name": "read_skill",
                                     "arguments": '{"name":"karpathy-guidelines"}'}}]}
            self.assertEqual(body["messages"][-1], {
                "role": "tool", "tool_call_id": "skill-1", "content": read_skill("karpathy-guidelines")})
            return {"role": "assistant", "content": "Define observable success criteria."}

        with patch.object(smoke_test_skills, "completion", side_effect=completion):
            result = smoke_test_skills.probe("http://127.0.0.1:8080/v1", "local", "forced", 10)
        self.assertTrue(result["pass"])
        self.assertEqual(requests, ["required", "none"])

    def test_prose_claiming_skill_use_does_not_pass_a_tool_probe(self):
        with patch.object(smoke_test_skills, "completion", return_value={
            "role": "assistant", "content": "I read the skill."}), self.assertRaisesRegex(
                ValueError, "Expected one read_skill call"):
            smoke_test_skills.probe("http://127.0.0.1:8080/v1", "local", "auto", 10)


if __name__ == "__main__":
    unittest.main()
