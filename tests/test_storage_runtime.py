from morphosis.os.storage import SQLiteLedger


def test_sqlite_health_and_close(tmp_path):
    path = tmp_path / "ledger.db"
    ledger = SQLiteLedger(path)
    health = ledger.health()
    assert health["ready"] is True
    assert health["integrity"] == "ok"
    assert health["events"] == 0
    assert health["schema_version"] == 1
    ledger.close()


def test_sqlite_persists_schema_metadata(tmp_path):
    path = tmp_path / "ledger.db"
    one = SQLiteLedger(path)
    one.close()
    two = SQLiteLedger(path)
    assert two.health()["schema_version"] == 1
    two.close()
