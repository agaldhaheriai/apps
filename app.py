"""
Turbo Racing League — Streamlit front end.

    pip install -r requirements.txt
    streamlit run app.py

Everything the browser needs is generated in Python:
  * race_core.py  — players.json store + multiplayer room API server
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


# --------------------------------------------------------------------------
# Background services — started once per Streamlit process
# --------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def services():
    board = core.Leaderboard()
    rooms = core.RoomManager()
    try:
        server = core.GameServer(board, rooms, port=API_PORT)
    except OSError:
        server = core.GameServer(board, rooms, port=0)  # port busy → pick any free one
    return server, board, rooms


server, board, rooms = services()

st.markdown(
    """
<style>
  .stApp {background:linear-gradient(180deg,#070c18 0%,#0d1526 55%,#070c18 100%);}
  html,body,[class*="css"],.stMarkdown,h1,h2,h3,h4,p,span,label{color:#e8eefc}
  div[data-testid="stMetricValue"]{color:#38bdf8}
  div[data-testid="stMetricLabel"]{color:#8fa6cf}
  section[data-testid="stSidebar"]{background:#0a1122;border-right:1px solid rgba(120,160,255,.2)}
  .stDataFrame{border:1px solid rgba(120,160,255,.22);border-radius:10px}
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
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Session state & deep links:  http://host:8501/?room=K7QD2&name=Sam
# --------------------------------------------------------------------------
qp = st.query_params
ss = st.session_state
ss.setdefault("mode", "room" if qp.get("room") else None)   # None | "solo" | "room"
ss.setdefault("room_code", core.normalize_room(qp.get("room")) if qp.get("room") else "")
ss.setdefault("driver", (qp.get("name") or "Player1")[:20])
ss.setdefault("invited", bool(qp.get("room")))
ss.setdefault("share_host", core.lan_ip())
ss.setdefault("share_port", 8501)


def invite_url(room: str) -> str:
    return f"http://{ss.share_host}:{int(ss.share_port)}/?room={room}"


def qr_image_html(url: str, size: int = 200) -> str:
    png = core.qr_png_bytes(url)
    if not png:
        return ('<div style="color:#fca5a5">Install <code>qrcode[pil]</code> '
                "to show the QR code.</div>")
    b64 = base64.b64encode(png).decode()
    return (f'<img src="data:image/png;base64,{b64}" width="{size}" '
            'style="border-radius:12px;border:6px solid #fff">')


def enter_room(code: str) -> None:
    code = core.normalize_room(code)
    ss.room_code = code
    ss.mode = "room"
    board.touch_driver(ss.driver, code)      # player recorded in players.json
    st.query_params["room"] = code
    st.rerun()


# --------------------------------------------------------------------------
# Sidebar — race setup
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🏎️ Race setup")
    driver = st.text_input("Driver name", value=ss.driver, max_chars=20)
    ss.driver = driver.strip() or "Player1"

    track = st.selectbox(
        "Circuit", [1, 2, 3],
        format_func=lambda i: {1: "1 · Sunset Oval (easy)",
                               2: "2 · Harbour S (technical)",
                               3: "3 · Grand Circuit (hard)"}[i])
    laps = st.slider("Laps", 1, 10, 3)
    power = st.slider("Engine power", 1, 5, 3, help="Top speed and points multiplier")

    st.markdown("### 🤖 Opponents")
    ai_count = st.slider("AI cars", 0, 6, 3)
    skill = st.select_slider("AI skill", ["Rookie", "Pro", "Ace", "Legend"], value="Pro")
    skill_map = {"Rookie": 0.68, "Pro": 0.82, "Ace": 0.92, "Legend": 1.0}
    hotseat = st.checkbox("Local 2-player (hot seat)",
                          help="Player 2 drives with I / J / K / L, U for nitro")
    p2_name = st.text_input("Player 2 name", value="Player2", max_chars=20) if hotseat else ""

    st.markdown("### 🎛️ Presentation")
    camera = st.radio("Camera", ["chase", "top", "cinematic"], horizontal=True)
    quality = st.radio("Graphics", ["high", "low"], horizontal=True,
                       help="Low disables shadows and antialiasing on slower machines")
    volume = st.slider("Master volume", 0.0, 1.0, 0.8, 0.05)
    view_h = st.slider("Arena height (px)", 420, 1000, 640, 20)

    st.divider()
    st.caption(f"API port **{server.port}** · data `{os.path.basename(core.DATA_PATH)}`")


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
head_l, head_r = st.columns([3, 1.3])
with head_l:
    st.title("🏁 Turbo Racing League")
    st.markdown(
        '<span class="pill">↑ / W throttle</span><span class="pill">← → steer</span>'
        '<span class="pill">Space nitro</span><span class="pill">C camera</span>'
        '<span class="pill">F fullscreen</span><span class="pill">M mute</span>'
        '<span class="pill">R recover</span>', unsafe_allow_html=True)
with head_r:
    rec = board.driver(ss.driver)
    m1, m2 = st.columns(2)
    m1.metric("Your points", int(rec["points"]) if rec else 0)
    m2.metric("Wins", int(rec["wins"]) if rec else 0)


# --------------------------------------------------------------------------
# LOBBY — create a room, join with a code, or race solo
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
        c3.caption("Everyone in the room races on the same circuit at the same time. "
                   "The first driver to press START starts the countdown for all of you.")
        st.divider()

    st.markdown("### 🎮 Choose how you want to race")
    a, b, c = st.columns(3)

    with a:
        st.markdown('<div class="lobbycard"><h4>🆕 Create a room</h4>'
                    '<p>Get a room code and a QR code, then let friends scan it to '
                    'race against you live.</p></div>', unsafe_allow_html=True)
        if st.button("Create room", use_container_width=True, key="mk"):
            enter_room(core.new_room_code())

    with b:
        st.markdown('<div class="lobbycard"><h4>🔑 Join with a code</h4>'
                    '<p>Got a 5-character code from whoever created the room? '
                    'Type it here.</p></div>', unsafe_allow_html=True)
        code = st.text_input("Room code", value=ss.room_code, max_chars=8,
                             placeholder="K7QD2", key="join_code",
                             label_visibility="collapsed")
        if st.button("Join room", use_container_width=True, key="jn"):
            if core.normalize_room(code) == "LOBBY" and not code.strip():
                st.warning("Enter a room code first.")
            else:
                enter_room(code)

    with c:
        st.markdown('<div class="lobbycard"><h4>🏎️ Race solo</h4>'
                    '<p>Straight into a race against the AI. Your results still go on '
                    'the league leaderboard.</p></div>', unsafe_allow_html=True)
        if st.button("Practice / solo race", use_container_width=True, key="solo"):
            ss.mode = "solo"
            ss.room_code = ""
            board.touch_driver(ss.driver)
            st.query_params.clear()
            st.rerun()


def room_panel() -> None:
    room = ss.room_code
    url = invite_url(room)
    st.markdown("### 🌐 Room " + room)
    c1, c2, c3 = st.columns([1, 1.25, 1.4])

    with c1:
        st.markdown(f'<div class="code">{room}</div>', unsafe_allow_html=True)
        st.caption("Share this code — anyone can type it on the lobby screen.")
        st.markdown(qr_image_html(url, 190), unsafe_allow_html=True)
        st.caption("📱 Scan to join on a phone (touch controls appear automatically).")

    with c2:
        st.markdown("**Invite link**")
        st.code(url, language=None)
        st.markdown("**Address other players use**")
        ss.share_host = st.text_input("Host / LAN IP", value=ss.share_host,
                                      help="Use your computer's LAN IP so phones on the "
                                           "same Wi-Fi can reach it — not 'localhost'.")
        ss.share_port = st.number_input("Streamlit port", 1, 65535, int(ss.share_port))
        if st.button("🚪 Leave room"):
            ss.mode = None
            ss.room_code = ""
            ss.invited = False
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
                    f'<span style="color:#8fa6cf;font-size:12px">lap {p["lap"]}</span></div>',
                    unsafe_allow_html=True)
        else:
            st.caption("Nobody connected yet — the arena below joins automatically "
                       "as soon as it loads.")
        if st.button("🔄 Refresh room"):
            st.rerun()


if ss.mode is None:
    lobby_gate()
    st.stop()

if ss.mode == "room" and ss.room_code:
    room_panel()
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
    "quality": quality,
    "camera": camera,
    "hotseat": bool(hotseat),
    "apiPort": int(server.port),
    "room": ss.room_code or None,
}

game_col, board_col = st.columns([2.6, 1.15])

with game_col:
    components.html(build_game_html(cfg), height=int(view_h) + 10, scrolling=False)
    st.caption("Click the arena once so it takes the keyboard. **F** (or ⛶) goes "
               "fullscreen — **Esc** or **F** again comes back.")

with board_col:
    st.markdown("### 🏆 League leaderboard")
    st.caption(f"Written to `{os.path.basename(core.DATA_PATH)}` after every race.")

    @st.fragment(run_every=3)
    def leaderboard_panel():
        rows = board.standings(50)
        if not rows:
            st.info("No races recorded yet. Finish one to open the league table.")
            return
        df = pd.DataFrame(rows)
        for col in ("best_time", "best_lap", "top_speed", "win_rate"):
            if col not in df:
                df[col] = None
        show = df[["rank", "name", "points", "wins", "races", "win_rate",
                   "best_time", "best_lap"]].rename(columns={
            "rank": "#", "name": "Driver", "points": "Points", "wins": "Wins",
            "races": "Races", "win_rate": "Win %", "best_time": "Best race (s)",
            "best_lap": "Best lap (s)"})
        st.dataframe(show, hide_index=True, use_container_width=True, height=330)

        mine = df[df["name"] == ss.driver]
        if not mine.empty:
            r = mine.iloc[0]
            a, b = st.columns(2)
            a.metric("Rank", f"#{int(r['rank'])}")
            b.metric("Win rate", f"{r['win_rate']}%")
            c, d = st.columns(2)
            c.metric("Best lap", f"{r['best_lap']:.2f}s" if pd.notna(r["best_lap"]) else "—")
            d.metric("Top speed", f"{int(r['top_speed'] or 0)} km/h")

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
        st.caption("This is the file everything is stored in — download it to keep a "
                   "backup or move the league to another machine.")
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
    st.markdown(
        f"""
**Driving.** Throttle ↑/W, brake and reverse ↓/S, steer ←→ or A/D, **Space** for nitro
(the purple bar refills when you're off the boost). Off the tarmac you lose grip and speed;
the tyre wall scrubs most of it. **R** puts you back on the racing line.

**Sound.** Synthesised in the browser with the Web Audio API — no audio files to download:
engine note and revs tied to throttle and speed, wind rush, tyre screech when you slide or
run wide, impact thud on contact, nitro whoosh, start-light beeps, a crowd that swells when
you complete a lap or crash, and a winner's fanfare.

**Start / finish.** The gantry over the line carries the *START / FINISH* board with the
circuit name and lap count, five start lights that light up red through the countdown, and
the checkered line painted across the tarmac. A lap only counts when you pass all eight
sectors in order, so cutting back across the line does nothing.

**Rooms.** Create a room, share the code or let people scan the QR. Every browser posts its
car position about twelve times a second to the API on port **{server.port}**, so everyone
sees everyone else's car, name plate and gap live. Players on other devices must reach your
machine: use `{core.lan_ip()}` rather than `localhost`, and allow ports 8501 and
{server.port} through the firewall.

**Player data.** Every finished race is appended to `{os.path.basename(core.DATA_PATH)}`
with position, total time, best lap, top speed and contacts. Points are Formula-style and
scale with engine class. The file is written atomically, so it never ends up half-saved.
"""
    )

st.caption(f"Turbo Racing League · circuit {track} · {laps} laps · engine {power}/5 · "
           f"host {socket.gethostname()} · API :{server.port}")
