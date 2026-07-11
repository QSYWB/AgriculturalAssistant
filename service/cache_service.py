"""缓存服务"""
import hashlib, json, time, threading
from pathlib import Path
from typing import Optional, Any
from config.settings import settings
from factory.model_factory import embedding_model
from utils.logger_handler import app_logger
from utils.path_tool import path_tool

class SemanticCache:
    def __init__(self, ttl: Optional[int] = None, threshold: Optional[float] = None):
        self.ttl = ttl or settings.rag_cache_ttl
        self.threshold = threshold or settings.rag_cache_threshold
        self._data: dict[int, tuple] = {}
        self._lock = threading.Lock()

    def get(self, qe: list[float]) -> Optional[Any]:
        if not self._data: return None
        now = time.time()
        with self._lock:
            for key, (emb, result, ts) in list(self._data.items()):
                if now - ts > self.ttl: del self._data[key]; continue
                sim = sum(a*b for a,b in zip(qe, emb)) / (sum(a*a for a in qe)**.5 * sum(b*b for b in emb)**.5 + 1e-10)
                if sim >= self.threshold: return result
        return None

    def set(self, qe: list[float], result: Any) -> None:
        with self._lock:
            self._data[hash(tuple(qe))] = (qe, result, time.time())


class LLMResponseCache:
    def __init__(self, ttl: Optional[int] = None, enabled: Optional[bool] = None):
        self.ttl = ttl or settings.llm_cache_ttl
        self.enabled = enabled if enabled is not None else settings.llm_cache_enabled
        self._path = path_tool.get_cache_dir() / "llm_cache.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._cache: dict = {}
        self._load()

    def get(self, query: str, context: str = "") -> Optional[str]:
        if not self.enabled: return None
        key = hashlib.md5((query + "|" + context).strip().lower().encode()).hexdigest()
        with self._lock:
            entry = self._cache.get(key)
            if entry and time.time() - entry["ts"] < self.ttl: return entry["response"]
        return None

    def set(self, query: str, response: str, context: str = "") -> None:
        if not self.enabled: return
        key = hashlib.md5((query + "|" + context).strip().lower().encode()).hexdigest()
        with self._lock:
            self._cache[key] = {"response": response, "ts": time.time()}
            self._save()

    def _load(self):
        try:
            if self._path.exists(): self._cache = json.loads(self._path.read_text(encoding="utf-8"))
        except: self._cache = {}

    def _save(self):
        try: self._path.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2), encoding="utf-8")
        except: pass

semantic_cache = SemanticCache()
llm_cache = LLMResponseCache()

