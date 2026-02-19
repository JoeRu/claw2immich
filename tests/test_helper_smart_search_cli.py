import io
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_smart_search_cli_module():
    module_path = Path(__file__).resolve().parents[1] / "helper" / "smart_search_cli.py"
    spec = importlib.util.spec_from_file_location("smart_search_cli", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load helper/smart_search_cli.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


smart_search_cli = _load_smart_search_cli_module()


class SmartSearchCliTests(unittest.TestCase):
    def test_list_env_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text("IMMICH_BASE_URL=https://example.com\n", encoding="utf-8")
            (root / ".env_test").write_text("IMMICH_BASE_URL=https://example.com\n", encoding="utf-8")
            (root / "notes.txt").write_text("ignore\n", encoding="utf-8")

            result = smart_search_cli.list_env_files(root)

            self.assertEqual(result, [".env", ".env_test"])

    def test_parse_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "# test\n"
                "export IMMICH_BASE_URL=https://immich.example.com\n"
                "IMMICH_API_KEY='abc123'\n",
                encoding="utf-8",
            )

            values = smart_search_cli.parse_env_file(env_file)

            self.assertEqual(values["IMMICH_BASE_URL"], "https://immich.example.com")
            self.assertEqual(values["IMMICH_API_KEY"], "abc123")

    def test_main_list_envs_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text("IMMICH_BASE_URL=https://example.com\n", encoding="utf-8")
            (root / ".env_web").write_text("IMMICH_BASE_URL=https://example.com\n", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            exit_code = smart_search_cli.main(
                argv=["--list-envs"], cwd=root, stdout=stdout, stderr=stderr
            )

            self.assertEqual(exit_code, 0)
            self.assertIn(".env", stdout.getvalue())
            self.assertIn(".env_web", stdout.getvalue())
            self.assertEqual(stderr.getvalue(), "")

    def test_main_requires_query(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            stdout = io.StringIO()
            stderr = io.StringIO()

            exit_code = smart_search_cli.main(argv=[], cwd=root, stdout=stdout, stderr=stderr)

            self.assertEqual(exit_code, 2)
            self.assertIn("--query", stderr.getvalue())

    def test_main_handles_missing_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            stdout = io.StringIO()
            stderr = io.StringIO()

            exit_code = smart_search_cli.main(
                argv=["--env", ".env_missing", "--query", "dog"],
                cwd=root,
                stdout=stdout,
                stderr=stderr,
            )

            self.assertEqual(exit_code, 2)
            self.assertIn("Env file not found", stderr.getvalue())

    def test_main_executes_smart_search_and_prints_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text(
                "IMMICH_BASE_URL=https://immich.example.com\n"
                "IMMICH_API_KEY=test-key\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with patch.object(
                smart_search_cli,
                "run_smart_search",
                return_value='{"assets":{"items":[]}}',
            ) as mocked:
                exit_code = smart_search_cli.main(
                    argv=["--query", "golden hour", "--size", "5", "--order", "desc"],
                    cwd=root,
                    stdout=stdout,
                    stderr=stderr,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), '{"assets":{"items":[]}}')
            self.assertEqual(stderr.getvalue(), "")
            mocked.assert_called_once()

    def test_main_handles_http_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text(
                "IMMICH_BASE_URL=https://immich.example.com\n"
                "IMMICH_API_KEY=test-key\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with patch.object(
                smart_search_cli,
                "run_smart_search",
                side_effect=RuntimeError("HTTP 401 Unauthorized"),
            ):
                exit_code = smart_search_cli.main(
                    argv=["--query", "cats"],
                    cwd=root,
                    stdout=stdout,
                    stderr=stderr,
                )

            self.assertEqual(exit_code, 1)
            self.assertIn("401", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
