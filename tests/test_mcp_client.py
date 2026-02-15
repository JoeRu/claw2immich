import json
import os
import sys
import unittest
from pathlib import Path

import mcp
from mcp.client import stdio as mcp_stdio


def _parse_env_file(path: str) -> dict[str, str]:
    env_vars: dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :]
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"").strip("'")
            if key:
                env_vars[key] = value
    return env_vars


def _build_server_env(env_path: str) -> dict[str, str]:
    if not os.path.exists(env_path):
        raise unittest.SkipTest(f"Missing env file: {env_path}")
    env_vars = os.environ.copy()
    env_vars.update(_parse_env_file(env_path))
    return env_vars


def _extract_tool_payload(result: mcp.types.CallToolResult) -> object:
    if result.structuredContent is not None:
        return result.structuredContent
    if not result.content:
        return None
    first = result.content[0]
    text = getattr(first, "text", None)
    if text is None and isinstance(first, dict):
        text = first.get("text")
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


class MCPClientTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.env_path = os.getenv("IMMICH_ENV_TEST", ".env_test")
        self.server_env = _build_server_env(self.env_path)
        self.repo_root = Path(__file__).resolve().parents[1]

    async def _with_session(self, callback):
        server = mcp_stdio.StdioServerParameters(
            command=sys.executable,
            args=["main.py"],
            env=self.server_env,
            cwd=str(self.repo_root),
        )
        async with mcp_stdio.stdio_client(server) as (read_stream, write_stream):
            session = mcp.ClientSession(read_stream, write_stream)
            await session.initialize()
            return await callback(session)

    async def test_list_tools_includes_core_tools(self) -> None:
        async def run(session: mcp.ClientSession) -> list[str]:
            tools = await session.list_tools()
            names: list[str] = []
            for tool in tools:
                if isinstance(tool, dict):
                    name = tool.get("name")
                else:
                    name = getattr(tool, "name", None)
                if name:
                    names.append(name)
            return names

        tool_names = await self._with_session(run)
        expected = {
            "openapi_summary",
            "list_openapi_paths",
            "ping_server",
            "get_server_info",
            "get_server_version",
            "tool_access_report",
            "write_capability_report",
        }
        self.assertTrue(expected.issubset(set(tool_names)))

    async def test_tool_access_report_shape(self) -> None:
        async def run(session: mcp.ClientSession) -> object:
            return _extract_tool_payload(await session.call_tool("tool_access_report"))

        payload = await self._with_session(run)
        if not isinstance(payload, dict):
            self.fail("Expected tool_access_report to return a dict payload")
        self.assertIn("allowed_tools", payload)
        self.assertIn("blocked_tools", payload)

    async def test_ping_server(self) -> None:
        async def run(session: mcp.ClientSession) -> object:
            return _extract_tool_payload(await session.call_tool("ping_server"))

        payload = await self._with_session(run)
        if isinstance(payload, dict) and payload.get("error"):
            self.skipTest(f"Immich server not reachable: {payload.get('detail')}")
