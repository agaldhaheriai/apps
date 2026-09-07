# Import system libraries
import streamlit as st  # Main web framework
import pandas as pd  # Data manipulation library
import streamlit.components.v1 as components  # Embedded HTML/JS renderer

# Set page configuration for 3D game layout with automotive theme styling
st.set_page_config(
    page_title="3D Turbo Racing League", layout="wide", page_icon="🏎️"
)

# Custom Automotive Theme Styling
st.markdown("""
<style>
    /* Dark Automotive Background Theme */
    .stApp {
        background: linear-gradient(rgba(15, 15, 20, 0.88), rgba(15, 15, 20, 0.95)), 
                    url('https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-attachment: fixed;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(30, 30, 40, 0.8);
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State Data Structures
if "sessions" not in st.session_state:
    st.session_state.sessions = {
        "Session #101 (Speedway)": {"host": "ProRacer", "players": ["ProRacer"], "max": 2, "status": "Waiting"},
        "Session #102 (Circuit)": {"host": "DriftKing", "players": ["DriftKing"], "max": 2, "status": "Waiting"}
    }

if "registered_users" not in st.session_state:
    st.session_state.registered_users = ["ProRacer", "DriftKing", "TurboMax"]

if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = "Racer1"


def record_win(winner, time_sec, speed_lvl):
    if winner not in st.session_state.leaderboard:
        st.session_state.leaderboard[winner] = {
            "Wins": 0, "Total Points": 0, "Fastest Time (s)": 999.0, "Races": 0
        }
    entry = st.session_state.leaderboard[winner]
    entry["Wins"] += 1
    entry["Total Points"] += 150 * speed_lvl
    entry["Races"] += 1
    if time_sec < entry["Fastest Time (s)"]:
        entry["Fastest Time (s)"] = round(time_sec, 2)


# App Header Setup
st.title("🏎️ 3D Low-Poly Racing Engine")
st.caption("Custom Track Boundaries | AI Bot Opponent | Progressive Level Difficulty")

# Navigation Tabs
tab_player, tab_arena, tab_lobbies, tab_ranks = st.tabs([
    "👤 Player Setup", "🏁 3D Race Arena", "🌐 Game Lobbies", "🏆 Leaderboard"
])

# --- TAB 1: PLAYER REGISTRATION ---
with tab_player:
    st.subheader("Register / Select Player Name")
    col_a, col_b = st.columns(2)
    
    with col_a:
        new_name = st.text_input("Enter New Player Name:", placeholder="e.g. SpeedDemon99")
        if st.button("Save & Select Name"):
            if new_name.strip():
                clean_name = new_name.strip()
                if clean_name not in st.session_state.registered_users:
                    st.session_state.registered_users.append(clean_name)
                st.session_state.current_user = clean_name
                st.success(f"Driver profile updated to: **{clean_name}**")
            else:
                st.warning("Please enter a valid player name.")

    with col_b:
        selected_profile = st.selectbox(
            "Select Existing Player Profile:",
            st.session_state.registered_users,
            index=0 if st.session_state.current_user not in st.session_state.registered_users 
            else st.session_state.registered_users.index(st.session_state.current_user)
        )
        if st.button("Switch Profile"):
            st.session_state.current_user = selected_profile
            st.info(f"Switched driver to: **{selected_profile}**")

    st.divider()
    st.markdown(f"**Current Driver Active:** `{st.session_state.current_user}`")

# --- TAB 2: 3D RACE ARENA ---
with tab_arena:
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.2, 1, 1, 1.2])
    
    with col1:
        p1_driver = st.text_input("Player 1 (Red Car):", value=st.session_state.current_user, key="p1_val")
    with col2:
        p2_input = st.text_input("Player 2 (Leave blank for AI Bot):", value="", key="p2_val", placeholder="AI Bot (Auto-Drive)")
        p2_driver = p2_input.strip() if p2_input.strip() else "CPU_Bot (AI)"
        is_cpu = not bool(p2_input.strip())
    with col3:
        level_choice = st.selectbox("Track Level Difficulty:", [1, 2, 3], format_func=lambda x: f"Level {x} " + ("(Oval)" if x==1 else "(Figure 8)" if x==2 else "(Complex Circuit)"))
    with col4:
        speed_lvl = st.slider("Engine Speed", 1, 5, 3, key="speed_setting")
    with col5:
        camera_view = st.selectbox("3D Camera:", ["Chase Cam (Behind)", "Third-Person (High)", "Top-Down (Map)"])

    st.markdown(
        f"**🎮 Mode:** {'**Player vs AI Bot**' if is_cpu else '**2-Player Local**'} | "
        "**Controls:** **P1 (Red):** `W` (Gas), `A` (Left), `D` (Right), `S` (Reverse)" + 
        ("" if is_cpu else " | **P2 (Blue):** `Up Arrow`, `Left Arrow`, `Right Arrow`, `Down Arrow`")
    )

    # Embedded HTML/Three.js Game Renderer
    threejs_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #111; font-family: sans-serif; }}
            #hud {{ 
                position: absolute; top: 10px; left: 10px; color: #fff; 
                font-weight: bold; font-size: 15px; text-shadow: 2px 2px 4px #000; z-index: 10;
                background: rgba(0,0,0,0.6); padding: 10px; border-radius: 6px;
            }}
            #start-btn {{
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                padding: 15px 35px; font-size: 22px; font-weight: bold; color: #fff;
                background: #e63946; border: none; border-radius: 8px; cursor: pointer;
                box-shadow: 0 4px 15px rgba(230,57,70,0.5); z-index: 20;
            }}
            #start-btn:hover {{ background: #d62839; }}
            canvas {{ display: block; width: 100vw; height: 520px; }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <button id="start-btn" onclick="startRace()">🚀 START RACE</button>
        <div id="hud">
            🏁 Level {level_choice} Track | Speed: {speed_lvl}<br>
            ⏱️ Timer: <span id="timer-display" style="color:#00ffcc;">0.0s</span><br>
            <span id="p1-hud" style="color: #ff4444;">{p1_driver}: Lap 0/3</span> | 
            <span id="p2-hud" style="color: #4488ff;">{p2_driver}: Lap 0/3</span><br>
            <span id="game-status" style="color: #ffcc00;">Click START RACE to begin countdown!</span>
        </div>
        <script>
            // Scene Setup
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x1a1a24);
            scene.fog = new THREE.Fog(0x1a1a24, 20, 160);

            const camera = new THREE.PerspectiveCamera(60, window.innerWidth / 520, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, 520);
            renderer.shadowMap.enabled = true;
            document.body.appendChild(renderer.domElement);

            // Lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
            dirLight.position.set(40, 80, 40);
            dirLight.castShadow = true;
            scene.add(dirLight);

            // Ground
            const groundGeo = new THREE.PlaneGeometry(250, 250);
            const groundMat = new THREE.MeshLambertMaterial({{ color: 0x223322 }});
            const ground = new THREE.Mesh(groundGeo, groundMat);
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
            scene.add(ground);

            // Track Level Paths Configuration
            const level = {level_choice};
            let trackCurve;
            const trackWidth = 7;

            if (level === 1) {{ // Level 1: Oval
                trackCurve = new THREE.CatmullRomCurve3([
                    new THREE.Vector3(-30, 0, 20), new THREE.Vector3(30, 0, 20),
                    new THREE.Vector3(45, 0, 0), new THREE.Vector3(30, 0, -20),
                    new THREE.Vector3(-30, 0, -20), new THREE.Vector3(-45, 0, 0)
                ], true);
            }} else if (level === 2) {{ // Level 2: Figure 8 Loop
                trackCurve = new THREE.CatmullRomCurve3([
                    new THREE.Vector3(-35, 0, 25), new THREE.Vector3(0, 0, 0),
                    new THREE.Vector3(35, 0, -25), new THREE.Vector3(45, 0, 0),
                    new THREE.Vector3(35, 0, 25), new THREE.Vector3(0, 0, 0),
                    new THREE.Vector3(-35, 0, -25), new THREE.Vector3(-45, 0, 0)
                ], true);
            }} else {{ // Level 3: Complex Multi-Turn Circuit
                trackCurve = new THREE.CatmullRomCurve3([
                    new THREE.Vector3(-40, 0, 30), new THREE.Vector3(10, 0, 35),
                    new THREE.Vector3(40, 0, 20), new THREE.Vector3(20, 0, -10),
                    new THREE.Vector3(40, 0, -35), new THREE.Vector3(-10, 0, -25),
                    new THREE.Vector3(-35, 0, -35), new THREE.Vector3(-25, 0, 0)
                ], true);
            }}

            // Render Track Surface
            const trackGeo = new THREE.TubeGeometry(trackCurve, 120, trackWidth, 8, true);
            const trackMat = new THREE.MeshLambertMaterial({{ color: 0x333338 }});
            const trackMesh = new THREE.Mesh(trackGeo, trackMat);
            trackMesh.scale.set(1, 0.01, 1); // Flatten tube into surface
            trackMesh.position.y = 0.02;
            scene.add(trackMesh);

            // Car Factory
            function createCar(colorHex) {{
                const carGroup = new THREE.Group();
                const bodyGeo = new THREE.BoxGeometry(1.8, 0.7, 3.2);
                const bodyMat = new THREE.MeshLambertMaterial({{ color: colorHex }});
                const body = new THREE.Mesh(bodyGeo, bodyMat);
                body.position.y = 0.5;
                body.castShadow = true;
                carGroup.add(body);

                const cabinGeo = new THREE.BoxGeometry(1.4, 0.6, 1.6);
                const cabinMat = new THREE.MeshLambertMaterial({{ color: 0x111111 }});
                const cabin = new THREE.Mesh(cabinGeo, cabinMat);
                cabin.position.set(0, 1.0, -0.2);
                carGroup.add(cabin);

                scene.add(carGroup);
                return carGroup;
            }}

            const car1 = createCar(0xff3333); // Red (P1)
            const car2 = createCar(0x3388ff); // Blue (P2 / AI)

            // Track Coordinates Sampling for Collision & AI Navigation
            const trackPoints = trackCurve.getSpacedPoints(200);

            function getClosestTrackPoint(pos) {{
                let minDistance = Infinity;
                let closestPt = trackPoints[0];
                for (let i = 0; i < trackPoints.length; i++) {{
                    const dist = pos.distanceTo(trackPoints[i]);
                    if (dist < minDistance) {{
                        minDistance = dist;
                        closestPt = trackPoints[i];
                    }}
                }}
                return {{ point: closestPt, distance: minDistance }};
            }}

            // State Initialization
            const startPt = trackPoints[0];
            const p1State = {{ x: startPt.x - 2, z: startPt.z, angle: 0, speed: 0, lap: 0, crossed: false }};
            const p2State = {{ x: startPt.x + 2, z: startPt.z, angle: 0, speed: 0, lap: 0, progressIdx: 0 }};
            const maxSpeed = 0.28 + ({speed_lvl} * 0.10);
            const isCPU = {"true" if is_cpu else "false"};

            let raceStarted = false;
            let startTime = 0;
            let elapsedTime = 0;
            let timerInterval = null;

            function startRace() {{
                document.getElementById('start-btn').style.display = 'none';
                let countdown = 3;
                const statusElem = document.getElementById('game-status');
                
                const countInterval = setInterval(() => {{
                    if (countdown > 0) {{
                        statusElem.innerText = "🚦 GET READY... " + countdown;
                        countdown--;
                    }} else {{
                        clearInterval(countInterval);
                        statusElem.innerText = "🟢 GO! RACE IN PROGRESS!";
                        raceStarted = true;
                        startTime = Date.now();
                    }}
                }}, 1000);
            }}

            const keys = {{}};
            window.addEventListener('keydown', e => keys[e.key] = true);
            window.addEventListener('keyup', e => keys[e.key] = false);

            // Car Physics & Track Boundary Collision Detection
            function updatePhysics(carMesh, state, forwardKey, leftKey, rightKey, backKey) {{
                if (!raceStarted) return;

                const nextSpeed = keys[forwardKey] ? Math.min(state.speed + 0.012, maxSpeed) :
                                  keys[backKey] ? Math.max(state.speed - 0.01, -maxSpeed * 0.4) :
                                  state.speed * 0.95;

                if (keys[leftKey] && Math.abs(state.speed) > 0.01) state.angle += 0.045;
                if (keys[rightKey] && Math.abs(state.speed) > 0.01) state.angle -= 0.045;

                const nextX = state.x + Math.sin(state.angle) * nextSpeed;
                const nextZ = state.z + Math.cos(state.angle) * nextSpeed;
                const testPos = new THREE.Vector3(nextX, 0, nextZ);

                // Check distance from central track spline curve
                const trackCheck = getClosestTrackPoint(testPos);
                if (trackCheck.distance <= trackWidth - 1.2) {{ // Keep strictly on track surface
                    state.x = nextX;
                    state.z = nextZ;
                    state.speed = nextSpeed;
                }} else {{ // Collided with edge boundary: bounce back and reset speed
                    state.speed = -state.speed * 0.3;
                }}

                carMesh.position.set(state.x, 0, state.z);
                carMesh.rotation.y = state.angle;

                // Lap Counter Detection
                const distToStart = testPos.distanceTo(startPt);
                if (distToStart < 6) {{
                    if (!state.crossed) {{
                        state.lap++;
                        state.crossed = true;
                    }}
                }} else {{
                    state.crossed = false;
                }}
            }}

            // AI Opponent Autonomous Driving System
            function updateAIBot() {{
                if (!raceStarted) return;
                
                const targetPt = trackPoints[p2State.progressIdx];
                const dx = targetPt.x - p2State.x;
                const dz = targetPt.z - p2State.z;
                const targetAngle = Math.atan2(dx, dz);

                p2State.angle = targetAngle;
                p2State.speed = maxSpeed * 0.85;
                p2State.x += Math.sin(p2State.angle) * p2State.speed;
                p2State.z += Math.cos(p2State.angle) * p2State.speed;

                car2.position.set(p2State.x, 0, p2State.z);
                car2.rotation.y = p2State.angle;

                if (new THREE.Vector3(p2State.x, 0, p2State.z).distanceTo(targetPt) < 4) {{
                    p2State.progressIdx = (p2State.progressIdx + 1) % trackPoints.length;
                    if (p2State.progressIdx === 0) p2State.lap++;
                }}
            }}

            // Camera Control
            const camView = "{camera_view}";
            function updateCamera() {{
                if (camView === "Chase Cam (Behind)") {{
                    camera.position.x = car1.position.x - Math.sin(p1State.angle) * 14;
                    camera.position.z = car1.position.z - Math.cos(p1State.angle) * 14;
                    camera.position.y = car1.position.y + 7;
                    camera.lookAt(car1.position.x, car1.position.y + 1, car1.position.z);
                }} else if (camView === "Third-Person (High)") {{
                    camera.position.set(0, 50, 50);
                    camera.lookAt(0, 0, 0);
                }} else {{
                    camera.position.set(0, 80, 0.1);
                    camera.lookAt(0, 0, 0);
                }}
            }}

            // Main Animation Render Loop
            function animate() {{
                requestAnimationFrame(animate);

                updatePhysics(car1, p1State, 'w', 'a', 'd', 's');
                if (isCPU) {{
                    updateAIBot();
                }} else {{
                    updatePhysics(car2, p2State, 'ArrowUp', 'ArrowLeft', 'ArrowRight', 'ArrowDown');
                }}

                if (raceStarted && p1State.lap < 3 && p2State.lap < 3) {{
                    elapsedTime = ((Date.now() - startTime) / 1000).toFixed(1);
                    document.getElementById('timer-display').innerText = elapsedTime + "s";
                }}

                document.getElementById('p1-hud').innerText = "{p1_driver}: Lap " + Math.min(p1State.lap, 3) + "/3";
                document.getElementById('p2-hud').innerText = "{p2_driver}: Lap " + Math.min(p2State.lap, 3) + "/3";

                if (p1State.lap >= 3 || p2State.lap >= 3) {{
                    raceStarted = false;
                    const winner = p1State.lap >= 3 ? "{p1_driver}" : "{p2_driver}";
                    document.getElementById('game-status').innerText = "🏆 WINNER: " + winner + " (" + elapsedTime + "s)!";
                }}

                updateCamera();
                renderer.render(scene, camera);
            }}

            animate();
        </script>
    </body>
    </html>
    """

    components.html(threejs_html, height=550)

    # Score Submission Section
    st.subheader("🏁 Submit Match Score")
    sc_col1, sc_col2, sc_col3 = st.columns([2, 2, 1])
    
    with sc_col1:
        winner_name = st.selectbox("Race Winner:", [p1_driver, p2_driver], key="winner_drop")
    with sc_col2:
        finish_sec = st.number_input("Finish Time (Seconds):", min_value=5.0, max_value=300.0, value=22.5, step=0.5)
    with sc_col3:
        st.write("")
        st.write("")
        if st.button("Save Result", use_container_width=True):
            record_win(winner_name, finish_sec, speed_lvl)
            st.success(f"Score recorded for {winner_name}!")

# --- TAB 3: GAME LOBBIES ---
with tab_lobbies:
    st.subheader("🌐 Active Open Racing Lobbies")
    lobby_data = []
    for session_id, details in st.session_state.sessions.items():
        lobby_data.append({
            "Session Name": session_id,
            "Host Player": details["host"],
            "Players Joined": f"{len(details['players'])} / {details['max']}",
            "Status": details["status"]
        })
    st.dataframe(pd.DataFrame(lobby_data), use_container_width=True)

    st.divider()
    st.subheader("Create or Join a Session")
    l_col1, l_col2 = st.columns(2)

    with l_col1:
        new_lobby_name = st.text_input("New Session Name:", placeholder="e.g. Session #103")
        if st.button("Create Open Session"):
            if new_lobby_name.strip():
                st.session_state.sessions[new_lobby_name.strip()] = {
                    "host": st.session_state.current_user,
                    "players": [st.session_state.current_user],
                    "max": 2,
                    "status": "Waiting"
                }
                st.success(f"Session '{new_lobby_name}' created successfully!")
            else:
                st.warning("Please provide a session title.")

    with l_col2:
        target_lobby = st.selectbox("Select Lobby to Join:", list(st.session_state.sessions.keys()))
        if st.button("Join Gaming Session"):
            lobby = st.session_state.sessions[target_lobby]
            if len(lobby["players"]) < lobby["max"]:
                if st.session_state.current_user not in lobby["players"]:
                    lobby["players"].append(st.session_state.current_user)
                    if len(lobby["players"]) == lobby["max"]:
                        lobby["status"] = "In Progress"
                    st.success(f"Joined {target_lobby}!")
                else:
                    st.info("You are already in this session.")
            else:
                st.error("Session is already full!")

# --- TAB 4: LEADERBOARD ---
with tab_ranks:
    st.subheader("🏆 Driver Global Rankings")
    if st.session_state.leaderboard:
        df_rank = pd.DataFrame.from_dict(st.session_state.leaderboard, orient="index")
        df_rank.index.name = "Driver Name"
        df_rank = df_rank.sort_values(by=["Total Points", "Fastest Time (s)"], ascending=[False, True])
        st.dataframe(df_rank.style.highlight_max(axis=0, subset=["Total Points"], color="#2e7d32"), use_container_width=True)
    else:
        st.info("No recorded match results yet. Complete a race in the Arena to post scores!")
