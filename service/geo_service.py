"""地理编码服务"""
import time, json, threading
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from utils.logger_handler import app_logger

NOM_URL = "https://nominatim.openstreetmap.org/reverse"
IP_API = "http://ip-api.com/json/{}?fields=city,regionName,country&lang=zh"

class GeoService:
    def __init__(self):
        self._cache = {}
        self._last_query = 0.0
        self._lock = threading.Lock()

    def reverse_geocode(self, lat: float, lng: float) -> str:
        key = f"{lat:.4f},{lng:.4f}"
        with self._lock:
            if key in self._cache: return self._cache[key]
        now = time.time()
        if now - self._last_query < 1.1: time.sleep(1.1 - (now - self._last_query))
        try:
            params = urlencode({"format":"json","lat":str(lat),"lon":str(lng),"zoom":10,"accept-language":"zh"})
            req = Request(f"{NOM_URL}?{params}", headers={"User-Agent":"AgriculturalAssistant/1.0"})
            with urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode("utf-8"))
                self._last_query = time.time()
            addr = data.get("address", {})
            parts = [p for p in [addr.get("state",""), addr.get("city","") or addr.get("town","") or addr.get("village","")] if p]
            result = " ".join(parts) or data.get("display_name","")[:50]
            with self._lock: self._cache[key] = result
            return result
        except Exception as e:
            app_logger.warning(f"[Geo] 解析失败: {e}")
            self._last_query = time.time()
            return ""

    def ip_geolocation(self, ip: str) -> str:
        if not ip or ip in ("127.0.0.1","::1","localhost"): return ""
        with self._lock:
            if ip in self._cache: return self._cache[ip]
        try:
            req = Request(IP_API.format(ip), headers={"User-Agent":"AgriculturalAssistant/1.0"})
            with urlopen(req, timeout=3) as r:
                d = json.loads(r.read().decode("utf-8"))
            parts = [p for p in [d.get("country",""), d.get("regionName",""), d.get("city","")] if p]
            result = " ".join(parts)
            with self._lock: self._cache[ip] = result
            return result
        except Exception as e:
            app_logger.warning(f"[Geo] IP解析失败: {e}")
            return ""

geo_service = GeoService()
