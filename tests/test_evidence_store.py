import json

from scripts.source_runtime.evidence_store import EvidenceStore


def test_evidence_manifest_tracks_files_and_redacts_secrets(tmp_path) -> None:
    store = EvidenceStore("GOV", "GOV-CANDIDATE-1", "Test Source", "https://example.test", "RUN-1", root=tmp_path)
    html_path = store.path_for("raw_html", "detail.html")
    html_path.write_text("<html>password=secret-value</html>", encoding="utf-8")
    store.record_raw_html(html_path)
    store.add_blocker("LOGIN_REQUIRED", details="password=secret-value")
    manifest = json.loads(store.manifest_path.read_text(encoding="utf-8"))
    assert manifest["raw_html"][0]["path"]
    assert manifest["blockers"][0]["reason"] == "LOGIN_REQUIRED"
    assert "secret-value" not in store.manifest_path.read_text(encoding="utf-8")
