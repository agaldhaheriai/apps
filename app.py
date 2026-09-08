"""
Turbo Racing League — Streamlit front end.

    pip install -r requirements.txt
    streamlit run app.py

Deliberately spare: race settings on the left, the game in the middle, the
league table on the right. Anything technical (invite troubleshooting, league
file management) is tucked into a collapsed expander so it stays out of the way
while people are playing.
"""

from __future__ import annotations

import base64
import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import race_core as core
from game_html import build_game_html

st.set_page_config(page_title="Turbo Racing League", page_icon="🏎️", layout="wide")

API_PORT = int(os.environ.get("RACE_API_PORT", "8765"))

PAINTS = {
    "Race red": 0xEF4444, "Electric blue": 0x3B82F6, "Circuit green": 0x22C55E,
    "Sunset amber": 0xF59E0B, "Ultraviolet": 0xA855F7, "Cyan": 0x06B6D4,
    "Hot pink": 0xEC4899, "Lime": 0x84CC16, "Gunmetal": 0x64748B,
    "Pearl white": 0xE2E8F0, "Midnight": 0x1E293B, "Gold": 0xEAB308,
}
CIRCUITS = {1: "Sunset Oval · easy", 2: "Harbour Sweep · technical",
            3: "Grand Circuit · hard"}


CORE_NEEDED = 4          # race_core.VERSION this file expects


@st.cache_resource(show_spinner=False)
def services():
    """Start the league store, room manager and race server.

    Written to tolerate a half-updated install: if race_core.py is older than
    this file expects, the app drops the features that need it and says so,
    rather than dying with a traceback.
    """
    board = core.Leaderboard()
    rooms = core.RoomManager()

    maker = getattr(core, "ConfigStore", None)
    configs = maker() if maker else None

    mounted = False
    try:
        mounted = (core.attach_to_streamlit(board, rooms, configs=configs) if configs
                   else core.attach_to_streamlit(board, rooms))
    except TypeError:                       # older signature without `configs`
        try:
            mounted = core.attach_to_streamlit(board, rooms)
        except Exception:
            mounted = False
    except Exception:
        mounted = False

    server = None
    for port in (API_PORT, 0):
        try:
            server = (core.GameServer(board, rooms, port=port, configs=configs) if configs
                      else core.GameServer(board, rooms, port=port))
            break
        except TypeError:
            try:
                server = core.GameServer(board, rooms, port=port)
                break
            except Exception:
                continue
        except Exception:
            continue
    return server, board, rooms, mounted, configs


server, board, rooms, mounted, configs = services()
api_port = server.port if server else None
core_version = getattr(core, "VERSION", 0)

if core_version < CORE_NEEDED:
    st.warning(
        "**Some files are out of date.** `race_core.py` is older than `app.py` expects, "
        "so the fullscreen play page is switched off. Copy **app.py, race_core.py and "
        "game_html.py** from the same download into the same folder and redeploy — "
        "they are a set.")

