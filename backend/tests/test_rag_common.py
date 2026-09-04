from __future__ import annotations

from io import BytesIO
import json

import pytest

from scraper.rag_common import BedrockEmbeddings, EmbeddingCache


class FakeBedrockClient:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []

    def invoke_model(self, **request):
        self.requests.append(request)
        body = json.loads(str(request["body"]))
        dimensions = int(body["dimensions"])
        return {
            "body": BytesIO(
                json.dumps({"embedding": [0.25] * dimensions}).encode("utf-8")
            )
        }


def test_bedrock_embeddings_use_titan_v2_and_cache_results(tmp_path) -> None:
    client = FakeBedrockClient()
    embedder = BedrockEmbeddings(
        region_name="us-east-1",
        dimensions=256,
        client=client,
    )
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")
    try:
        first = embedder.embed_with_cache(["critical illness"], cache, batch_size=1)
        second = embedder.embed_with_cache(["critical illness"], cache, batch_size=1)
    finally:
        cache.close()

    assert first == second
    assert len(first[0]) == 256
    assert len(client.requests) == 1
    assert client.requests[0]["modelId"] == "amazon.titan-embed-text-v2:0"
    assert json.loads(str(client.requests[0]["body"])) == {
        "inputText": "critical illness",
        "dimensions": 256,
        "normalize": True,
    }


def test_bedrock_embeddings_reject_unsupported_dimensions() -> None:
    with pytest.raises(ValueError, match="256, 512, 1024"):
        BedrockEmbeddings(region_name="us-east-1", dimensions=1536)
