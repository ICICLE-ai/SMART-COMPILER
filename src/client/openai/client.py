import json
import os
from typing import Any
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.session import ListRootsFnT
from mcp.client.sse import sse_client
from mcp.shared.context import RequestContext
from mcp.types import ErrorData, ListRootsResult, Root, TextResourceContents
from pydantic import FileUrl

from client.abstract.base_client import AbstractMCPClient
from shared.logging import get_logger


load_dotenv()
logger = get_logger()


class LLMListRootsFnT(ListRootsFnT):
    async def __call__(self, context: RequestContext[ClientSession, Any]) -> ListRootsResult | ErrorData:
        return ListRootsResult(
            roots=[
                Root(
                    name="smart-compiler-db_mock",
                    uri=FileUrl(os.getenv("ALLOWED_PATHS", "")),
                )
            ]
        )


class OpenAIResponsesMCPClient(AbstractMCPClient):
    """MCP client using the OpenAI Responses API and function calling."""

    def __init__(self):
        super().__init__()
        self.llm_host = os.getenv("LLM_HOST", "https://api.openai.com/v1").rstrip("/")
        self.llm_model = os.getenv("LLM_MODEL", "gpt-6-astra")
        parsed_host = urlsplit(self.llm_host)
        is_local = parsed_host.hostname in {"localhost", "127.0.0.1", "::1"}
        self._use_responses_api = parsed_host.hostname == "api.openai.com"
        api_key = os.getenv("OPENAI_API_KEY")
        if self._use_responses_api and not api_key:
            raise RuntimeError(
                "Set OPENAI_API_KEY in your shell before using the OpenAI API."
            )
        headers = {}
        if api_key and not is_local:
            headers["Authorization"] = "Bearer " + api_key
        self.http = httpx.AsyncClient(
            base_url=self.llm_host + "/",
            headers=headers,
            timeout=httpx.Timeout(180.0),
        )
        self.tools = []

    async def connect_to_server(self):
        server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
        self.stdio, self.write = await self.exit_stack.enter_async_context(
            sse_client(server_url)
        )
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(
                self.stdio,
                self.write,
                list_roots_callback=LLMListRootsFnT(),
            )
        )
        await self.session.initialize()
        response = await self.session.list_tools()
        self.tools = [
            {
                "type": "function",
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema,
            }
            for tool in response.tools
        ]
        logger.info("Connected to MCP server with %d tools", len(self.tools))

    def _chat_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool["parameters"],
                },
            }
            for tool in self.tools
        ]

    @staticmethod
    def _result_text(result: Any) -> str:
        parts = []
        for item in result.content:
            if item.type == "text":
                parts.append(item.text)
            elif item.type == "image":
                parts.append("[Tool returned an image]")
            elif item.type == "resource":
                resource = item.resource
                parts.append(
                    resource.text
                    if isinstance(resource, TextResourceContents)
                    else str(resource.blob)
                )
        return chr(10).join(parts) or "Tool returned no text."

    async def _call_api(self, endpoint: str, payload: dict) -> dict:
        response = await self.http.post(endpoint, json=payload)
        if not response.is_success:
            detail = ""
            try:
                detail = response.json().get("error", {}).get("message", "")
            except (ValueError, AttributeError):
                pass
            if not detail:
                detail = response.text[:500]
            raise RuntimeError(
                "LLM API returned HTTP "
                + str(response.status_code)
                + ": "
                + detail
            )
        return response.json()

    async def process_query(self, query: str) -> str:
        if self.session is None:
            raise ValueError("Session not initialized")

        instructions = """
You are SColer, an assistant specializing in compilers and C optimization.
Use the provided MCP tools whenever they can perform the requested work.
For a request to optimize a C file by path, call get_file_content with the exact path first, then call optimize_code_snippet with the returned C source and the requested profile. Never pass a file path or tool name as code_snippet.
Available profiles include parallel, paw_tiling_nt, paw_tiling_lrw, paw_tiling_fixed32, reuse_analysis, and loop_interchange. Use parallel when the request does not name a profile.
Do not substitute GCC or LLVM shell commands for Cetus. Do not invent tool results or claim an optimization succeeded unless the tool returned the result.
""".strip()
        inputs = [{"role": "user", "content": query}]
        chat_messages = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": query},
        ]
        final_text = []

        for _ in range(8):
            if self._use_responses_api:
                response = await self._call_api(
                    "responses",
                    {
                        "model": self.llm_model,
                        "instructions": instructions,
                        "input": inputs,
                        "tools": self.tools,
                        "tool_choice": "auto",
                    },
                )
                output = response.get("output", [])
                calls = [
                    {
                        "call_id": item.get("call_id"),
                        "name": item.get("name"),
                        "arguments": item.get("arguments", "{}"),
                    }
                    for item in output
                    if item.get("type") == "function_call"
                ]
                if not calls:
                    for item in output:
                        if item.get("type") == "message":
                            for content in item.get("content", []):
                                if content.get("type") == "output_text":
                                    final_text.append(content.get("text", ""))
                    return chr(10).join(part for part in final_text if part)
                inputs.extend(output)
            else:
                response = await self._call_api(
                    "chat/completions",
                    {
                        "model": self.llm_model,
                        "messages": chat_messages,
                        "tools": self._chat_tools(),
                    },
                )
                choices = response.get("choices", [])
                if not choices:
                    raise RuntimeError("LLM API returned no choices")
                message = choices[0].get("message", {})
                calls = [
                    {
                        "call_id": item.get("id"),
                        "name": item.get("function", {}).get("name"),
                        "arguments": item.get("function", {}).get(
                            "arguments", "{}"
                        ),
                    }
                    for item in message.get("tool_calls", [])
                ]
                if not calls:
                    return message.get("content") or ""
                chat_messages.append(message)

            for call in calls:
                name = call["name"]
                args = json.loads(call.get("arguments") or "{}")
                if not isinstance(args, dict):
                    raise ValueError("The LLM returned invalid tool arguments")
                if name == "optimize_code_snippet" and "profile" in args:
                    args.setdefault("optimization_profile", args.pop("profile"))

                if name == "optimize_code_snippet":
                    snippet = str(args.get("code_snippet") or "").strip()
                    path = args.pop("path", None)
                    placeholder = not snippet or (
                        len(snippet) < 256
                        and (
                            "get_file_content" in snippet.lower()
                            or snippet == "read_file"
                        )
                    )
                    if not path and (placeholder or snippet.endswith(".c")):
                        for token in query.split():
                            candidate = token.strip(" \t\r\n\"'.,:;()[]{}<>")
                            if candidate.startswith("/") and candidate.endswith(".c"):
                                path = candidate
                                break
                    if path and (placeholder or snippet == str(path)):
                        read_result = await self.session.call_tool(
                            "get_file_content", {"path": str(path)}
                        )
                        read_text = self._result_text(read_result)
                        final_text.append(
                            "[Calling tool get_file_content with path "
                            + str(path)
                            + "]"
                        )
                        if getattr(read_result, "isError", False):
                            final_text.append(read_text)
                            return chr(10).join(final_text)
                        args["code_snippet"] = read_text

                result = await self.session.call_tool(name, args)
                text = self._result_text(result)
                if name == "optimize_code_snippet":
                    profile = args.get("optimization_profile", "parallel")
                    final_text.append(
                        "[Calling tool optimize_code_snippet with profile "
                        + str(profile)
                        + "]"
                    )
                else:
                    final_text.append(
                        "[Calling tool " + name + " with args " + str(args) + "]"
                    )
                final_text.append(text)
                if self._use_responses_api:
                    inputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": call["call_id"],
                            "output": text,
                        }
                    )
                else:
                    chat_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call["call_id"],
                            "content": text,
                        }
                    )
                if name == "optimize_code_snippet":
                    return chr(10).join(final_text)

        final_text.append("Stopped after 8 MCP tool rounds.")
        return chr(10).join(final_text)

    async def chat_loop(self):
        logger.info("Type your queries or 'quit' to exit.")
        while True:
            try:
                query = input("You: ")
                if query.lower() == "quit":
                    break
                print(chr(10) + await self.process_query(query) + chr(10))
            except Exception as exc:
                logger.error("LLM request failed: %s", exc)

    async def cleanup(self):
        await self.exit_stack.aclose()
        await self.http.aclose()