st.markdown(
    """
<style>
  .stApp {background:linear-gradient(180deg,#070c18 0%,#0d1526 55%,#070c18 100%);}
  html,body,[class*="css"],.stMarkdown,h1,h2,h3,h4,p,span,label{color:#e8eefc}
  header[data-testid="stHeader"]{background:transparent}
  .block-container{padding-top:2.2rem;padding-bottom:1rem}
  div[data-testid="stMetricValue"]{color:#38bdf8;font-size:1.5rem}
  div[data-testid="stMetricLabel"]{color:#8fa6cf}
  section[data-testid="stSidebar"]{background:#0a1122;border-right:1px solid rgba(120,160,255,.2)}
  .stButton>button{border:1px solid rgba(120,160,255,.3);background:rgba(56,189,248,.12);
        color:#e8eefc;font-weight:600}
  .stButton>button:hover{background:rgba(56,189,248,.28);color:#fff}
  .code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:30px;font-weight:800;
        letter-spacing:9px;color:#fbbf24;background:rgba(251,191,36,.1);
        border:1px dashed rgba(251,191,36,.55);border-radius:12px;padding:9px 4px 9px 13px;
        display:block;text-align:center}
  .lobbycard{background:rgba(15,23,42,.75);border:1px solid rgba(120,160,255,.25);
        border-radius:16px;padding:18px 20px;height:100%}
  .lobbycard h4{margin:0 0 6px;font-size:16px}
  .lobbycard p{color:#9fb3d9;font-size:13px;margin:0 0 12px;line-height:1.5}
  a.playbtn{display:block;text-align:center;text-decoration:none;font-weight:800;
        font-size:19px;letter-spacing:.06em;color:#04121f;padding:15px 20px;
        border-radius:14px;background:linear-gradient(135deg,#34d399,#22d3ee);
        box-shadow:0 10px 30px rgba(34,211,238,.28);margin-bottom:10px}
  a.playbtn:hover{filter:brightness(1.08)}
  .league{width:100%;border-collapse:separate;border-spacing:0 4px;font-size:13px}
  .league th{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:#7e93bb;
        font-weight:700;padding:0 10px 6px;text-align:left}
  .league th.r,.league td.r{text-align:right}
  .league td{background:rgba(19,28,50,.72);padding:9px 10px;
        border-top:1px solid rgba(120,160,255,.12);
        border-bottom:1px solid rgba(120,160,255,.12);
        font-variant-numeric:tabular-nums}
  .league td:first-child{border-left:1px solid rgba(120,160,255,.12);
        border-radius:10px 0 0 10px}
  .league td:last-child{border-right:1px solid rgba(120,160,255,.12);
        border-radius:0 10px 10px 0}
  .league tr.me td{background:rgba(56,189,248,.15);border-color:rgba(56,189,248,.45)}
  .rank{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;
        border-radius:7px;font-weight:800;font-size:12px;color:#0b1220;
        background:rgba(148,163,184,.55)}
  .rank.g1{background:linear-gradient(135deg,#fde68a,#f59e0b)}
  .rank.g2{background:linear-gradient(135deg,#e2e8f0,#94a3b8)}
  .rank.g3{background:linear-gradient(135deg,#fdba74,#c2703a)}
  .drv{font-weight:700;color:#fff}
  .sub{color:#8fa6cf;font-size:11px}
  .ptbar{height:4px;border-radius:3px;background:rgba(255,255,255,.1);margin-top:5px}
  .ptbar span{display:block;height:100%;border-radius:3px;
        background:linear-gradient(90deg,#22d3ee,#38bdf8)}
  .tnum{font-family:ui-monospace,Menlo,Consolas,monospace;color:#dbe6ff}
  .empty{color:#8fa6cf;font-size:13px;padding:18px;text-align:center;
        border:1px dashed rgba(120,160,255,.3);border-radius:12px}
  .warn{background:rgba(248,113,113,.12);border:1px solid rgba(248,113,113,.45);
        color:#fecaca;border-radius:10px;padding:10px 12px;font-size:13px}
  .good{background:rgba(52,211,153,.12);border:1px solid rgba(52,211,153,.4);
        color:#bbf7d0;border-radius:10px;padding:10px 12px;font-size:13px}
  .who{display:flex;align-items:center;gap:8px;padding:3px 0;font-size:13px}
  .dot{width:11px;height:11px;border-radius:50%;display:inline-block}
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Session state and deep links:  http://host:8501/?room=K7QD2&name=Sam
# --------------------------------------------------------------------------
qp = st.query_params
ss = st.session_state


def browser_origin() -> str:
    try:
        h = st.context.headers
        host = h.get("Host") or h.get("host") or ""
        scheme = (h.get("X-Forwarded-Proto") or h.get("x-forwarded-proto")
                  or ("https" if ":443" in host else "http"))
        if host:
            return f"{scheme}://{host}"
    except Exception:
        pass
    return ""


def lan_bases() -> list:
    bases, origin = [], browser_origin()
    host_only = origin.split("//")[-1]
    port = 8501
    if ":" in host_only:
        try:
            port = int(host_only.rsplit(":", 1)[1])
        except ValueError:
            port = 443 if origin.startswith("https") else 80
    hosted = bool(origin) and not any(
        host_only.startswith(p) for p in ("localhost", "127.0.0.1", "0.0.0.0"))
    if origin and hosted:
        bases.append(origin)
    for ip in core.lan_ip_candidates():
        url = f"http://{ip}:{port}"
        if url not in bases:
            bases.append(url)
    if origin and not hosted:
        bases.append(origin)
    return bases or ["http://localhost:8501"]


ss.setdefault("mode", None)                    # None (lobby) | "solo" | "room"
ss.setdefault("room_code", core.normalize_room(qp.get("room")) if qp.get("room") else "")
ss.setdefault("driver", (qp.get("name") or "Player1")[:20])
ss.setdefault("invited", bool(qp.get("room")))
ss.setdefault("is_host", False)
ss.setdefault("share_base", lan_bases()[0])


def invite_url(room: str) -> str:
    return f"{ss.share_base.rstrip('/')}/?room={room}"


def enter_room(code: str, host: bool = False) -> None:
    code = core.normalize_room(code)
    ss.room_code, ss.mode, ss.is_host = code, "room", host
    board.touch_driver(ss.driver, code)
    st.query_params["room"] = code
    st.rerun()


# --------------------------------------------------------------------------
# Sidebar — settings, and nothing else
# --------------------------------------------------------------------------
room_cfg = rooms.get_config(ss.room_code) if ss.room_code else {}
locked = bool(room_cfg) and not ss.is_host
paint_names = list(PAINTS)

with st.sidebar:
    st.markdown("## 🏎️ Settings")

    driver = st.text_input("Your name", value=ss.driver, max_chars=20)
    ss.driver = driver.strip() or "Player1"
    c1_name = st.selectbox("Your car", paint_names, index=0)

    st.markdown("**Race**")
    if locked:
        st.caption(f"Set by the host of room {ss.room_code}.")
    track = st.selectbox(
        "Circuit", [1, 2, 3],
        index=(int(room_cfg.get("track", 1)) - 1) if locked else 0,
        disabled=locked, format_func=lambda i: CIRCUITS[i])
    laps = st.slider("Laps", 1, 10, int(room_cfg.get("laps", 3)) if locked else 3,
                     disabled=locked)
    power = st.slider("Engine power", 1, 5, int(room_cfg.get("power", 3)) if locked else 3,
                      disabled=locked)
    if locked:
        track = int(room_cfg.get("track", 1))
        laps = int(room_cfg.get("laps", 3))
        power = int(room_cfg.get("power", 3))

    st.markdown("**Opponents**")
    ai_count = st.slider("Computer cars", 0, 6, 0 if ss.mode == "room" else 3)
    ai_names_raw = st.text_input(
        "Their names", value="Vortex, Blaze, Nova",
        help="Separate with commas — one name per computer car.") if ai_count else ""
    ai_names = [n.strip()[:14] for n in ai_names_raw.split(",") if n.strip()]
    skill = st.select_slider("Skill", ["Rookie", "Pro", "Ace", "Legend"], value="Pro")
    skill_map = {"Rookie": 0.68, "Pro": 0.82, "Ace": 0.92, "Legend": 1.0}

    hotseat = st.checkbox("Second player on this keyboard")
    p2_name, c2_name = "Player2", paint_names[1]
    if hotseat:
        p2_name = st.text_input("Player 2 name", value="Player2", max_chars=20)
        c2_name = st.selectbox("Player 2 car", paint_names, index=1)
        st.caption("Player 2 drives with I / J / K / L, U for nitro.")

    st.markdown("**Sound**")
    volume = st.slider("Effects", 0.0, 1.0, 0.8, 0.05)
    music_volume = st.slider("Music", 0.0, 1.0, 0.35, 0.05)
    own_track = st.file_uploader("Your own track", type=["mp3", "ogg", "wav", "m4a"])
    music_url = None
    if own_track is not None:
        raw = own_track.getvalue()
        if len(raw) <= 8 * 1024 * 1024:
            ext = own_track.name.rsplit(".", 1)[-1].lower()
            mime = {"mp3": "audio/mpeg", "ogg": "audio/ogg",
                    "wav": "audio/wav", "m4a": "audio/mp4"}[ext]
            music_url = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
        else:
            st.caption("That file is over 8 MB — trim it first.")

    st.markdown("**Display**")
    camera = st.radio("Camera", ["chase", "top", "cinematic"], horizontal=True)
    quality = st.radio("Graphics", ["high", "low"], horizontal=True)
    auto_fs = st.checkbox("Fullscreen on start", value=True)
    view_h = st.slider("Arena height", 420, 1000, 640, 20)


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
head_l, head_r = st.columns([3, 1.2])
head_l.title("🏁 Turbo Racing League")
rec = board.driver(ss.driver)
m1, m2 = head_r.columns(2)
m1.metric("Points", int(rec["points"]) if rec else 0)
m2.metric("Wins", int(rec["wins"]) if rec else 0)


# --------------------------------------------------------------------------
# Lobby
# --------------------------------------------------------------------------
def lobby_gate() -> None:
    if ss.invited and ss.room_code:
        st.success(f"🎟️ You've been invited to room **{ss.room_code}**")
        c1, c2 = st.columns([1.2, 1])
        name = c1.text_input("Your name", value=ss.driver, max_chars=20, key="join_name")
        c2.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if c2.button("🏁 Join this race", type="primary", use_container_width=True):
            ss.driver = (name or "Player").strip()[:20]
            enter_room(ss.room_code)
        st.divider()

    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="lobbycard"><h4>🆕 Create a room</h4>'
                    '<p>Get a code and a QR for friends to scan.</p></div>',
                    unsafe_allow_html=True)
        if st.button("Create room", use_container_width=True, key="mk"):
            enter_room(core.new_room_code(), host=True)
    with b:
        st.markdown('<div class="lobbycard"><h4>🔑 Join with a code</h4>'
                    '<p>Type the code you were given.</p></div>', unsafe_allow_html=True)
        code = st.text_input("Room code", value=ss.room_code, max_chars=8,
                             placeholder="K7QD2", key="join_code",
                             label_visibility="collapsed")
        if st.button("Join room", use_container_width=True, key="jn"):
            if code.strip():
                enter_room(code)
    with c:
        st.markdown('<div class="lobbycard"><h4>🏎️ Race now</h4>'
                    '<p>Straight into a race against the computer.</p></div>',
                    unsafe_allow_html=True)
        if st.button("Race now", use_container_width=True, key="solo", type="primary"):
            ss.mode, ss.room_code, ss.is_host = "solo", "", False
            board.touch_driver(ss.driver)
            st.query_params.clear()
            st.rerun()


def room_strip(track: int, laps: int, power: int) -> None:
    room = ss.room_code
    if ss.is_host:
        rooms.set_config(room, {"track": int(track), "laps": int(laps),
                                "power": int(power), "host": ss.driver})
    url = invite_url(room)
    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        st.markdown(f'<div class="code">{room}</div>', unsafe_allow_html=True)
        if st.button("Leave room", use_container_width=True):
            ss.mode, ss.room_code, ss.invited, ss.is_host = None, "", False, False
            st.query_params.clear()
            st.rerun()

    with c2:
        png = core.qr_png_bytes(url)
        if png:
            st.markdown(
                f'<img src="data:image/png;base64,{base64.b64encode(png).decode()}" '
                'width="132" style="border-radius:10px;border:6px solid #fff">',
                unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warn">Install <code>qrcode[pil]</code> for the QR '
                        f'image. Invite link: {url}</div>', unsafe_allow_html=True)

    with c3:
        live = rooms.state(room)["players"]
        if live:
            st.markdown("".join(
                f'<div class="who"><span class="dot" style="background:{p["color"]}"></span>'
                f'<b>{p["name"]}</b><span class="sub">lap {p["lap"]}</span></div>'
                for p in sorted(live, key=lambda x: x.get("joined", 0))),
                unsafe_allow_html=True)
        else:
            st.caption("Waiting for drivers — scan the code to join.")

        with st.expander("Invite link / not working?"):
            st.markdown(f"`{url}`")
            bases = lan_bases()
            options = bases + ["Custom…"]
            if ss.share_base not in bases:
                options.insert(0, ss.share_base)
            choice = st.selectbox("Address other players use", options,
                                  index=options.index(ss.share_base)
                                  if ss.share_base in options else 0)
            ss.share_base = (st.text_input("Custom base URL", value=ss.share_base)
                             if choice == "Custom…" else choice)
            host_only = ss.share_base.split("//")[-1].split("/")[0]
            host_name = host_only.rsplit(":", 1)[0] if ":" in host_only else host_only
            try:
                host_port = (int(host_only.rsplit(":", 1)[1]) if ":" in host_only
                             else (443 if ss.share_base.startswith("https") else 80))
            except ValueError:
                host_port = 8501
            if host_name in ("localhost", "127.0.0.1", "0.0.0.0"):
                st.markdown('<div class="warn">A link to <b>localhost</b> only opens on '
                            'this computer — pick a 192.168.x / 10.x address.</div>',
                            unsafe_allow_html=True)
            if st.button("Check other devices can reach this"):
                if ss.share_base.startswith("https"):
                    st.markdown('<div class="good">Hosted address — anyone with the link '
                                'can join.</div>', unsafe_allow_html=True)
                elif core.port_reachable(host_name, host_port):
                    st.markdown('<div class="good">Reachable. If a phone still cannot '
                                'load it, the devices are on different networks.</div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown('<div class="warn">Nothing answered. Start with '
                                '<code>--server.address 0.0.0.0</code> and allow the port '
                                'through your firewall.</div>', unsafe_allow_html=True)
            if not mounted and not api_port:
                st.markdown('<div class="warn">Live multiplayer is unavailable in this '
                            'deployment.</div>', unsafe_allow_html=True)


if ss.mode is None:
    lobby_gate()
    st.stop()

if ss.mode == "room" and ss.room_code:
    room_strip(track, laps, power)
    st.divider()


# --------------------------------------------------------------------------
# Game + league table
# --------------------------------------------------------------------------
cfg = {
    "player": ss.driver,
    "player2": p2_name or "Player2",
    "laps": int(laps),
    "power": int(power),
    "track": int(track),
    "aiCount": int(ai_count),
    "aiNames": ai_names or None,
    "aiSkill": skill_map[skill],
    "volume": float(volume),
    "musicVolume": float(music_volume),
    "musicUrl": music_url,
    "quality": quality,
    "camera": camera,
    "hotseat": bool(hotseat),
    "autoFullscreen": bool(auto_fs),
    "color1": PAINTS[c1_name],
    "color2": PAINTS[c2_name],
    "apiPrefix": core.API_PREFIX if mounted else None,
    "apiPort": int(api_port) if api_port else None,
    "room": ss.room_code or None,
}

# Streamlit's component iframe is sandboxed, and browsers refuse fullscreen from
# one — so the game is also served at its own URL, where fullscreen works.
play_url = None
if configs is not None:
    play_token = configs.put(cfg)
    if mounted:
        play_url = f"/racing/play?c={play_token}"
    elif api_port:
        host = (ss.share_base.split("//")[-1].split(":")[0]
                if ss.share_base else "localhost")
        play_url = f"http://{host}:{api_port}/play?c={play_token}"

game_col, board_col = st.columns([2.6, 1.1])

with game_col:
    if play_url:
        st.markdown(f'<a class="playbtn" href="{play_url}" target="_blank" '
                    'rel="noopener">▶&nbsp; PLAY FULLSCREEN</a>', unsafe_allow_html=True)
    components.html(build_game_html(cfg), height=int(view_h) + 10, scrolling=False)

with board_col:
    st.markdown("### 🏆 League")

    def league_table(rows) -> str:
        top = max((r["points"] for r in rows), default=1) or 1
        html = ['<table class="league"><tr><th>#</th><th>Driver</th>'
                '<th class="r">Points</th><th class="r">Best lap</th></tr>']
        for r in rows[:15]:
            medal = f" g{r['rank']}" if r["rank"] <= 3 else ""
            best = f"{r['best_lap']:.2f}s" if r.get("best_lap") else "—"
            html.append(
                f'<tr class="{"me" if r["name"] == ss.driver else ""}">'
                f'<td><span class="rank{medal}">{r["rank"]}</span></td>'
                f'<td><div class="drv">{r["name"]}</div>'
                f'<div class="sub">{r["wins"]} wins · {r["races"]} races · '
                f'{r["win_rate"]}%</div></td>'
                f'<td class="r"><b class="tnum">{r["points"]:,}</b>'
                f'<div class="ptbar"><span style="width:'
                f'{max(4, round(100 * r["points"] / top))}%"></span></div></td>'
                f'<td class="r tnum">{best}</td></tr>')
        html.append("</table>")
        return "".join(html)

    @st.fragment(run_every=3)
    def leaderboard_panel():
        rows = board.standings(50)
        if not rows:
            st.markdown('<div class="empty">No races yet.<br>Finish one to open the '
                        'league table.</div>', unsafe_allow_html=True)
            return
        st.markdown(league_table(rows), unsafe_allow_html=True)

    leaderboard_panel()

    with st.expander("League data"):
        st.download_button("Download players.json", board.export_json(),
                           "players.json", "application/json", use_container_width=True)
        rows = board.standings(500)
        if rows:
            st.download_button("Export CSV",
                               pd.DataFrame(rows).to_csv(index=False).encode(),
                               "turbo_leaderboard.csv", "text/csv",
                               use_container_width=True)
        col_a, col_b = st.columns(2)
        if col_a.button("Remove me", use_container_width=True):
            board.delete_driver(ss.driver)
            st.rerun()
        if col_b.button("Reset league", use_container_width=True):
            if ss.get("confirm_reset"):
                board.reset()
                ss.confirm_reset = False
                st.rerun()
            ss.confirm_reset = True
            st.caption("Press again to erase every result.")
