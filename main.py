from claw2immich.capabilities import (
    _discover_capabilities,
    _discover_write_capability,
    _write_probe_settings,
)
from claw2immich.http_client import _probe
from claw2immich.mcp_app import run
from claw2immich.openapi import (
    _fetch_openapi_spec,
    _list_openapi_operations,
    _merge_parameters,
    _operation_admin_only,
    _operation_param_specs,
    _operation_request_body_spec,
    _tool_name_for_operation,
)
from claw2immich.tooling import tool_access_report


def main() -> None:
    run()


if __name__ == "__main__":
    main()
