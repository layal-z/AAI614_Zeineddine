#37- Local MCP server for controlled recruitment retrieval.
# The notebook supplies a temporary snapshot after checking approvals.
# The server exposes read-only tools and cannot update the tracker.

import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("Recruitment Retrieval")
snapshot_path = None


def read_authorized_snapshot(tool_name: str, candidate_id: str) -> dict:
    """Read only the tool and candidate authorized by the application."""

    if snapshot_path is None:
        raise RuntimeError("No application snapshot was supplied.")

    snapshot = json.loads(
        snapshot_path.read_text(encoding="utf-8")
    )

    # The model cannot choose another file or change the authorized scope.
    if (
        snapshot["tool_name"] != tool_name
        or snapshot["candidate_id"] != candidate_id
    ):
        raise PermissionError("Unauthorized tool or candidate request.")

    data = snapshot["data"]

    if not isinstance(data, dict):
        raise ValueError("Invalid retrieval snapshot.")

    if data.get("candidate_id") != candidate_id:
        raise PermissionError("Snapshot candidate does not match.")

    return data


@mcp.tool()
def read_candidate_evidence(candidate_id: str) -> dict:
    """Retrieve the selected candidate's CV evidence with source IDs."""
    return read_authorized_snapshot(
        "read_candidate_evidence",
        candidate_id
    )


@mcp.tool()
def read_interview_context(candidate_id: str) -> dict:
    """Retrieve approved criteria and reviewed screening for interview planning."""
    return read_authorized_snapshot(
        "read_interview_context",
        candidate_id
    )


@mcp.tool()
def read_evaluation_context(candidate_id: str) -> dict:
    """Retrieve approved criteria, CV evidence and reviewed interview evidence."""
    return read_authorized_snapshot(
        "read_evaluation_context",
        candidate_id
    )


if __name__ == "__main__":
    # The MCP client supplies this path when launching the subprocess.
    # It is not an argument exposed to the model.
    if len(sys.argv) != 2:
        raise RuntimeError("Supply one application snapshot path.")

    snapshot_path = Path(sys.argv[1]).resolve()

    if not snapshot_path.is_file():
        raise FileNotFoundError("The retrieval snapshot does not exist.")

    # Standard input/output carries MCP protocol messages.
    # Do not print ordinary messages to stdout in this server.
    mcp.run(transport="stdio")