import json
import subprocess
from pathlib import Path

from scripts import run_live_source_canary as canary


def test_classify_adapter_payload_distinguishes_live_evidence_from_blockers() -> None:
    healthy = canary.classify_adapter_payload(
        "cppp",
        {
            "results": [
                {
                    "adapter": "cppp",
                    "opportunities": [
                        {
                            "external_reference": "CPP/2026/1",
                            "opportunity_title": "Supply and installation of laboratory equipment",
                            "source_url": "https://example.test/tender/1",
                            "blocker_status": "",
                        }
                    ],
                }
            ]
        },
    )
    blocked = canary.classify_adapter_payload(
        "ungm",
        {
            "results": [
                {
                    "adapter": "ungm",
                    "opportunities": [
                        {"external_reference": "", "source_url": "", "blocker_status": "CAPTCHA"}
                    ],
                }
            ]
        },
    )

    assert healthy["status"] == "HEALTHY"
    assert healthy["evidence_backed_records"] == 1
    assert blocked["status"] == "BLOCKED"
    assert blocked["blockers"] == ["CAPTCHA"]


def test_classify_adapter_payload_rejects_shifted_or_placeholder_fields() -> None:
    result = canary.classify_adapter_payload(
        "cppp",
        {
            "results": [
                {
                    "adapter": "cppp",
                    "opportunities": [
                        {
                            "external_reference": "11-Jul-2026 06:55 PM",
                            "opportunity_title": "25-Jul-2026 05:00 PM",
                            "source_url": "https://eprocure.gov.in/cppp/tendersfullview/example",
                            "blocker_status": "",
                        }
                    ],
                }
            ]
        },
    )

    assert result["status"] == "UNPROVEN"
    assert result["evidence_backed_records"] == 0
    assert "external_reference looks like a date or placeholder" in result["quality_issues"]

    navigation_fallback = canary.opportunity_quality_issues(
        {
            "external_reference": "Request",
            "opportunity_title": "Procurement opportunities English Help Center Log in Register " * 12,
            "source_url": "https://www.ungm.org/Public/Notice",
        }
    )
    assert "external_reference looks like a date or placeholder" in navigation_fallback
    assert "opportunity_title looks like page navigation rather than a record" in navigation_fallback


def test_run_canary_fails_truthfully_when_no_adapter_is_healthy(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "run_source_adapter.py").write_text("# fixture\n", encoding="utf-8")

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        output = Path(command[command.index("--output") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "adapter": "cppp",
                            "opportunities": [
                                {"external_reference": "", "source_url": "", "blocker_status": "LOGIN_REQUIRED"}
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, stdout="adapter wrote output", stderr="")

    report = canary.run_canary(
        ["cppp"],
        project_root=tmp_path,
        runner=runner,
        stamp="20260712T130000Z",
    )

    assert report["status"] == "FAIL"
    assert report["healthy_adapters"] == 0
    assert report["external_business_actions"] is False
