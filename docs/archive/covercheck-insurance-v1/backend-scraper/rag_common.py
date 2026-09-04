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


OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"


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

    def __init__(self, url: str, service_key: str, *, timeout: int = 120) -> None:
        self.rest_url = url.rstrip("/") + "/rest/v1"
        self.service_key = service_key
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: Any = None,
        prefer: str | None = None,
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
        request = urllib.request.Request(url, data=encoded, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            raise RuntimeError(error_message(payload, exc.code, "Supabase")) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Supabase request failed: {exc}") from exc
        if not payload:
            return None
        return json.loads(payload.decode("utf-8"))

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
        result = self.request("POST", table, body=rows, prefer="return=representation")
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


class OpenAIEmbeddings:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        timeout: int = 120,
        max_attempts: int = 5,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions
        self.timeout = timeout
        self.max_attempts = max_attempts

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        body = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
            "dimensions": self.dimensions,
        }
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        retryable = {408, 409, 429, 500, 502, 503, 504}
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            request = urllib.request.Request(
                OPENAI_EMBEDDINGS_URL,
                data=encoded,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "sn-hackathon-insurance-rag/1.0",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
                ordered = sorted(result["data"], key=lambda item: item["index"])
                embeddings = [item["embedding"] for item in ordered]
                if len(embeddings) != len(texts):
                    raise RuntimeError("OpenAI returned a different number of embeddings than inputs")
                if any(len(vector) != self.dimensions for vector in embeddings):
                    raise RuntimeError(f"OpenAI embedding dimension did not match {self.dimensions}")
                return embeddings
            except urllib.error.HTTPError as exc:
                payload = exc.read()
                last_error = RuntimeError(error_message(payload, exc.code, "OpenAI"))
                if exc.code not in retryable or attempt == self.max_attempts:
                    raise last_error
            except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, RuntimeError) as exc:
                last_error = exc
                if attempt == self.max_attempts:
                    raise
            time.sleep(min(30.0, 2 ** (attempt - 1) + random.random()))
        raise RuntimeError(str(last_error or "OpenAI embedding request failed"))

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
            vectors = self.embed_batch(batch)
            for text, vector in zip(batch, vectors):
                cache.put(self.model, self.dimensions, text, vector)
                for index in missing_by_text[text]:
                    results[index] = vector
            cache.commit()

        if any(vector is None for vector in results):
            raise RuntimeError("Embedding cache resolution was incomplete")
        return [vector for vector in results if vector is not None]
