from scripts.source_runtime.document_downloader import DocumentDownloader
from scripts.source_runtime.evidence_store import EvidenceStore


class FakeResponse:
    ok = True
    status = 200

    def body(self) -> bytes:
        return b"fixture document"


class FakeRequest:
    def get(self, url: str, timeout: int):
        return FakeResponse()


class FakeContext:
    request = FakeRequest()


class FakePage:
    context = FakeContext()


def test_browser_context_download_records_document(tmp_path) -> None:
    store = EvidenceStore("GOV", "DL", "Fixture", "https://example.test", "RUN", root=tmp_path)
    downloader = DocumentDownloader(store)
    document = downloader.download_from_browser_context(FakePage(), "https://example.test/nit.pdf")
    assert document is not None
    assert document.sha256
    assert store.manifest["downloads"][0]["local_path"]
