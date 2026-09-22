from pathlib import Path

from tsd_bridge.command_store import CommandIdentity, JsonCommandIdentityStore


def test_put_if_absent_is_idempotent(tmp_path: Path):
    store = JsonCommandIdentityStore(tmp_path / "map.json")
    first = CommandIdentity(
        tsd_command_id="cmd-1",
        deployment_id="dep-1",
        engine_client_order_id="O-1",
        status="submitted",
    )
    inserted, current = store.put_if_absent(first)
    assert inserted is True
    assert current.engine_client_order_id == "O-1"

    inserted2, current2 = store.put_if_absent(
        CommandIdentity(
            tsd_command_id="cmd-1",
            deployment_id="dep-1",
            engine_client_order_id="O-DUPLICATE",
            status="submitted",
        ),
    )
    assert inserted2 is False
    assert current2.engine_client_order_id == "O-1"


def test_update_broker_order_id(tmp_path: Path):
    store = JsonCommandIdentityStore(tmp_path / "map.json")
    store.put_if_absent(
        CommandIdentity(tsd_command_id="cmd-2", deployment_id="dep-1", engine_client_order_id="O-2"),
    )
    store.update(
        CommandIdentity(
            tsd_command_id="cmd-2",
            deployment_id="dep-1",
            engine_client_order_id="O-2",
            broker_order_id="BR-99",
            status="filled",
        ),
    )
    got = store.get("cmd-2")
    assert got is not None
    assert got.broker_order_id == "BR-99"
    assert got.status == "filled"
