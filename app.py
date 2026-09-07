"""
Turbo Racing League — Streamlit front end.

    pip install -r requirements.txt
    streamlit run app.py

Everything the browser needs is generated in Python:
  * race_core.py  — players.json store + multiplayer room API
  * game_html.py  — the Three.js / Web Audio racing client
"""

from __future__ import annotations

import base64
import os
import socket

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


# --------------------------------------------------------------------------
# Background services — started once per Streamlit process
# --------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def services():
    board = core.Leaderboard()
    rooms = core.RoomManager()

    # Preferred path: serve the API from Streamlit's own port, so players need
    # only one open port and hosted HTTPS deployments stay same-origin.
    mounted = core.attach_to_streamlit(board, rooms)

    # Fallback listener on its own port. Hosted platforms often forbid extra
    # ports, so a failure here is fine as long as the mount worked.
    server = None
    for port in (API_PORT, 0):
        try:
            server = core.GameServer(board, rooms, port=port)
            break
        except Exception:
            continue
    return server, board, rooms, mounted


server, board, rooms, mounted = services()
api_port = server.port if server else None

if not mounted and not api_port:
    st.warning("The race server could not start, so multiplayer rooms are unavailable "
               "in this deployment. Solo and hot-seat racing still work, and results "
               "are kept in your browser.")

