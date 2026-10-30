import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from client.openai.client import OpenAIResponsesMCPClient


class FakeSession:
    def __init__(self):
        self.calls = []

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        text = (
            "int main(void) { return 0; }"
            if name == "get_file_content"
            else "Cetus transformed the source."
        )
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=text)],
            isError=False,
        )


class OpenAICompatibleClientTests(unittest.IsolatedAsyncioTestCase):
    def _tools(self):
        return [
            {
                "type": "function",
                "name": "get_file_content",
                "description": "Read source",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
            {
                "type": "function",
                "name": "optimize_code_snippet",
                "description": "Optimize source",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code_snippet": {"type": "string"},
                        "optimization_profile": {"type": "string"},
                    },
                    "required": ["code_snippet", "optimization_profile"],
                },
            },
        ]

    def _response_tool_call(self, call_id, name, arguments):
        return {
            "type": "function_call",
            "call_id": call_id,
            "name": name,
            "arguments": json.dumps(arguments),
        }

    def _chat_tool_call(self, call_id, name, arguments):
        return {
            "id": call_id,
            "type": "function",
            "function": {
                "name": name,
                "arguments": json.dumps(arguments),
            },
        }

    async def test_responses_function_calls_round_trip_to_mcp(self):
        with patch.dict(
            os.environ,
            {
                "LLM_HOST": "https://api.openai.com/v1",
                "LLM_MODEL": "gpt-6-astra",
                "OPENAI_API_KEY": "unit-test-key",
            },
        ):
            client = OpenAIResponsesMCPClient()

        client.session = FakeSession()
        client.tools = self._tools()
        requests = []
        responses = [
            {"output": [self._response_tool_call(
                "read-call", "get_file_content", {"path": "/tmp/example.c"}
            )]},
            {"output": [self._response_tool_call(
                "opt-call",
                "optimize_code_snippet",
                {
                    "code_snippet": "int main(void) { return 0; }",
                    "optimization_profile": "parallel",
                },
            )]},
        ]

        async def fake_api(endpoint, payload):
            requests.append((endpoint, payload))
            return responses.pop(0)

        client._call_api = fake_api
        try:
            result = await client.process_query(
                "Read /tmp/example.c and optimize it with parallel."
            )
        finally:
            await client.cleanup()

        self.assertIn("Cetus transformed the source.", result)
        self.assertEqual(
            [name for name, _ in client.session.calls],
            ["get_file_content", "optimize_code_snippet"],
        )
        self.assertEqual(requests[0][0], "responses")
        self.assertEqual(requests[0][1]["model"], "gpt-6-astra")
        self.assertEqual(requests[0][1]["tools"][0]["type"], "function")
        self.assertTrue(
            any(
                item.get("type") == "function_call_output"
                and item.get("call_id") == "read-call"
                for item in requests[1][1]["input"]
            )
        )

    async def test_chat_completions_tool_results_keep_call_ids(self):
        with patch.dict(
            os.environ,
            {
                "LLM_HOST": "https://provider.example/v1",
                "LLM_MODEL": "provider-model",
                "OPENAI_API_KEY": "unit-test-key",
            },
        ):
            client = OpenAIResponsesMCPClient()

        client.session = FakeSession()
        client.tools = self._tools()
        requests = []
        responses = [
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                self._chat_tool_call(
                                    "read-call",
                                    "get_file_content",
                                    {"path": "/tmp/example.c"},
                                )
                            ],
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                self._chat_tool_call(
                                    "opt-call",
                                    "optimize_code_snippet",
                                    {
                                        "code_snippet": "int main(void) { return 0; }",
                                        "optimization_profile": "parallel",
                                    },
                                )
                            ],
                        }
                    }
                ]
            },
        ]

        async def fake_api(endpoint, payload):
            requests.append((endpoint, payload))
            return responses.pop(0)

        client._call_api = fake_api
        try:
            result = await client.process_query(
                "Read /tmp/example.c and optimize it with parallel."
            )
        finally:
            await client.cleanup()

        self.assertIn("Cetus transformed the source.", result)
        self.assertEqual(
            [endpoint for endpoint, _ in requests],
            ["chat/completions", "chat/completions"],
        )
        tool_messages = [
            item
            for item in requests[1][1]["messages"]
            if item.get("role") == "tool"
        ]
        self.assertEqual(tool_messages[0]["tool_call_id"], "read-call")
        self.assertEqual(requests[0][1]["tools"][0]["type"], "function")


if __name__ == "__main__":
    unittest.main()
