from modules.rerankers.fake import FakeReranker
from modules.types import Document

def test_fake_reranker_smoke():
    rr = FakeReranker(weight=1.0, top_k=3)
    docs = [
        Document(id="1", text="USB-C cable fast charging 60W"),
        Document(id="2", text="HDMI cable 4k video high speed"),
        Document(id="3", text="Wireless mouse bluetooth silent"),
        Document(id="4", text="AI deep learning transformer tutorial"),
    ]
    out = rr.rerank("fast usb c cable", docs)
    assert len(out) == 3
    # top-1 should contain 'USB-C cable...' due to token overlap
    assert out[0].document.id in {"1"}