st.markdown(
    """
<style>
  .stApp {background:linear-gradient(180deg,#070c18 0%,#0d1526 55%,#070c18 100%);}
  html,body,[class*="css"],.stMarkdown,h1,h2,h3,h4,p,span,label{color:#e8eefc}
  div[data-testid="stMetricValue"]{color:#38bdf8}
  div[data-testid="stMetricLabel"]{color:#8fa6cf}
  section[data-testid="stSidebar"]{background:#0a1122;border-right:1px solid rgba(120,160,255,.2)}
  .pill{display:inline-block;padding:4px 12px;margin:2px 4px 2px 0;border-radius:20px;
        background:rgba(56,189,248,.16);color:#7dd3fc;font-size:12px;font-weight:700}
  .code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:34px;font-weight:800;
        letter-spacing:10px;color:#fbbf24;background:rgba(251,191,36,.1);
        border:1px dashed rgba(251,191,36,.55);border-radius:12px;padding:10px 8px 10px 18px;
        display:block;text-align:center}
  .lobbycard{background:rgba(15,23,42,.75);border:1px solid rgba(120,160,255,.25);
        border-radius:16px;padding:18px 20px;height:100%}
  .lobbycard h4{margin:0 0 6px;font-size:16px}
  .lobbycard p{color:#9fb3d9;font-size:13px;margin:0 0 12px;line-height:1.5}
  .stButton>button{border:1px solid rgba(120,160,255,.3);background:rgba(56,189,248,.12);
        color:#e8eefc;font-weight:600}
  .stButton>button:hover{background:rgba(56,189,248,.28);color:#fff}

  /* ---- league table ---- */
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
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Session state & deep links:  http://host:8501/?room=K7QD2&name=Sam
# --------------------------------------------------------------------------
qp = st.query_params
ss = st.session_state


def browser_origin() -> str:
    """The base URL this browser reached the app on.

    On a hosted deployment (Streamlit Community Cloud and friends) this is the
    only address other people can use, and it is also the right answer when you
    opened the app on your LAN address. Falls back to a LAN guess locally.
    """
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
    """Every base URL that could plausibly reach this app."""
    bases = []
    origin = browser_origin()
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
        bases.append(origin)              # last: only works on this computer
    return bases or ["http://localhost:8501"]


ss.setdefault("mode", None)                    # None (lobby) | "solo" | "room"
ss.setdefault("room_code", core.normalize_room(qp.get("room")) if qp.get("room") else "")
ss.setdefault("driver", (qp.get("name") or "Player1")[:20])
ss.setdefault("invited", bool(qp.get("room")))
ss.setdefault("is_host", False)
ss.setdefault("share_base", lan_bases()[0])


def invite_url(room: str) -> str:
    return f"{ss.share_base.rstrip('/')}/?room={room}"


def qr_image_html(url: str, size: int = 210) -> str:
    png = core.qr_png_bytes(url)
    if not png:
        return ('<div class="warn">Install <code>qrcode[pil]</code> to render the QR '
                "image — the invite link below still works.</div>")
    b64 = base64.b64encode(png).decode()
    return (f'<img src="data:image/png;base64,{b64}" width="{size}" '
            'style="border-radius:12px;border:8px solid #fff">')


def enter_room(code: str, host: bool = False) -> None:
    code = core.normalize_room(code)
    ss.room_code = code
    ss.mode = "room"
    ss.is_host = host
    board.touch_driver(ss.driver, code)        # player recorded in players.json
    st.query_params["room"] = code
    st.rerun()


# --------------------------------------------------------------------------
# Sidebar — race setup
# --------------------------------------------------------------------------
room_cfg = rooms.get_config(ss.room_code) if ss.room_code else {}
locked = bool(room_cfg) and not ss.is_host

with st.sidebar:
    st.markdown("## 🏎️ Race setup")
    driver = st.text_input("Driver name", value=ss.driver, max_chars=20)
    ss.driver = driver.strip() or "Player1"

    if locked:
        st.info(f"Room **{ss.room_code}** settings are set by whoever created it — "
                "circuit, laps and engine are matched for everyone.")

    track_opts = [1, 2, 3]
    track = st.selectbox(
        "Circuit", track_opts,
        index=track_opts.index(int(room_cfg.get("track", 1))) if locked else 0,
        disabled=locked,
        format_func=lambda i: {1: "1 · Sunset Oval (easy)",
                               2: "2 · Harbour Sweep (technical)",
                               3: "3 · Grand Circuit (hard)"}[i])
    laps = st.slider("Laps", 1, 10, int(room_cfg.get("laps", 3)) if locked else 3,
                     disabled=locked)
    power = st.slider("Engine power", 1, 5, int(room_cfg.get("power", 3)) if locked else 3,
                      disabled=locked, help="Top speed and points multiplier")
    if locked:
        track, laps = int(room_cfg.get("track", 1)), int(room_cfg.get("laps", 3))
        power = int(room_cfg.get("power", 3))

    st.markdown("### 🎨 Cars")
    paint_names = list(PAINTS)
    c1_name = st.selectbox("Player 1 paint", paint_names, index=0)
    hotseat = st.checkbox("Local 2-player (hot seat)",
                          help="Both players on this keyboard: P2 drives with I / J / K / L, "
                               "U for nitro")
    p2_name, c2_name = "Player2", paint_names[1]
    if hotseat:
        p2_name = st.text_input("Player 2 name", value="Player2", max_chars=20)
        c2_name = st.selectbox("Player 2 paint", paint_names, index=1)

    st.markdown("### 🤖 Opponents")
    ai_default = 0 if ss.mode == "room" else 3
    ai_count = st.slider("AI cars", 0, 6, ai_default,
                         help="In a room, keep this low so the grid stays about the "
                              "real drivers.")
    skill = st.select_slider("AI skill", ["Rookie", "Pro", "Ace", "Legend"], value="Pro")
    skill_map = {"Rookie": 0.68, "Pro": 0.82, "Ace": 0.92, "Legend": 1.0}

    st.markdown("### 🔊 Sound")
    volume = st.slider("Effects volume", 0.0, 1.0, 0.8, 0.05)
    music_volume = st.slider("Music volume", 0.0, 1.0, 0.35, 0.05,
                             help="Drift-style backing loop; it ducks under the engine "
                                  "and crashes automatically. B toggles it in-game.")
    own_track = st.file_uploader("Use your own track (mp3 / ogg / wav)",
                                 type=["mp3", "ogg", "wav", "m4a"])
    music_url = None
    if own_track is not None:
        raw = own_track.getvalue()
        if len(raw) > 8 * 1024 * 1024:
            st.warning("That file is over 8 MB — trim it or it will slow the page down.")
        else:
            mime = {"mp3": "audio/mpeg", "ogg": "audio/ogg",
                    "wav": "audio/wav", "m4a": "audio/mp4"}[own_track.name.rsplit(".", 1)[-1].lower()]
            music_url = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
            st.caption(f"▶️ {own_track.name} will play instead of the built-in loop.")

    st.markdown("### 🎛️ Presentation")
    auto_fs = st.checkbox("Go fullscreen when the race starts", value=True,
                          help="Uses the START click as the gesture browsers require. "
                               "Esc or F comes back.")
    camera = st.radio("Camera", ["chase", "top", "cinematic"], horizontal=True)
    quality = st.radio("Graphics", ["high", "low"], horizontal=True,
                       help="Low disables shadows and antialiasing on slower machines")
    view_h = st.slider("Arena height (px)", 420, 1000, 640, 20)

    st.divider()
    st.caption(("Race API on Streamlit's own port ✅" if mounted
                else (f"Race API on port {api_port}" if api_port else "Race API unavailable"))
               + f" · data `{os.path.basename(core.DATA_PATH)}`")


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
head_l, head_r = st.columns([3, 1.3])
with head_l:
    st.title("🏁 Turbo Racing League")
    st.markdown(
        '<span class="pill">↑ / W throttle</span><span class="pill">← → steer</span>'
        '<span class="pill">Space nitro</span><span class="pill">C camera</span>'
        '<span class="pill">F fullscreen</span><span class="pill">M sound</span>'
        '<span class="pill">B music</span><span class="pill">R recover</span>',
        unsafe_allow_html=True)
with head_r:
    rec = board.driver(ss.driver)
    m1, m2 = st.columns(2)
    m1.metric("Your points", int(rec["points"]) if rec else 0)
    m2.metric("Wins", int(rec["wins"]) if rec else 0)


# --------------------------------------------------------------------------
# LOBBY
# --------------------------------------------------------------------------
def lobby_gate() -> None:
    if ss.invited and ss.room_code:
        st.success(f"🎟️ You've been invited to room **{ss.room_code}**")
        c1, c2, c3 = st.columns([1.2, 1, 2])
        name = c1.text_input("Your driver name", value=ss.driver, max_chars=20, key="join_name")
        c2.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if c2.button("🏁 Join this race", type="primary", use_container_width=True):
            ss.driver = (name or "Player").strip()[:20]
            enter_room(ss.room_code)
        c3.caption("You'll race the circuit and lap count the room's host picked. "
                   "The first driver to press START begins the countdown for everyone.")
        st.divider()

    st.markdown("### 🎮 Choose how you want to race")
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="lobbycard"><h4>🆕 Create a room</h4>'
                    '<p>Get a room code and a QR code, then let friends scan it to '
                    'race against you live.</p></div>', unsafe_allow_html=True)
        if st.button("Create room", use_container_width=True, key="mk"):
            enter_room(core.new_room_code(), host=True)
    with b:
        st.markdown('<div class="lobbycard"><h4>🔑 Join with a code</h4>'
                    '<p>Got a 5-character code from whoever created the room? '
                    'Type it here.</p></div>', unsafe_allow_html=True)
        code = st.text_input("Room code", value=ss.room_code, max_chars=8,
                             placeholder="K7QD2", key="join_code",
                             label_visibility="collapsed")
        if st.button("Join room", use_container_width=True, key="jn"):
            if not code.strip():
                st.warning("Enter a room code first.")
            else:
                enter_room(code)
    with c:
        st.markdown('<div class="lobbycard"><h4>🏎️ Race solo</h4>'
                    '<p>Straight into a race against the AI — or share the keyboard '
                    'with the hot-seat option in the sidebar.</p></div>',
                    unsafe_allow_html=True)
        if st.button("Practice / solo race", use_container_width=True, key="solo"):
            ss.mode, ss.room_code, ss.is_host = "solo", "", False
            board.touch_driver(ss.driver)
            st.query_params.clear()
            st.rerun()


def room_panel(track: int, laps: int, power: int) -> None:
    room = ss.room_code
    if ss.is_host:                     # host's settings define the event
        rooms.set_config(room, {"track": int(track), "laps": int(laps),
                                "power": int(power), "host": ss.driver})
    url = invite_url(room)
    st.markdown("### 🌐 Room " + room)
    if not mounted and not api_port:
        st.markdown('<div class="warn">Live multiplayer is not available in this '
                    'deployment — the race server could not start. Everyone can still '
                    'race the same circuit and compare times on the leaderboard.</div>',
                    unsafe_allow_html=True)
    elif not mounted and browser_origin().startswith("https"):
        st.markdown(f'<div class="warn">This is a hosted deployment and the race API '
                    f'could not attach to the app\'s own port, so it is only reachable '
                    f'on port {api_port} — which hosted platforms block. Cars from other '
                    f'players will not appear here; run the app on your own machine or '
                    f'network for live racing.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.25, 1.35])

    with c1:
        st.markdown(f'<div class="code">{room}</div>', unsafe_allow_html=True)
        st.markdown(qr_image_html(url), unsafe_allow_html=True)
        st.caption("📱 Scan with a phone camera on the **same Wi-Fi**. "
                   "Touch controls appear automatically.")

    with c2:
        st.markdown("**Invite link**")
        st.code(url, language=None)

        bases = lan_bases()
        options = bases + ["Custom…"]
        if ss.share_base not in bases:
            options.insert(0, ss.share_base)
        choice = st.selectbox(
            "Address other players use", options,
            index=options.index(ss.share_base) if ss.share_base in options else 0,
            help="Whatever you pick here is what the QR code encodes. On a hosted "
                 "deployment use the public URL; on your own network use the LAN "
                 "address of the Wi-Fi your phone is on.")
        if choice == "Custom…":
            ss.share_base = st.text_input("Custom base URL", value=ss.share_base)
        else:
            ss.share_base = choice

        host_only = ss.share_base.split("//")[-1].split("/")[0]
        host_name = host_only.rsplit(":", 1)[0] if ":" in host_only else host_only
        try:
            host_port = int(host_only.rsplit(":", 1)[1]) if ":" in host_only else (
                443 if ss.share_base.startswith("https") else 80)
        except ValueError:
            host_port = 8501

        if host_name in ("localhost", "127.0.0.1", "0.0.0.0"):
            st.markdown('<div class="warn">A link pointing at <b>localhost</b> only '
                        'ever opens on this computer. Pick a 192.168.x / 10.x address '
                        'so a phone can reach you.</div>', unsafe_allow_html=True)
        if st.button("🔎 Check that other devices can reach this"):
            if ss.share_base.startswith("https"):
                st.markdown('<div class="good">This is a hosted address — anyone with '
                            'the link can join, no firewall changes needed.</div>',
                            unsafe_allow_html=True)
            elif core.port_reachable(host_name, host_port):
                st.markdown('<div class="good">Port is open on that address. If a phone '
                            'still cannot load it, the two devices are on different '
                            'networks (guest Wi-Fi, or mobile data).</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="warn">Nothing answered on that address. Restart with '
                    '<code>streamlit run app.py --server.address 0.0.0.0</code> and '
                    'allow the port through your firewall.</div>',
                    unsafe_allow_html=True)
        if st.button("🚪 Leave room"):
            ss.mode, ss.room_code, ss.invited, ss.is_host = None, "", False, False
            st.query_params.clear()
            st.rerun()

    with c3:
        st.markdown("**Drivers in this room**")
        live = rooms.state(room)["players"]
        if live:
            for p in sorted(live, key=lambda x: x.get("joined", 0)):
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0">'
                    f'<span style="width:12px;height:12px;border-radius:50%;'
                    f'background:{p["color"]};display:inline-block"></span>'
                    f'<b>{p["name"]}</b>'
                    f'<span class="sub">lap {p["lap"]}</span></div>',
                    unsafe_allow_html=True)
        else:
            st.caption("Nobody connected yet — the arena below joins automatically once "
                       "it loads, and other players appear here within a second or two.")
        cfg_now = rooms.get_config(room)
        if cfg_now:
            st.markdown(
                f'<span class="pill">Circuit {cfg_now.get("track", 1)}</span>'
                f'<span class="pill">{cfg_now.get("laps", 3)} laps</span>'
                f'<span class="pill">Engine {cfg_now.get("power", 3)}/5</span>'
                + (f'<span class="pill">Host {cfg_now.get("host", "?")}</span>'
                   if cfg_now.get("host") else ""),
                unsafe_allow_html=True)
        if st.button("🔄 Refresh"):
            st.rerun()


if ss.mode is None:
    lobby_gate()
    st.stop()

if ss.mode == "room" and ss.room_code:
    room_panel(track, laps, power)
else:
    lb1, lb2 = st.columns([4, 1])
    lb1.info("Solo race — results are saved to the league leaderboard.")
    if lb2.button("🌐 Play with friends", use_container_width=True):
        ss.mode = None
        st.rerun()

st.divider()


# --------------------------------------------------------------------------
# The game
# --------------------------------------------------------------------------
cfg = {
    "player": ss.driver,
    "player2": p2_name or "Player2",
    "laps": int(laps),
    "power": int(power),
    "track": int(track),
    "aiCount": int(ai_count),
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

game_col, board_col = st.columns([2.6, 1.15])

with game_col:
    components.html(build_game_html(cfg), height=int(view_h) + 10, scrolling=False)
    st.caption("Pressing **START RACE** takes the game fullscreen on desktop and "
               "phones — **Esc** or **F** comes back. On a phone, turn it sideways "
               "for the full width of the track.")

with board_col:
    st.markdown("### 🏆 League leaderboard")
    st.caption(f"Written to `{os.path.basename(core.DATA_PATH)}` after every race.")

    def league_table(rows) -> str:
        top = max((r["points"] for r in rows), default=1) or 1
        html = ['<table class="league"><tr><th>#</th><th>Driver</th>'
                '<th class="r">Points</th><th class="r">Best lap</th></tr>']
        for r in rows[:15]:
            medal = f" g{r['rank']}" if r["rank"] <= 3 else ""
            best = f"{r['best_lap']:.2f}s" if r.get("best_lap") else "—"
            race = f"{r['best_time']:.2f}s" if r.get("best_time") else "—"
            html.append(
                f'<tr class="{"me" if r["name"] == ss.driver else ""}">'
                f'<td><span class="rank{medal}">{r["rank"]}</span></td>'
                f'<td><div class="drv">{r["name"]}</div>'
                f'<div class="sub">{r["wins"]} wins · {r["races"]} races · '
                f'{r["win_rate"]}% · best race {race}</div></td>'
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
            st.markdown('<div class="empty">No races recorded yet.<br>'
                        'Finish one to open the league table.</div>',
                        unsafe_allow_html=True)
            return
        st.markdown(league_table(rows), unsafe_allow_html=True)
        mine = next((r for r in rows if r["name"] == ss.driver), None)
        if mine:
            a, b = st.columns(2)
            a.metric("Rank", f"#{mine['rank']}")
            b.metric("Win rate", f"{mine['win_rate']}%")
            c, d = st.columns(2)
            c.metric("Best lap", f"{mine['best_lap']:.2f}s" if mine.get("best_lap") else "—")
            d.metric("Top speed", f"{int(mine.get('top_speed') or 0)} km/h")

    leaderboard_panel()

    with st.expander("📜 Recent results"):
        recent = board.recent_races(20)
        if recent:
            rdf = pd.DataFrame(recent)
            rdf["When"] = pd.to_datetime(rdf["ts"], unit="s").dt.strftime("%d %b %H:%M")
            st.dataframe(
                rdf[["When", "driver", "position", "field", "total_time", "best_lap", "track"]]
                .rename(columns={"driver": "Driver", "position": "Pos", "field": "Cars",
                                 "total_time": "Time", "best_lap": "Best lap",
                                 "track": "Circuit"}),
                hide_index=True, use_container_width=True, height=260)
        else:
            st.caption("Nothing yet.")

    with st.expander("💾 Player data (players.json)"):
        st.caption("Everything is stored in this one file — download it to keep a backup "
                   "or move the league to another machine.")
        if browser_origin().startswith("https"):
            st.caption("⚠️ On a hosted deployment the file lives on a temporary disk and "
                       "is wiped when the app restarts or redeploys. Download it if you "
                       "want to keep a season's results.")
        st.download_button("⬇️ Download players.json", board.export_json(),
                           "players.json", "application/json", use_container_width=True)
        rows = board.standings(500)
        if rows:
            st.download_button("⬇️ Export CSV", pd.DataFrame(rows).to_csv(index=False).encode(),
                               "turbo_leaderboard.csv", "text/csv", use_container_width=True)
        col_a, col_b = st.columns(2)
        if col_a.button("Remove my driver", use_container_width=True):
            board.delete_driver(ss.driver)
            st.rerun()
        if col_b.button("Reset league", use_container_width=True):
            if ss.get("confirm_reset"):
                board.reset()
                ss.confirm_reset = False
                st.rerun()
            ss.confirm_reset = True
            st.warning("Press again to erase every result.")


# --------------------------------------------------------------------------
# Help
# --------------------------------------------------------------------------
with st.expander("📖 How it all works"):
    ips = ", ".join(core.lan_ip_candidates()[:3])
    st.markdown(
        f"""
**Driving.** Throttle ↑/W, brake and reverse ↓/S, steer ←→ or A/D, **Space** for nitro.
Off the tarmac you lose grip; the tyre wall scrubs most of your speed. **R** puts you back
on the racing line. Hot seat gives Player 2 I/J/K/L and U.

**Sound.** All synthesised in the browser — engine revs tied to throttle and speed, wind
rush, tyre screech, crash thud, nitro whoosh, a whoosh and a crowd swell when you take a
place off someone, start-light beeps, lap cheers and a winner's fanfare. The backing loop
is an original drift-style track that ducks under the engine and drops on impacts; **B**
toggles it, and you can upload your own track in the sidebar instead.

**Two players.**
*Same computer* — tick **Local 2-player (hot seat)** in the sidebar; both cars appear on
the grid with the colours you chose.
*Two devices* — create a room, then have the other player scan the QR or type the code.
The room's host sets circuit, laps and engine, and everyone joining is matched to them, so
you are always on the same track. The chip above the arena shows how many drivers are
connected.

**If the QR does not open on a phone:** both devices must be on the same Wi-Fi, and the
address in the invite must be this computer's LAN address ({ips}) — not `localhost`, and
not a VPN address. Start Streamlit with `--server.address 0.0.0.0`, allow the port through
your firewall, and use **Check that phones can reach this** in the room panel.
{"The race API is served on Streamlit's own port, so one open port is all you need."
 if mounted else
 (f"The race API is on port {api_port}, so that port needs to be open too."
  if api_port else "The race API could not start in this deployment.")}

**Player data.** Every finished race is appended to `{os.path.basename(core.DATA_PATH)}`
with position, total time, best lap, top speed and contacts. Points are Formula-style and
scale with engine class.
"""
    )

st.caption(f"Turbo Racing League · circuit {track} · {laps} laps · engine {power}/5 · "
           f"host {socket.gethostname()} · "
           + ("API mounted on Streamlit" if mounted
              else (f"API :{api_port}" if api_port else "API offline")))
