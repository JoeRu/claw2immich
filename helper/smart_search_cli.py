#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

import httpx


def list_env_files(root: Path) -> list[str]:
    env_files: list[str] = []
    for entry in root.iterdir():
        if not entry.is_file():
            continue
        if entry.name == ".env" or entry.name.startswith(".env_"):
            env_files.append(entry.name)
    return sorted(env_files)


def parse_env_file(path: Path) -> dict[str, str]:
    env_vars: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as env_file:
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
            value = value.strip().strip('"').strip("'")
            if key:
                env_vars[key] = value
    return env_vars


def _build_headers(api_key: str, api_token: str) -> dict[str, str]:
    if api_key:
        return {"x-api-key": api_key}
    if api_token:
        return {"Authorization": f"Bearer {api_token}"}
    raise ValueError("Missing IMMICH_API_KEY or IMMICH_API_TOKEN")


def run_smart_search(
    base_url: str,
    headers: dict[str, str],
    query: str,
    size: int | None,
    page: int | None,
    order: str | None,
) -> str:
    payload: dict[str, object] = {"query": query}
    if size is not None:
        payload["size"] = size

    params: dict[str, object] = {}
    if page is not None:
        params["page"] = page
    if order:
        params["order"] = order

    endpoint = f"{base_url.rstrip('/')}/api/search/smart"
    with httpx.Client(timeout=30.0) as client:
        response = client.post(endpoint, headers=headers, params=params, json=payload)
        response.raise_for_status()
        response_json = response.json()
    return json.dumps(response_json, separators=(",", ":"))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List .env files and execute Immich Smart Search."
    )
    parser.add_argument(
        "--list-envs",
        action="store_true",
        help="List available .env files in current working directory.",
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="Env file to load (default: .env).",
    )
    parser.add_argument(
        "--query",
        help="Smart search query text.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=None,
        help="Optional result size.",
    )
    parser.add_argument(
        "--page",
        type=int,
        default=None,
        help="Optional page number.",
    )
    parser.add_argument(
        "--order",
        choices=["asc", "desc"],
        default=None,
        help="Optional order parameter.",
    )
    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    cwd: Path | None = None,
    stdout=None,
    stderr=None,
) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    cwd = cwd or Path.cwd()

    args = parse_args(argv)
    env_files = list_env_files(cwd)

    if args.list_envs:
        for env_name in env_files:
            print(env_name, file=stdout)
        if not args.query:
            return 0

    if not args.query:
        print("Missing required argument: --query", file=stderr)
        return 2

    env_path = cwd / args.env
    if not env_path.exists():
        listed = ", ".join(env_files) if env_files else "(none)"
        print(
            f"Env file not found: {args.env}. Available: {listed}",
            file=stderr,
        )
        return 2

    try:
        env_vars = parse_env_file(env_path)
        base_url = env_vars.get("IMMICH_BASE_URL", "").strip().rstrip("/")
        if not base_url:
            raise ValueError("Missing IMMICH_BASE_URL")
        headers = _build_headers(
            env_vars.get("IMMICH_API_KEY", "").strip(),
            env_vars.get("IMMICH_API_TOKEN", "").strip(),
        )
        output = run_smart_search(
            base_url=base_url,
            headers=headers,
            query=args.query,
            size=args.size,
            page=args.page,
            order=args.order,
        )
    except Exception as exc:
        print(str(exc), file=stderr)
        return 1

    print(output, file=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
