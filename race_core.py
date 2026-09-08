"""
race_core.py — engine-room for Turbo Racing League.

Pure standard library (plus optional `qrcode` for the invite QR image).
Nothing here imports Streamlit, so it can be unit-tested or reused headless.

Provides:
  * A JSON-file persistent leaderboard (players.json) that survives restarts.
  * A tiny threaded HTTP/JSON API used by the in-browser game for
    real-time multiplayer room sync and for saving race results.
  * Room management with automatic pruning of disconnected drivers.
  * Helpers for LAN IP detection and QR-code invite generation.
"""

from __future__ import annotations

import json
import os
import random
import socket
import string
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Player records live in a plain JSON file so they are easy to read, edit,
# back up, sync or check into version control.
DATA_PATH = os.environ.get("RACE_DATA_PATH", os.path.join(APP_DIR, "players.json"))

# How long a driver can go silent before we drop them from a room (seconds).
PLAYER_TIMEOUT = 12.0
ROOM_TIMEOUT = 900.0
MAX_HISTORY = 500

CAR_COLORS = [
    "#ef4444", "#3b82f6", "#22c55e", "#f59e0b",
    "#a855f7", "#06b6d4", "#ec4899", "#84cc16",
]


# --------------------------------------------------------------------------
# Leaderboard storage (JSON file)
# --------------------------------------------------------------------------
class Leaderboard:
    """Thread-safe JSON-file leaderboard.

    Layout of players.json::

        {
          "version": 2,
          "updated": 1757200000.0,
          "drivers": {"Amna": {"name": ..., "wins": 2, "points": 940, ...}},
          "races":   [{"ts":..., "driver":..., "position":..., ...}, ...]
        }

    Every finished race is flushed to disk immediately (atomic replace), so
    results survive page refreshes, reruns and restarts.
    """

    def __init__(self, path: str = DATA_PATH):
        self.path = path
        self._lock = threading.Lock()
        self.data: Dict[str, Any] = {"version": 2, "updated": 0.0, "drivers": {}, "races": []}
        self._load()

    # -- disk --------------------------------------------------------------
    def _load(self) -> None:
        with self._lock:
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                if isinstance(raw, dict) and isinstance(raw.get("drivers"), dict):
                    self.data = {
                        "version": raw.get("version", 2),
                        "updated": raw.get("updated", 0.0),
                        "drivers": raw["drivers"],
                        "races": raw.get("races", []),
                    }
                elif isinstance(raw, list):  # tolerate a bare list of drivers
                    self.data["drivers"] = {d.get("name", "?"): d for d in raw}
            except FileNotFoundError:
                self._flush()
            except Exception:
                # Corrupt file: keep a copy rather than silently losing history.
                try:
                    os.replace(self.path, self.path + ".broken")
                except Exception:
                    pass
                self._flush()

    def _flush(self) -> None:
        """Atomic write — never leaves a half-written players.json behind."""
        self.data["updated"] = time.time()
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        except Exception:
            pass

    def reload(self) -> None:
        """Re-read the file (useful if another process edited it)."""
        self._load()

    # -- writes ------------------------------------------------------------
    def record_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Record one driver's finish and persist. Returns the driver record."""
        name = str(result.get("driver", "") or "Anonymous").strip()[:24] or "Anonymous"
        position = int(result.get("position", 1) or 1)
        field = max(1, int(result.get("field", 1) or 1))
        total_time = _as_float(result.get("total_time"))
        best_lap = _as_float(result.get("best_lap"))
        laps = int(result.get("laps", 0) or 0)
        track = int(result.get("track", 1) or 1)
        power = max(1, min(5, int(result.get("power", 3) or 3)))
        top_speed = _as_float(result.get("top_speed")) or 0.0
        crashes = int(result.get("crashes", 0) or 0)
        room = str(result.get("room", "") or "")[:12]

        # Formula-style points: 1st gets the most, scaled by engine class,
        # with a win bonus so taking the flag always beats a safe second.
        base = max(0, field - position + 1)
        points = int((base * 40 + (60 if position == 1 else 0)) * (0.6 + 0.2 * power))
        won = 1 if position == 1 else 0
        now = time.time()

        with self._lock:
            drivers = self.data["drivers"]
            d = drivers.get(name)
            if d is None:
                d = {"name": name, "wins": 0, "races": 0, "points": 0,
                     "best_time": None, "best_lap": None, "top_speed": 0.0,
                     "crashes": 0, "first_seen": now, "last_seen": now}
                drivers[name] = d
            d["wins"] = int(d.get("wins", 0)) + won
            d["races"] = int(d.get("races", 0)) + 1
            d["points"] = int(d.get("points", 0)) + points
            d["best_time"] = _better(d.get("best_time"), total_time)
            d["best_lap"] = _better(d.get("best_lap"), best_lap)
            d["top_speed"] = max(float(d.get("top_speed") or 0), top_speed)
            d["crashes"] = int(d.get("crashes", 0)) + crashes
            d["last_seen"] = now

            self.data["races"].append({
                "ts": now, "driver": name, "position": position, "field": field,
                "total_time": total_time, "best_lap": best_lap, "laps": laps,
                "track": track, "power": power, "room": room,
            })
            if len(self.data["races"]) > MAX_HISTORY:
                self.data["races"] = self.data["races"][-MAX_HISTORY:]
            self._flush()
            return dict(d)

    def touch_driver(self, name: str, room: str = "") -> Dict[str, Any]:
        """Register a player as soon as they enter a lobby, before any race."""
        name = str(name or "").strip()[:24] or "Anonymous"
        now = time.time()
        with self._lock:
            d = self.data["drivers"].get(name)
            if d is None:
                d = {"name": name, "wins": 0, "races": 0, "points": 0,
                     "best_time": None, "best_lap": None, "top_speed": 0.0,
                     "crashes": 0, "first_seen": now, "last_seen": now}
                self.data["drivers"][name] = d
                self._flush()
            else:
                d["last_seen"] = now
            if room:
                d["last_room"] = room
            return dict(d)

    def reset(self) -> None:
        with self._lock:
            self.data["drivers"] = {}
            self.data["races"] = []
            self._flush()

    def delete_driver(self, name: str) -> None:
        with self._lock:
            self.data["drivers"].pop(name, None)
            self.data["races"] = [r for r in self.data["races"] if r.get("driver") != name]
            self._flush()

    # -- reads -------------------------------------------------------------
    def standings(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            rows = [dict(d) for d in self.data["drivers"].values()]
        rows.sort(key=lambda d: (-int(d.get("points", 0)), -int(d.get("wins", 0)),
                                 d.get("best_time") if d.get("best_time") is not None else 1e9))
        out = []
        for i, d in enumerate(rows[:limit], start=1):
            d["rank"] = i
            races = int(d.get("races", 0))
            d["win_rate"] = round(100.0 * int(d.get("wins", 0)) / races, 1) if races else 0.0
            out.append(d)
        return out

    def driver(self, name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            d = self.data["drivers"].get(name)
            return dict(d) if d else None

    def recent_races(self, limit: int = 25) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(r) for r in reversed(self.data["races"][-limit:])]

    def export_json(self) -> str:
        with self._lock:
            return json.dumps(self.data, indent=2, ensure_ascii=False)


def _as_float(v: Any) -> Optional[float]:
    try:
        f = float(v)
        if f != f or f in (float("inf"), float("-inf")):  # NaN / inf guard
            return None
        return round(f, 3)
    except (TypeError, ValueError):
        return None


def _better(old: Optional[float], new: Optional[float]) -> Optional[float]:
    """Smaller (faster) wins; either side may be missing."""
    if new is None:
        return old
    if old is None:
        return new
    return min(old, new)


# --------------------------------------------------------------------------
# Multiplayer rooms
# --------------------------------------------------------------------------
class RoomManager:
    """In-memory room registry. Small, fast, and good enough for a LAN party:
    each browser POSTs its car state ~12x/sec and gets everyone else back."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.rooms: Dict[str, Dict[str, Any]] = {}

    def join(self, room: str, name: str, pid: Optional[str] = None,
             config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        room = normalize_room(room)
        now = time.time()
        with self._lock:
            r = self.rooms.setdefault(
                room,
                {"created": now, "start_at": 0.0, "players": {}, "config": config or {},
                 "results": []},
            )
            self._prune(r, now)
            if not pid or pid not in r["players"]:
                pid = pid or _rand_id()
                used = {p["slot"] for p in r["players"].values()}
                slot = next((i for i in range(len(CAR_COLORS)) if i not in used), len(r["players"]))
                r["players"][pid] = {
                    "pid": pid, "name": name[:20] or "Driver", "slot": slot,
                    "color": CAR_COLORS[slot % len(CAR_COLORS)],
                    "x": 0.0, "z": 0.0, "angle": 0.0, "speed": 0.0,
                    "lap": 0, "progress": 0.0, "finished": False, "time": 0.0,
                    "ready": False, "seen": now, "joined": now,
                }
            else:
                r["players"][pid]["name"] = name[:20] or "Driver"
                r["players"][pid]["seen"] = now
            if config and not r["config"]:
                r["config"] = config
            return {"room": room, "pid": pid, "player": dict(r["players"][pid]),
                    "config": r["config"], "start_at": r["start_at"]}

    def update(self, room: str, pid: str, state: Dict[str, Any]) -> Dict[str, Any]:
        room = normalize_room(room)
        now = time.time()
        with self._lock:
            r = self.rooms.get(room)
            if r is None:
                return {"error": "no_room", "players": [], "start_at": 0.0}
            self._prune(r, now)
            p = r["players"].get(pid)
            if p is None:
                return {"error": "not_joined", "players": [], "start_at": 0.0}
            for key in ("x", "z", "angle", "speed", "progress", "time"):
                if key in state:
                    p[key] = _as_float(state[key]) or 0.0
            if "lap" in state:
                p["lap"] = int(state["lap"] or 0)
            for key in ("finished", "ready"):
                if key in state:
                    p[key] = bool(state[key])
            p["seen"] = now
            # First driver to hit GO schedules the start for everybody.
            if state.get("start") and not r["start_at"]:
                r["start_at"] = now + float(state.get("start_delay", 3.0))
            if state.get("reset_start"):
                r["start_at"] = 0.0
            return {
                "room": room,
                "start_at": r["start_at"],
                "now": now,
                "config": r["config"],
                "players": [dict(v) for v in r["players"].values()],
            }

    def state(self, room: str) -> Dict[str, Any]:
        room = normalize_room(room)
        now = time.time()
        with self._lock:
            r = self.rooms.get(room)
            if r is None:
                return {"room": room, "players": [], "start_at": 0.0, "now": now}
            self._prune(r, now)
            return {
                "room": room, "start_at": r["start_at"], "now": now,
                "config": r["config"],
                "players": [dict(v) for v in r["players"].values()],
            }

    def set_config(self, room: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Pin the circuit, lap count and engine class for a whole room, so
        everyone who joins races the same event rather than their own."""
        room = normalize_room(room)
        now = time.time()
        with self._lock:
            r = self.rooms.setdefault(
                room, {"created": now, "start_at": 0.0, "players": {}, "config": {},
                       "results": []})
            r["config"] = dict(config or {})
            return dict(r["config"])

    def get_config(self, room: str) -> Dict[str, Any]:
        with self._lock:
            r = self.rooms.get(normalize_room(room))
            return dict(r["config"]) if r else {}

    def leave(self, room: str, pid: str) -> None:
        with self._lock:
            r = self.rooms.get(normalize_room(room))
            if r:
                r["players"].pop(pid, None)

    def _prune(self, room: Dict[str, Any], now: float) -> None:
        dead = [pid for pid, p in room["players"].items() if now - p["seen"] > PLAYER_TIMEOUT]
        for pid in dead:
            room["players"].pop(pid, None)
        if not room["players"] and now - room["created"] > 30:
            room["start_at"] = 0.0
        # Drop whole rooms that have been empty for a while.
        stale = [k for k, v in self.rooms.items()
                 if not v["players"] and now - v["created"] > ROOM_TIMEOUT]
        for k in stale:
            self.rooms.pop(k, None)


def normalize_room(room: Any) -> str:
    s = "".join(ch for ch in str(room or "").upper() if ch.isalnum())[:8]
    return s or "LOBBY"


def new_room_code(n: int = 5) -> str:
    # Ambiguity-free alphabet (no O/0/I/1) so codes are easy to read aloud.
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(n))


