import os
import unittest

import main


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


def _ensure_server_reachable() -> None:
    probe = main._probe("GET", "/api/server/ping")
    if not probe.get("ok"):
        detail = probe.get("detail") or probe.get("error") or "unknown error"
        raise unittest.SkipTest(f"Immich server not reachable: {detail}")


class IntegrationPermissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._original_env)
        main._discover_capabilities.cache_clear()

    def _load_env(self, env_path: str) -> None:
        if not os.path.exists(env_path):
            raise unittest.SkipTest(f"Missing env file: {env_path}")
        os.environ.update(_parse_env_file(env_path))

    def _assert_access_matches_probe(self) -> None:
        probe = main._probe("GET", "/api/users/me", require_auth=True)
        expected_allowed = bool(probe.get("ok"))

        main._discover_capabilities.cache_clear()
        report = main.tool_access_report()
        blocked = {item["tool"]: item["reason"] for item in report["blocked_tools"]}

        if expected_allowed:
            if "get_current_user" in blocked:
                self.fail(
                    "Expected get_current_user to be allowed; "
                    f"reason: {blocked['get_current_user']}"
                )
            self.assertIn("get_current_user", report["allowed_tools"])
        else:
            self.assertIn("get_current_user", blocked)
            self.assertNotIn("get_current_user", report["allowed_tools"])

    def test_read_only_credentials_block_get_current_user(self) -> None:
        env_path = os.getenv("IMMICH_ENV_TEST", ".env_test")
        self._load_env(env_path)
        _ensure_server_reachable()
        self._assert_access_matches_probe()

    def test_full_credentials_allow_get_current_user(self) -> None:
        env_path = os.getenv("IMMICH_ENV_FULL", ".env")
        self._load_env(env_path)
        _ensure_server_reachable()
        self._assert_access_matches_probe()
