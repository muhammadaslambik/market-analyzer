import importlib
from pathlib import Path

import pytest
import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
SECRETS = {"DATABASE_URL", "CF_ACCOUNT_ID", "CF_D1_DATABASE_ID", "CF_API_TOKEN"}


@pytest.mark.parametrize(
    ("filename", "module", "cron"),
    [
        ("crypto-hourly.yml", "analyzer.jobs.crypto_hourly", "7 * * * *"),
        ("crypto-daily.yml", "analyzer.jobs.crypto_daily", "12 0 * * *"),
    ],
)
def test_workflow_terjadwal_sesuai_spesifikasi(filename: str, module: str, cron: str) -> None:
    workflow = yaml.safe_load((WORKFLOWS / filename).read_text(encoding="utf-8"))
    triggers = workflow.get("on") or workflow.get(True)  # PyYAML membaca kunci `on` sebagai True
    assert triggers["schedule"][0]["cron"] == cron
    assert "workflow_dispatch" in triggers
    assert workflow["concurrency"]["cancel-in-progress"] is False
    assert workflow["permissions"] == {"contents": "read"}

    job = workflow["jobs"]["run"]
    assert job["timeout-minutes"] <= 15
    run_step = job["steps"][-1]
    assert run_step["run"] == f"python -m {module}"
    assert set(run_step["env"]) == SECRETS
    assert all(v.startswith("${{ secrets.") for v in run_step["env"].values())
    importlib.import_module(module)  # nama modul harus benar-benar ada
