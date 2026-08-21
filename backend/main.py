"""
ScannerGreen Backend — WebSocket real-time
Polls RoboBet API and pushes live data to connected clients.
"""

import asyncio
import json
import time
import logging
from typing import Optional

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("scannergreen")

app = FastAPI(title="ScannerGreen Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

API_BASE = "https://m.robobet.app/api"
POLL_INTERVAL = 8          # seconds between full cycles
STATS_POOL_SIZE = 6        # parallel live-stats requests
TODAY_EVERY_N = 3          # fetch /events/today every N cycles

# ── WebSocket manager ──────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        log.info(f"WS connected — {len(self.active)} client(s)")

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
        log.info(f"WS disconnected — {len(self.active)} client(s)")

    async def broadcast(self, data: dict):
        if not self.active:
            return
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

manager = ConnectionManager()

# ── HTTP helpers ───────────────────────────────────────────────────
_client: Optional[httpx.AsyncClient] = None

async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(20.0), follow_redirects=True)
    return _client

async def fetch_json(url: str, retries: int = 1) -> Optional[dict]:
    client = await get_client()
    for attempt in range(retries + 1):
        try:
            r = await client.get(url, headers={"Accept": "application/json"})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt < retries:
                await asyncio.sleep(1.2 * (attempt + 1))
            else:
                log.warning(f"fetch failed {url}: {e}")
    return None

async def fetch_pool(ids: list[str], limit: int, fn) -> dict:
    """Simple concurrency-limited gather."""
    sem = asyncio.Semaphore(limit)
    results = {}

    async def worker(mid: str):
        async with sem:
            try:
                results[mid] = await fn(mid)
            except Exception:
                pass

    await asyncio.gather(*(worker(i) for i in ids))
    return results

# ── State ──────────────────────────────────────────────────────────
state = {
    "matches": {},           # id -> match data (inplay + liveStats)
    "today_forecast": {},    # id -> forecast data
    "finished_scores": {},   # id -> {h, a, home, away}
    "cycle": 0,
    "today_loaded": False,
}

# ── Core polling loop ─────────────────────────────────────────────
async def poll_cycle():
    """Single poll cycle: fetch inplay → live-stats → today → broadcast."""
    try:
        inplay = await fetch_json(f"{API_BASE}/inplay/list.json", retries=2)
        if not inplay:
            return

        events = inplay.get("events", [])
        live = [e for e in events if e and e.get("isLive") and e.get("status") == "live"]
        ids = [str(e["id"]) for e in live]
        now = time.time() * 1000

        # Parallel: live-stats + today overlay
        async def fetch_stats(mid):
            ls = await fetch_json(f"{API_BASE}/events/{mid}/live-stats", retries=0)
            return ls if ls and ls.get("success") else None

        fetch_today = (
            (not state["today_loaded"] or state["cycle"] % TODAY_EVERY_N == 0)
            and fetch_json(f"{API_BASE}/events/today", retries=2)
        ) or asyncio.sleep(0)

        stats, today = await asyncio.gather(
            fetch_pool(ids, STATS_POOL_SIZE, fetch_stats),
            fetch_today,
        )

        if isinstance(today, dict):
            apply_today_overlay(today)
            state["today_loaded"] = True

        # Remove finished matches
        live_set = set(ids)
        for mid in list(state["matches"]):
            if mid not in live_set:
                del state["matches"][mid]

        # Build/update match objects
        for e in live:
            mid = str(e["id"])
            ls = stats.get(mid)
            prev = state["matches"].get(mid)

            m = {
                "id": mid,
                "slug": e.get("slug"),
                "fi_id": e.get("fi_id"),
                "league": (e.get("league") or {}).get("name", "N/D"),
                "home": e.get("home", "—"),
                "away": e.get("away", "—"),
                "scoreHome": e.get("scoreHome") or 0,
                "scoreAway": e.get("scoreAway") or 0,
                "minute": num_or_null(e.get("minute")) or 0,
                "period": e.get("period", ""),
                "time": e.get("time", ""),
                "injuryTime": num_or_null(e.get("injury_time_min")),
                "odds": e.get("odds", []),
                "redH": bool(e.get("redCardHome")),
                "redA": bool(e.get("redCardAway")),
                "hasCornersMarket": bool(e.get("has_corners_market")),
                "liveStats": ls or (prev and prev.get("liveStats")),
                "statsAge": now if ls else (prev.get("statsAge") if prev else None),
                "forecast": (prev.get("forecast") if prev else None) or state["today_forecast"].get(mid),
            }
            state["matches"][mid] = m

        # Broadcast to all WebSocket clients
        await manager.broadcast({
            "type": "tick",
            "matches": state["matches"],
            "finishedScores": state["finished_scores"],
            "cycle": state["cycle"],
            "ts": now,
        })

        state["cycle"] += 1

    except Exception as e:
        log.error(f"poll error: {e}")


def apply_today_overlay(today: dict):
    """Extract forecast data and finished scores from /events/today."""
    now = time.time() * 1000
    for league in today.get("leagues", []):
        for mt in league.get("matches", []):
            mid = str(mt.get("id", ""))
            # Finished scores
            if mt.get("status") == "finished" and mt.get("scoreHome") is not None:
                state["finished_scores"][mid] = {
                    "h": mt["scoreHome"],
                    "a": mt.get("scoreAway"),
                    "home": mt.get("home"),
                    "away": mt.get("away"),
                }
            # Forecast overlay
            fd = mt.get("forecast_data", {})
            mk = fd.get("markets", {})
            if mk.get("over_goals") or mk.get("corners") or mk.get("winner"):
                state["today_forecast"][mid] = {
                    "ts": now,
                    "over_goals": mk.get("over_goals"),
                    "corners": mk.get("corners"),
                    "winner": mk.get("winner"),
                    "double_chance": mk.get("double_chance"),
                    "prematch_xg": fd.get("prematch_xg"),
                }
            # Live score sync
            if mt.get("isLive") and mt.get("scoreHome") is not None:
                m = state["matches"].get(mid)
                if m:
                    m["scoreHome"] = mt["scoreHome"]
                    m["scoreAway"] = mt.get("scoreAway")


def num_or_null(v):
    if v is None:
        return None
    try:
        f = float(v)
        return f if f == f else None  # NaN check
    except (TypeError, ValueError):
        return None

# ── Background poller ──────────────────────────────────────────────
async def poll_loop():
    """Main polling loop — runs forever."""
    log.info("Polling loop started")
    while True:
        t0 = time.monotonic()
        await poll_cycle()
        elapsed = time.monotonic() - t0
        wait = max(0.1, POLL_INTERVAL - elapsed)
        await asyncio.sleep(wait)

@app.on_event("startup")
async def startup():
    asyncio.create_task(poll_loop())

@app.on_event("shutdown")
async def shutdown():
    if _client and not _client.is_closed:
        await _client.aclose()

# ── Endpoints ──────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"ok": True, "clients": len(manager.active), "matches": len(state["matches"])}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    # Send current state immediately
    try:
        await ws.send_text(json.dumps({
            "type": "init",
            "matches": state["matches"],
            "finishedScores": state["finished_scores"],
            "cycle": state["cycle"],
            "ts": time.time() * 1000,
        }, ensure_ascii=False, separators=(",", ":")))
    except Exception:
        pass
    try:
        while True:
            # Keep connection alive; client can send pings
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)
