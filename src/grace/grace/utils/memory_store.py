"""
grace_agi/utils/memory_store.py
Simple JSON-file-backed key-value / list store for persistent memory.
Thread-safe for single-process use.
"""
import json
import os
import threading
import time
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Append-only list store backed by a JSON file.
    Entries are dicts.  Older entries are trimmed when max_entries is exceeded.

    Usage
    -----
    store = MemoryStore("/home/grace/memory/episodic.json", max_entries=500)
    store.append({"content": "Saw a robin", "timestamp": 1234567890.0})
    recent = store.tail(10)
    matches = store.search("robin")
    """

    def __init__(self, path: str, max_entries: int = 500):
        self.path = path
        self.max_entries = max_entries
        self._lock = threading.Lock()
        self._data: list[dict] = []
        self._load()

    # ── Public ────────────────────────────────────────────────────────────────

    def append(self, entry: dict) -> None:
        entry.setdefault("timestamp", time.time())
        with self._lock:
            self._data.append(entry)
            if len(self._data) > self.max_entries:
                self._data = self._data[-self.max_entries:]
            self._save()

    def tail(self, n: int = 10) -> list[dict]:
        with self._lock:
            return list(self._data[-n:])

    def all(self) -> list[dict]:
        with self._lock:
            return list(self._data)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Naive substring search — good enough on Jetson without a vector DB."""
        q = query.lower()
        with self._lock:
            hits = [e for e in self._data if q in json.dumps(e).lower()]
        return hits[-top_k:]

    def clear(self) -> None:
        with self._lock:
            self._data = []
            self._save()

    # ── KV accessors (stored as {"_kv": {key: value}}) ───────────────────────

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            kv = self._kv()
            kv[key] = value
            self._set_kv(kv)
            self._save()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._kv().get(key, default)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _kv(self) -> dict:
        for entry in self._data:
            if "_kv" in entry:
                return entry["_kv"]
        return {}

    def _set_kv(self, kv: dict) -> None:
        for entry in self._data:
            if "_kv" in entry:
                entry["_kv"] = kv
                return
        self._data.insert(0, {"_kv": kv})

    def _load(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    self._data = json.load(f)
                logger.info(f"MemoryStore: loaded {len(self._data)} entries from {self.path}")
            except Exception as exc:
                logger.warning(f"MemoryStore: could not load {self.path}: {exc}")
                self._data = []
        else:
            self._data = []

    def _save(self) -> None:
        try:
            tmp = self.path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self._data, f, indent=2)
            os.replace(tmp, self.path)
        except Exception as exc:
            logger.error(f"MemoryStore: save failed: {exc}")
