from pathlib import Path

from tsd_bridge.command_store import JsonCommandIdentityStore
from tsd_bridge.paper_runner import PaperTargetRequest, PaperTargetRunner


def test_paper_runner_fills_and_blocks_duplicate(tmp_path: Path):
    runner = PaperTargetRunner(JsonCommandIdentityStore(tmp_path / "ids.json"))
    req = PaperTargetRequest(
        tsd_command_id="paper-job-1",
        deployment_id="dep-demo",
        seed_quantity="0.18",
        target_quantity="0.20",
    )
    first = runner.run(req)
    assert first.accepted is True
    assert first.duplicate is False
    assert first.evidence["final_position"] == "0.200000"
    assert first.identity.engine_client_order_id == "paper-job-1"

    second = runner.run(req)
    assert second.accepted is False
    assert second.duplicate is True
    assert second.status == "duplicate"