def _rand_id() -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))


# --------------------------------------------------------------------------
# Standalone play pages
# --------------------------------------------------------------------------
class ConfigStore:
    """Holds race settings so the game can open as its own page.

    Streamlit embeds components in a sandboxed iframe, which blocks the
    Fullscreen API outright. Serving the game at its own URL sidesteps that
    entirely: a top-level page can go fullscreen, lock orientation and use the
    whole screen. The Streamlit page hands settings over by token rather than
    stuffing them (including an uploaded soundtrack) into the URL.
    """

    def __init__(self, ttl: float = 12 * 3600, limit: int = 200):
        self.ttl = ttl
        self.limit = limit
        self._lock = threading.Lock()
        self._items: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def put(self, cfg: Dict[str, Any], token: Optional[str] = None) -> str:
        token = token or _rand_id()
        with self._lock:
            self._items[token] = (time.time(), dict(cfg))
            self._prune()
        return token

    def get(self, token: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            item = self._items.get(str(token))
            return dict(item[1]) if item else None

    def _prune(self) -> None:
        now = time.time()
        for k in [k for k, (t, _) in self._items.items() if now - t > self.ttl]:
            self._items.pop(k, None)
        while len(self._items) > self.limit:
            oldest = min(self._items, key=lambda k: self._items[k][0])
            self._items.pop(oldest, None)


def render_play_page(configs: "ConfigStore", query: Dict[str, str]) -> Tuple[int, str, bytes]:
    """Full HTML document for the standalone player."""
    try:
        from game_html import build_game_html
    except Exception:
        return 500, "text/plain", b"game_html module not importable"
    cfg = configs.get(query.get("c", "")) or {}
    if not cfg:
        return 404, "text/html", (
            "<!doctype html><meta charset=utf-8><style>body{background:#070c18;"
            "color:#e8eefc;font-family:system-ui;display:flex;height:100vh;margin:0;"
            "align-items:center;justify-content:center;text-align:center}</style>"
            "<div><h2>This race link has expired</h2>"
            "<p>Go back to the app and press <b>Play fullscreen</b> again.</p></div>"
        ).encode("utf-8")
    cfg = dict(cfg)
    cfg["standalone"] = True
    return 200, "text/html", build_game_html(cfg).encode("utf-8")


# --------------------------------------------------------------------------
# Request handling (shared by the standalone server and the Streamlit mount)
# --------------------------------------------------------------------------
def handle_request(board: "Leaderboard", rooms: "RoomManager", method: str,
                   path: str, query: Dict[str, str],
                   data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """One place that answers every API call, whichever server received it."""
    path = "/" + path.strip("/").split("/")[-1] if path else "/"
    try:
        if method == "GET":
            if path == "/ping":
                return 200, {"ok": True, "t": time.time()}
            if path == "/state":
                return 200, rooms.state(query.get("room", "LOBBY"))
            if path == "/leaderboard":
                return 200, {"standings": board.standings(int(query.get("limit", 50)))}
            return 404, {"error": "not_found"}

        if path == "/join":
            return 200, rooms.join(data.get("room", "LOBBY"), str(data.get("name", "Driver")),
                                   data.get("pid"), data.get("config"))
        if path == "/pos":
            return 200, rooms.update(data.get("room", "LOBBY"), str(data.get("pid", "")), data)
        if path == "/leave":
            rooms.leave(data.get("room", "LOBBY"), str(data.get("pid", "")))
            return 200, {"ok": True}
        if path == "/hello":
            return 200, {"ok": True, "driver": board.touch_driver(
                str(data.get("name", "")), str(data.get("room", "")))}
        if path == "/result":
            return 200, {"ok": True, "driver": board.record_result(data)}
        return 404, {"error": "not_found"}
    except Exception as exc:                      # never drop the game's connection
        return 500, {"error": str(exc)}


# --------------------------------------------------------------------------
# Standalone HTTP API (fallback when the Streamlit mount is unavailable)
# --------------------------------------------------------------------------
class _Handler(BaseHTTPRequestHandler):
    server_version = "TurboRacing/4.0"
    board: "Leaderboard"
    rooms: "RoomManager"
    configs: "ConfigStore"

    def log_message(self, fmt, *args):            # keep Streamlit's console readable
        pass

    def _send(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> Dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0:
                return {}
            data = json.loads(self.rfile.read(min(length, 64_000)).decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def do_OPTIONS(self):  # noqa: N802
        self._send({"ok": True})

    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path.rstrip("/").endswith("/play"):
            status, ctype, body = render_play_page(self.configs, q)
            self.send_response(status)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return
        status, payload = handle_request(self.board, self.rooms, "GET", u.path, q, {})
        self._send(payload, status)

    def do_POST(self):  # noqa: N802
        u = urlparse(self.path)
        status, payload = handle_request(self.board, self.rooms, "POST", u.path, {}, self._body())
        self._send(payload, status)


class GameServer:
    """Background API server. One per Streamlit process."""

    def __init__(self, board: Leaderboard, rooms: RoomManager, port: int = 0,
                 host: str = "0.0.0.0", configs: Optional["ConfigStore"] = None):
        self.configs = configs or ConfigStore()
        handler = type("Handler", (_Handler,), {"board": board, "rooms": rooms,
                                                "configs": self.configs})
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever,
                                       name="race-api", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        try:
            self.httpd.shutdown()
        except Exception:
            pass


def start_server(port: int = 0) -> Tuple[GameServer, Leaderboard, RoomManager]:
    board = Leaderboard()
    rooms = RoomManager()
    return GameServer(board, rooms, port=port), board, rooms


# --------------------------------------------------------------------------
# Mounting the API inside Streamlit's own web server
# --------------------------------------------------------------------------
# Sharing Streamlit's port matters a lot in practice: players on phones then
# need exactly one open port (8501), the API is same-origin so HTTPS
# deployments don't trip mixed-content blocking, and one firewall rule covers
# everything.  If the internals ever move, we fall back to the extra port.
API_PREFIX = "/racing/api"


def attach_to_streamlit(board: Leaderboard, rooms: RoomManager,
                        prefix: str = API_PREFIX,
                        configs: Optional["ConfigStore"] = None) -> bool:
    """Add the racing API to the Tornado app Streamlit is already running.

    Best-effort by design: this reaches into another library's internals, so
    every step is guarded and any failure just means the game falls back to the
    standalone API port. It must never take the app down with it.
    """
    try:
        return _attach_to_streamlit(board, rooms, prefix, configs)
    except Exception:
        return False


def _attach_to_streamlit(board: Leaderboard, rooms: RoomManager, prefix: str,
                         configs: Optional["ConfigStore"] = None) -> bool:
    try:
        import gc

        import tornado.web
    except Exception:
        return False

    # Some objects on the heap raise from __class__ lookups, so isinstance()
    # gets its own guard rather than being trusted inside a comprehension.
    apps = []
    for obj in gc.get_objects():
        try:
            if isinstance(obj, tornado.web.Application):
                apps.append(obj)
        except Exception:
            continue
    if not apps:
        return False

    class RacingHandler(tornado.web.RequestHandler):  # type: ignore[misc]
        def initialize(self, board, rooms):           # noqa: A002
            self.board, self.rooms = board, rooms

        def set_default_headers(self):
            self.set_header("Content-Type", "application/json")
            self.set_header("Access-Control-Allow-Origin", "*")
            self.set_header("Access-Control-Allow-Headers", "Content-Type")
            self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.set_header("Cache-Control", "no-store")

        def check_xsrf_cookie(self):                  # game client, not a form post
            return

        def options(self, *a):
            self.finish(json.dumps({"ok": True}))

        def _run(self, method, endpoint):
            query = {}
            for k, v in self.request.query_arguments.items():
                key = k.decode() if isinstance(k, bytes) else k
                val = v[0] if v else b""
                query[key] = val.decode() if isinstance(val, bytes) else str(val)
            data = {}
            if method == "POST" and self.request.body:
                try:
                    parsed = json.loads(self.request.body.decode("utf-8"))
                    data = parsed if isinstance(parsed, dict) else {}
                except Exception:
                    data = {}
            status, payload = handle_request(self.board, self.rooms, method,
                                             endpoint, query, data)
            self.set_status(status)
            self.finish(json.dumps(payload))

        def get(self, endpoint):
            self._run("GET", endpoint)

        def post(self, endpoint):
            self._run("POST", endpoint)

    class PlayHandler(tornado.web.RequestHandler):  # type: ignore[misc]
        def initialize(self, configs):
            self.configs = configs

        def check_xsrf_cookie(self):
            return

        def get(self):
            query = {}
            for k, v in self.request.query_arguments.items():
                key = k.decode() if isinstance(k, bytes) else k
                val = v[0] if v else b""
                query[key] = val.decode() if isinstance(val, bytes) else str(val)
            status, ctype, body = render_play_page(self.configs, query)
            self.set_status(status)
            self.set_header("Content-Type", ctype + "; charset=utf-8")
            self.set_header("Cache-Control", "no-store")
            self.finish(body)

    root = prefix.rstrip("/").rsplit("/", 1)[0] or "/racing"
    specs = [
        (prefix.rstrip("/") + r"/(\w+)", RacingHandler, {"board": board, "rooms": rooms}),
        (root + r"/play", PlayHandler, {"configs": configs or ConfigStore()}),
    ]
    ok = False
    for app in apps:
        try:
            app.add_handlers(r".*$", specs)
            ok = True
        except Exception:
            continue
    return ok


# --------------------------------------------------------------------------
# Networking / QR helpers
# --------------------------------------------------------------------------
def lan_ip() -> str:
    """Best-effort local network address so phones on the same Wi-Fi can join."""
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.3)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"
    finally:
        if s:
            s.close()


def lan_ip_candidates() -> List[str]:
    """Every plausible address other devices could use to reach this machine.

    Picking the wrong one is the usual reason a QR code "does not work": the
    default route can point at a VPN or a virtual adapter the phone can't see.
    """
    found: List[str] = []

    def add(ip: str) -> None:
        if (ip and ip not in found and not ip.startswith("127.")
                and not ip.startswith("169.254.")):
            found.append(ip)

    add(lan_ip())
    try:
        host = socket.gethostname()
        for info in socket.getaddrinfo(host, None, socket.AF_INET):
            add(info[4][0])
    except Exception:
        pass
    try:  # Linux/macOS: read the interface list directly
        import subprocess
        out = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=2)
        for ip in out.stdout.split():
            add(ip)
    except Exception:
        pass
    # Home/office networks first — those are the ones a phone shares.
    found.sort(key=lambda ip: 0 if ip.startswith(("192.168.", "10.", "172.")) else 1)
    return found or ["127.0.0.1"]


def port_reachable(host: str, port: int, timeout: float = 1.2) -> bool:
    """Can something actually connect to host:port from outside localhost?"""
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


def qr_png_bytes(text: str, scale: int = 8) -> Optional[bytes]:
    """QR image bytes for the invite link, or None if `qrcode` isn't installed."""
    try:
        import io

        import qrcode  # type: ignore

        img = qrcode.make(text)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


def qr_ascii(text: str) -> Optional[str]:
    try:
        import io

        import qrcode  # type: ignore

        qr = qrcode.QRCode(border=1)
        qr.add_data(text)
        qr.make(fit=True)
        buf = io.StringIO()
        qr.print_ascii(out=buf, invert=True)
        return buf.getvalue()
    except Exception:
        return None


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    srv, lb, rm = start_server(port=8765)
    print(f"API on http://{lan_ip()}:{srv.port}  data -> {DATA_PATH}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        srv.stop()
