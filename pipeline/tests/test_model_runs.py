from datetime import UTC, datetime

from analyzer.store.neon import NeonStore


class Conn:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []
        self.commits = 0

    def execute(self, sql: str, params: tuple = ()):
        self.calls.append((sql, params))

    def commit(self) -> None:
        self.commits += 1


def test_insert_model_run_urutan_kolom_dan_json() -> None:
    conn = Conn()
    store = NeonStore(conn)
    store.insert_model_run(
        "crypto-1h-4h-confluence-v1",
        "crypto",
        "BTCUSDT",
        "1h",
        "4h",
        {"bss": 0.01},
        False,
        {"model": "confluence"},
    )
    sql, params = conn.calls[0]
    assert "INSERT INTO model_runs" in sql
    assert (
        "(version, market, symbol, timeframe, horizon, metrics_json, passed_gate, artifact)" in sql
    )
    assert params[:5] == ("crypto-1h-4h-confluence-v1", "crypto", "BTCUSDT", "1h", "4h")
    assert params[5].obj == {"bss": 0.01} and params[6] is False
    assert params[7].obj == {"model": "confluence"}
    assert conn.commits == 1
    assert isinstance(datetime.now(UTC), datetime)
