"""Shared HTTP, environment, and embedding helpers for the insurance RAG tools."""

from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable


DEFAULT_BEDROCK_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
DEFAULT_BEDROCK_EMBEDDING_DIMENSIONS = 1024
TRANSIENT_HTTP_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504}
BEDROCK_TRANSIENT_ERROR_CODES = {
    "InternalServerException",
    "ModelNotReadyException",
    "ModelTimeoutException",
    "RequestTimeout",
    "RequestTimeoutException",
    "ServiceUnavailable",
    "ServiceUnavailableException",
    "Throttling",
    "ThrottlingException",
}
BEDROCK_TRANSIENT_EXCEPTION_NAMES = {
    "ConnectTimeoutError",
    "ConnectionClosedError",
    "EndpointConnectionError",
    "HTTPClientError",
    "ReadTimeoutError",
}


class TransientNetworkError(RuntimeError):
    """A retryable remote-service failure safe for a higher-level resume loop."""


def retry_delay(attempt: int) -> float:
    return min(30.0, 2 ** max(0, attempt - 1) + random.random())


def is_transient_bedrock_error(error: Exception) -> bool:
    response = getattr(error, "response", None)
    error_code = None
    if isinstance(response, dict):
        details = response.get("Error")
        if isinstance(details, dict):
            error_code = details.get("Code")
    return (
        isinstance(error, (ConnectionError, TimeoutError, OSError))
        or error.__class__.__name__ in BEDROCK_TRANSIENT_EXCEPTION_NAMES
        or error_code in BEDROCK_TRANSIENT_ERROR_CODES
    )


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def chunks(values: list[Any], size: int) -> Iterable[list[Any]]:
    for start in range(0, len(values), size):
        yield values[start:start + size]


def error_message(payload: bytes, status: int, service: str) -> str:
    try:
        parsed = json.loads(payload.decode("utf-8", errors="replace"))
        message = parsed.get("message") or parsed.get("error", {}).get("message")
        details = parsed.get("details")
        if message:
            return f"{service} HTTP {status}: {message}" + (f" ({details})" if details else "")
    except (json.JSONDecodeError, AttributeError):
        pass
    return f"{service} HTTP {status}"


