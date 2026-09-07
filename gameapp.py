# Save this file as exporter.py and run: python exporter.py

app_code = """import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# Page Configuration
st.set_page_config(
    page_title="3D Turbo Racing League", layout="wide", page_icon="🏎️"
)

# Custom High-Contrast Styling
st.markdown(\"\"\"
<style>
    .stApp {
        background: linear-gradient(rgba(10, 10, 15, 0.75), rgba(10, 10, 15, 0.85)), 
                    url('https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }
    
    html, body, [class*="css"], .stMarkdown, h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #FFFFFF !important;
        text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.9);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(20, 20, 30, 0.9);
        border-radius: 8px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #E0E0E0 !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #00FFCC !important;
        border-bottom-color: #00FFCC !important;
    }
    
    input, select, textarea, div[role="combobox"] {
        color: #FFFFFF !important;
        background-color: rgba(25, 30, 40, 0.95) !important;
    }
</style>
\"\"\", unsafe_allow_html=True)

# State Management
if "sessions" not in st.session_state:
    st.session_state.sessions = {
        "Session #101 (Night Track)": {"host": "ProRacer", "players": ["ProRacer"], "max": 2, "status": "Waiting"},
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

st.title("🏎️ 3D Low-Poly Racing Engine")
st.caption("Arrow Keys: Steering & Throttle | Spacebar: Nitro Boost | WebAudio Engine Revs & Particle FX")

tab_player, tab_arena, tab_lobbies, tab_ranks = st.tabs([
    "👤 Player Setup", "🏁 Immersive 3D Arena", "🌐 Game Lobbies", "🏆 Leaderboard"
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

# --- TAB 2: IMMERSIVE 3D ARENA ---
with tab_arena:
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.2, 1, 1, 1.2])
    
    with col1:
        p1_driver = st.text_input("Player 1 (Red Car):", value=st.session_state.current_user, key="p1_val")
    with col2:
        p2_input = st.text_input("Player 2 (Leave blank for AI Bot):", value="", key="p2_val", placeholder="AI Bot (Auto-Drive)")
        p2_driver = p2_input.strip() if p2_input.strip() else "CPU_Bot (AI)"
        is_cpu = not bool(p2_input.strip())
    with col3:
        level_choice = st.selectbox("Track Level:", [1, 2, 3], format_func=lambda x: f"Level {x} " + ("(Oval)" if x==1 else "(Figure 8)" if x==2 else "(Circuit)"))
    with col4:
        speed_lvl = st.slider("Engine Power", 1, 5, 3, key="speed_setting")
    with col5:
        camera_view = st.selectbox("3D Camera:", ["Chase Cam (Behind)", "Third-Person (High)", "Top-Down (Map)"])

    st.markdown(
        f"**🎮 Mode:** {'**Player vs AI Bot**' if is_cpu else '**2-Player Local**'} | "
        "**Controls:** **P1:** `Up` (Gas), `Left`/`Right` (Steer), `Down` (Brake/Reverse), `Space` (Nitro Boost)"
    )

    # Immersive Three.js Engine
    threejs_html = f\"\"\"
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #05050a; font-family: 'Segoe UI', sans-serif; }}
            #hud {{ 
                position: absolute; top: 12px; left: 12px; color: #fff; 
                font-weight: bold; font-size: 14px; text-shadow: 2px 2px 4px #000; z-index: 10;
                background: rgba(10, 12, 20, 0.75); padding: 12px 18px; border-radius: 8px;
                border: 1px solid rgba(0,255,204,0.3); backdrop-filter: blur(4px);
            }}
            #start-btn {{
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                padding: 18px 42px; font-size: 24px; font-weight: bold; color: #fff;
                background: linear-gradient(45deg, #ff0055, #ff5500); border: none; border-radius: 12px; cursor: pointer;
                box-shadow: 0 0 25px rgba(255,0,85,0.6); z-index: 20; transition: all 0.2s;
            }}
            #start-btn:hover {{ transform: translate(-50%, -50%) scale(1.05); }}
            canvas {{ display: block; width: 100vw; height: 550px; }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <button id="start-btn" onclick="startRace()">🏁 START RACE</button>
        <div id="hud">
            🏎️ Level {level_choice} Track | Engine Power: {speed_lvl}<br>
            ⏱️ Time: <span id="timer-display" style="color:#00ffcc;">0.0s</span><br>
            <span id="p1-hud" style="color: #ff4444;">{p1_driver}: Lap 0/3</span> | 
            <span id="p2-hud" style="color: #4488ff;">{p2_driver}: Lap 0/3</span><br>
            <span id="game-status" style="color: #ffcc00;">Click START RACE to enable Audio & Ignition!</span>
        </div>
        <script>
            // Audio Engine using Web Audio API
            let audioCtx, osc, gainNode;
            function initAudio() {{
                if (!audioCtx) {{
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    osc = audioCtx.createOscillator();
                    gainNode = audioCtx.createGain();
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(60, audioCtx.currentTime);
                    gainNode.gain.setValueAtTime(0.05, audioCtx.currentTime);
                    osc.connect(gainNode);
                    gainNode.connect(audioCtx.destination);
                    osc.start();
                }}
            }}
            function updateEngineSound(speedRatio) {{
                if (audioCtx && osc) {{
                    const pitch = 60 + (speedRatio * 220);
                    osc.frequency.setTargetAtTime(pitch, audioCtx.currentTime, 0.05);
                }}
            }}

            // Three.js Scene Setup
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0a12);
            scene.fog = new THREE.FogExp2(0x0a0a12, 0.008);

            const camera = new THREE.PerspectiveCamera(60, window.innerWidth / 550, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, 550);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            document.body.appendChild(renderer.domElement);

            // Lighting Setup
            const ambientLight = new THREE.AmbientLight(0x222233, 0.8);
            scene.add(ambientLight);
            
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
            dirLight.position.set(50, 100, 50);
            dirLight.castShadow = true;
            scene.add(dirLight);

            // Ground Track Base
            const groundGeo = new THREE.PlaneGeometry(300, 300);
            const groundMat = new THREE.MeshStandardMaterial({{ color: 0x081008, roughness: 0.9 }});
            const ground = new THREE.Mesh(groundGeo, groundMat);
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
            scene.add(ground);

            // Level Track Generation
            const level = {level_choice};
            let trackCurve;
            const trackWidth = 8;

            if (level === 1) {{
                trackCurve = new THREE.CatmullRomCurve3([
                    new THREE.Vector3(-35, 0, 25), new THREE.Vector3(35, 0, 25),
                    new THREE.Vector3(50, 0, 0), new THREE.Vector3(35, 0, -25),
                    new THREE.Vector3(-35, 0, -25), new THREE.Vector3(-50, 0, 0)
                ], true);
            }} else if (level === 2) {{
                trackCurve = new THREE.CatmullRomCurve3([
                    new THREE.Vector3(-40, 0, 30), new THREE.Vector3(0, 0, 0),
                    new THREE.Vector3(40, 0, -30), new THREE.Vector3(50, 0, 0),
                    new THREE.Vector3(40, 0, 30), new THREE.Vector3(0, 0, 0),
                    new THREE.Vector3(-40, 0, -30), new THREE.Vector3(-50, 0, 0)
                ], true);
            }} else {{
                trackCurve = new THREE.CatmullRomCurve3([
                    new THREE.Vector3(-45, 0, 35), new THREE.Vector3(15, 0, 40),
                    new THREE.Vector3(45, 0, 20), new THREE.Vector3(25, 0, -15),
                    new THREE.Vector3(-45, 0, -40), new THREE.Vector3(-15, 0, -30),
                    new THREE.Vector3(-40, 0, -40), new THREE.Vector3(-30, 0, 0)
                ], true);
            }}

            const trackGeo = new THREE.TubeGeometry(trackCurve, 150, trackWidth, 8, true);
            const trackMat = new THREE.MeshStandardMaterial({{ color: 0x222228, roughness: 0.4, metalness: 0.1 }});
            const trackMesh = new THREE.Mesh(trackGeo, trackMat);
            trackMesh.scale.set(1, 0.01, 1);
            trackMesh.position.y = 0.02;
            scene.add(trackMesh);

            // Detailed Vehicle Factory
            function createCar(colorHex) {{
                const carGroup = new THREE.Group();
                
                // Chassis
                const bodyGeo = new THREE.BoxGeometry(2.0, 0.6, 3.8);
                const bodyMat = new THREE.MeshStandardMaterial({{ color: colorHex, roughness: 0.2, metalness: 0.5 }});
                const body = new THREE.Mesh(bodyGeo, bodyMat);
                body.position.y = 0.5;
                body.castShadow = true;
                carGroup.add(body);

                // Cabin
                const cabinGeo = new THREE.BoxGeometry(1.5, 0.5, 1.8);
                const cabinMat = new THREE.MeshStandardMaterial({{ color: 0x050505, roughness: 0.1 }});
                const cabin = new THREE.Mesh(cabinGeo, cabinMat);
                cabin.position.set(0, 0.9, -0.2);
                carGroup.add(cabin);

                // Headlights
                const headlightMat = new THREE.MeshBasicMaterial({{ color: 0xffffaa }});
                const hl1 = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.15, 0.1), headlightMat);
                hl1.position.set(-0.7, 0.5, 1.9);
                const hl2 = hl1.clone();
                hl2.position.set(0.7, 0.5, 1.9);
                carGroup.add(hl1);
                carGroup.add(hl2);

                // Spotlights Beam
                const spotLight = new THREE.SpotLight(0xffffaa, 2, 25, Math.PI / 6, 0.5);
                spotLight.position.set(0, 0.6, 1.8);
                spotLight.target.position.set(0, 0, 10);
                carGroup.add(spotLight);
                carGroup.add(spotLight.target);

                scene.add(carGroup);
                return carGroup;
            }}

            const car1 = createCar(0xff2244);
            const car2 = createCar(0x2288ff);

            // Particles System (Tire Smoke & Nitro Flame)
            const particles = [];
            function createParticle(x, y, z, colorHex) {{
                const pGeo = new THREE.SphereGeometry(0.15 + Math.random() * 0.1, 4, 4);
                const pMat = new THREE.MeshBasicMaterial({{ color: colorHex, transparent: true, opacity: 0.8 }});
                const p = new THREE.Mesh(pGeo, pMat);
                p.position.set(x, y, z);
                scene.add(p);
                particles.push({{ mesh: p, life: 1.0 }});
            }}

            function updateParticles() {{
                for (let i = particles.length - 1; i >= 0; i--) {{
                    const p = particles[i];
                    p.life -= 0.04;
                    p.mesh.scale.multiplyScalar(1.05);
                    p.mesh.material.opacity = p.life;
                    if (p.life <= 0) {{
                        scene.remove(p.mesh);
                        particles.splice(i, 1);
                    }}
                }}
            }}

            // Track Coordinates Sampling
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

            const startPt = trackPoints[0];
            const p1State = {{ x: startPt.x - 2, z: startPt.z, angle: 0, speed: 0, lap: 0, crossed: false }};
            const p2State = {{ x: startPt.x + 2, z: startPt.z, angle: 0, speed: 0, lap: 0, progressIdx: 0 }};
            const baseMaxSpeed = 0.28 + ({speed_lvl} * 0.10);
            const isCPU = {"true" if is_cpu else "false"};

            let raceStarted = false;
            let startTime = 0;
            let elapsedTime = 0;

            function startRace() {{
                initAudio();
                document.getElementById('start-btn').style.display = 'none';
                let countdown = 3;
                const statusElem = document.getElementById('game-status');
                
                const countInterval = setInterval(() => {{
                    if (countdown > 0) {{
                        statusElem.innerText = "🚦 GET READY... " + countdown;
                        countdown--;
                    }} else {{
                        clearInterval(countInterval);
                        statusElem.innerText = "🟢 GO! NITRO ACTIVE!";
                        raceStarted = true;
                        startTime = Date.now();
                    }}
                }}, 1000);
            }}

            const keys = {{}};
            window.addEventListener('keydown', e => keys[e.key] = true);
            window.addEventListener('keyup', e => keys[e.key] = false);

            function updatePhysics(carMesh, state, forwardKey, leftKey, rightKey, backKey, nitroKey) {{
                if (!raceStarted) return;

                const isNitro = keys[nitroKey];
                const currentMax = isNitro ? baseMaxSpeed * 1.4 : baseMaxSpeed;

                const nextSpeed = keys[forwardKey] ? Math.min(state.speed + 0.015, currentMax) :
                                  keys[backKey] ? Math.max(state.speed - 0.012, -currentMax * 0.4) :
                                  state.speed * 0.95;

                if (keys[leftKey] && Math.abs(state.speed) > 0.01) state.angle += 0.045;
                if (keys[rightKey] && Math.abs(state.speed) > 0.01) state.angle -= 0.045;

                const nextX = state.x + Math.sin(state.angle) * nextSpeed;
                const nextZ = state.z + Math.cos(state.angle) * nextSpeed;
                const testPos = new THREE.Vector3(nextX, 0, nextZ);

                const trackCheck = getClosestTrackPoint(testPos);
                if (trackCheck.distance <= trackWidth - 1.2) {{
                    state.x = nextX;
                    state.z = nextZ;
                    state.speed = nextSpeed;
                }} else {{
                    state.speed = -state.speed * 0.3; // Wall bounce
                    createParticle(state.x, 0.5, state.z, 0xffaa00);
                }}

                carMesh.position.set(state.x, 0, state.z);
                carMesh.rotation.y = state.angle;

                // Nitro & Smoke FX
                if (isNitro && state.speed > 0.1) {{
                    createParticle(state.x - Math.sin(state.angle)*1.5, 0.4, state.z - Math.cos(state.angle)*1.5, 0x00d2ff);
                }} else if (Math.abs(state.speed) > 0.2) {{
                    if (Math.random() < 0.3) createParticle(state.x, 0.2, state.z, 0x888888);
                }}

                // Sound Pitch Feedback
                updateEngineSound(Math.abs(state.speed) / baseMaxSpeed);

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

            let botErrorOffset = 0;
            let mistakeTimer = 0;

            function updateAIBot() {{
                if (!raceStarted) return;
                
                const targetPt = trackPoints[p2State.progressIdx];
                const dx = targetPt.x - p2State.x;
                const dz = targetPt.z - p2State.z;
                
                mistakeTimer++;
                if (mistakeTimer % 120 === 0) botErrorOffset = (Math.random() - 0.5) * 0.3;

                const targetAngle = Math.atan2(dx, dz) + botErrorOffset;
                p2State.angle += (targetAngle - p2State.angle) * 0.1;
                
                const botMaxSpeed = baseMaxSpeed * 0.70;
                p2State.speed = Math.min(p2State.speed + 0.006, botMaxSpeed);

                const nextX = p2State.x + Math.sin(p2State.angle) * p2State.speed;
                const nextZ = p2State.z + Math.cos(p2State.angle) * p2State.speed;
                
                p2State.x = nextX;
                p2State.z = nextZ;

                car2.position.set(p2State.x, 0, p2State.z);
                car2.rotation.y = p2State.angle;

                if (new THREE.Vector3(p2State.x, 0, p2State.z).distanceTo(targetPt) < 5) {{
                    p2State.progressIdx = (p2State.progressIdx + 1) % trackPoints.length;
                    if (p2State.progressIdx === 0) p2State.lap++;
                }}
            }}

            const camView = "{camera_view}";
            function updateCamera() {{
                if (camView === "Chase Cam (Behind)") {{
                    camera.position.x = car1.position.x - Math.sin(p1State.angle) * 12;
                    camera.position.z = car1.position.z - Math.cos(p1State.angle) * 12;
                    camera.position.y = car1.position.y + 6;
                    camera.lookAt(car1.position.x, car1.position.y + 1, car1.position.z);
                }} else if (camView === "Third-Person (High)") {{
                    camera.position.set(0, 50, 50);
                    camera.lookAt(0, 0, 0);
                }} else {{
                    camera.position.set(0, 80, 0.1);
                    camera.lookAt(0, 0, 0);
                }}
            }}

            function animate() {{
                requestAnimationFrame(animate);

                updatePhysics(car1, p1State, 'ArrowUp', 'ArrowLeft', 'ArrowRight', 'ArrowDown', ' ');
                
                if (isCPU) {{
                    updateAIBot();
                }} else {{
                    updatePhysics(car2, p2State, 'w', 'a', 'd', 's', 'Shift');
                }}

                updateParticles();

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
    \"\"\"

    components.html(threejs_html, height=580)

    st.subheader("🏁 Submit Match Score")
    sc_col1, sc_col2, sc_col3 = st.columns([2, 2, 1])
    
    with sc_col1:
        winner_name = st.selectbox("Race Winner:", [p1_driver, p2_driver], key="winner_drop")
    with sc_col2:
        finish_sec = st.number_input("Finish Time (Seconds):", min_value=5.0, max_value=300.0, value=20.0, step=0.5)
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
        new_lobby_name = st.text_input("New Session Name:", placeholder="e.g. Night Circuit #103")
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
"""

req_code = """streamlit>=1.28.0
pandas>=2.0.0
"""

with open("app.py", "w") as f:
    f.write(app_code)

with open("requirements.txt", "w") as f:
    f.write(req_code)

print("Export Complete! Run 'streamlit run app.py' to launch.")