class SupabaseREST:
    """Small PostgREST client using the Supabase service role."""

    def __init__(
        self,
        url: str,
        service_key: str,
        *,
        timeout: int = 120,
        max_attempts: int = 5,
    ) -> None:
        self.rest_url = url.rstrip("/") + "/rest/v1"
        self.service_key = service_key
        self.timeout = timeout
        self.max_attempts = max(1, max_attempts)

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: Any = None,
        prefer: str | None = None,
        retry_transient: bool = True,
    ) -> Any:
        url = self.rest_url + "/" + path.lstrip("/")
        if query:
            url += "?" + urllib.parse.urlencode(query, safe="(),.*:-_")
        encoded = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "sn-hackathon-insurance-rag/1.0",
        }
        if prefer:
            headers["Prefer"] = prefer
        attempts = self.max_attempts if retry_transient else 1
        for attempt in range(1, attempts + 1):
            request = urllib.request.Request(
                url,
                data=encoded,
                method=method,
                headers=headers,
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    payload = response.read()
                if not payload:
                    return None
                return json.loads(payload.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                payload = exc.read()
                failure = RuntimeError(error_message(payload, exc.code, "Supabase"))
                if exc.code not in TRANSIENT_HTTP_STATUSES:
                    raise failure from exc
                if attempt == attempts:
                    raise TransientNetworkError(str(failure)) from exc
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                if attempt == attempts:
                    raise TransientNetworkError(
                        f"Supabase request failed after {attempt} attempt(s): {exc}"
                    ) from exc
            delay = retry_delay(attempt)
            print(
                f"RETRY supabase method={method} path={path} "
                f"attempt={attempt + 1}/{attempts} delay={delay:.1f}s",
                flush=True,
            )
            time.sleep(delay)
        raise TransientNetworkError("Supabase request failed")

    def select(
        self,
        table: str,
        *,
        columns: str = "*",
        filters: dict[str, str] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        query = {"select": columns, **(filters or {})}
        if limit is not None:
            query["limit"] = str(limit)
        result = self.request("GET", table, query=query)
        return result or []

    def insert(self, table: str, rows: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = self.request(
            "POST",
            table,
            body=rows,
            prefer="return=representation",
            retry_transient=False,
        )
        return result or []

    def upsert(
        self,
        table: str,
        rows: dict[str, Any] | list[dict[str, Any]],
        *,
        on_conflict: str,
    ) -> list[dict[str, Any]]:
        result = self.request(
            "POST",
            table,
            query={"on_conflict": on_conflict},
            body=rows,
            prefer="resolution=merge-duplicates,return=representation",
        )
        return result or []

    def update(self, table: str, values: dict[str, Any], filters: dict[str, str]) -> list[dict[str, Any]]:
        result = self.request(
            "PATCH",
            table,
            query=filters,
            body=values,
            prefer="return=representation",
        )
        return result or []

    def delete(self, table: str, filters: dict[str, str]) -> None:
        self.request("DELETE", table, query=filters, prefer="return=minimal")

    def rpc(self, function_name: str, body: dict[str, Any]) -> Any:
        return self.request("POST", f"rpc/{function_name}", body=body)


class EmbeddingCache:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
              cache_key TEXT PRIMARY KEY,
              model TEXT NOT NULL,
              dimensions INTEGER NOT NULL,
              embedding_json TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.commit()

    @staticmethod
    def key(model: str, dimensions: int, text: str) -> str:
        raw = f"{model}\0{dimensions}\0{text}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, model: str, dimensions: int, text: str) -> list[float] | None:
        row = self.connection.execute(
            "SELECT embedding_json FROM embeddings WHERE cache_key = ?",
            (self.key(model, dimensions, text),),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, model: str, dimensions: int, text: str, embedding: list[float]) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO embeddings(cache_key, model, dimensions, embedding_json) VALUES (?, ?, ?, ?)",
            (self.key(model, dimensions, text), model, dimensions, json.dumps(embedding, separators=(",", ":"))),
        )

    def commit(self) -> None:
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()


class BedrockEmbeddings:
    """Amazon Titan Text Embeddings V2 client with local result caching."""

    SUPPORTED_DIMENSIONS = {256, 512, 1024}

    def __init__(
        self,
        *,
        model: str = DEFAULT_BEDROCK_EMBEDDING_MODEL,
        dimensions: int = DEFAULT_BEDROCK_EMBEDDING_DIMENSIONS,
        region_name: str,
        timeout: int = 120,
        max_attempts: int = 5,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
        client: Any | None = None,
    ) -> None:
        if dimensions not in self.SUPPORTED_DIMENSIONS:
            supported = ", ".join(str(value) for value in sorted(self.SUPPORTED_DIMENSIONS))
            raise ValueError(f"Titan Text Embeddings V2 dimensions must be one of: {supported}")
        if not region_name:
            raise ValueError("AWS region is required for Bedrock embeddings")
        self.model = model
        self.dimensions = dimensions
        self.region_name = region_name
        self.timeout = timeout
        self.max_attempts = max_attempts
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._aws_session_token = aws_session_token
        self._client = client

    def _bedrock_client(self) -> Any:
        if self._client is None:
            import boto3
            from botocore.config import Config

            options: dict[str, Any] = {
                "region_name": self.region_name,
                "config": Config(
                    connect_timeout=self.timeout,
                    read_timeout=self.timeout,
                    retries={"max_attempts": self.max_attempts, "mode": "standard"},
                ),
            }
            if self._aws_access_key_id and self._aws_secret_access_key:
                options.update(
                    {
                        "aws_access_key_id": self._aws_access_key_id,
                        "aws_secret_access_key": self._aws_secret_access_key,
                        "aws_session_token": self._aws_session_token,
                    }
                )
            self._client = boto3.client("bedrock-runtime", **options)
        return self._client

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in texts:
            try:
                response = self._bedrock_client().invoke_model(
                    modelId=self.model,
                    body=json.dumps(
                        {
                            "inputText": text,
                            "dimensions": self.dimensions,
                            "normalize": True,
                        }
                    ),
                    accept="application/json",
                    contentType="application/json",
                )
                payload = json.loads(response["body"].read())
                raw_embedding = payload["embedding"]
                if not isinstance(raw_embedding, list):
                    raise RuntimeError("Bedrock returned an invalid embedding")
                embedding = [float(value) for value in raw_embedding]
                if len(embedding) != self.dimensions:
                    raise RuntimeError(
                        f"Bedrock embedding dimension did not match {self.dimensions}"
                    )
                embeddings.append(embedding)
            except Exception as error:
                if is_transient_bedrock_error(error):
                    raise TransientNetworkError(
                        "Bedrock embedding request failed after SDK retries"
                    ) from error
                raise RuntimeError("Bedrock embedding request failed") from error
        return embeddings

    def embed_with_cache(
        self,
        texts: list[str],
        cache: EmbeddingCache,
        *,
        batch_size: int = 64,
    ) -> list[list[float]]:
        results: list[list[float] | None] = [None] * len(texts)
        missing_by_text: dict[str, list[int]] = {}
        for index, text in enumerate(texts):
            cached = cache.get(self.model, self.dimensions, text)
            if cached is not None:
                results[index] = cached
            else:
                missing_by_text.setdefault(text, []).append(index)

        missing_texts = list(missing_by_text)
        for batch in chunks(missing_texts, batch_size):
            for text in batch:
                vector = self.embed_batch([text])[0]
                cache.put(self.model, self.dimensions, text, vector)
                for index in missing_by_text[text]:
                    results[index] = vector
                cache.commit()

        if any(vector is None for vector in results):
            raise RuntimeError("Embedding cache resolution was incomplete")
        return [vector for vector in results if vector is not None]
