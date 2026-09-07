# Save this file as exporter.py and run: python exporter.py

app_code = """import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json

# Page Configuration
st.set_page_config(
    page_title="3D Turbo Racing League", layout="wide", page_icon="🏎️"
)

# Custom Bright / High-Visibility Light Styling
st.markdown(\"\"\"
<style>
    .stApp {
        background: #F4F6F9;
    }
    
    html, body, [class*="css"], .stMarkdown, h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #1A1D20 !important;
        text-shadow: none !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: #E2E8F0;
        border-radius: 8px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #4A5568 !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #2B6CB0 !important;
        border-bottom-color: #2B6CB0 !important;
    }
    
    input, select, textarea, div[role="combobox"] {
        color: #1A1D20 !important;
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E0 !important;
    }
</style>
\"\"\", unsafe_allow_html=True)

# State Management
if "registered_users" not in st.session_state:
    st.session_state.registered_users = ["ProRacer", "DriftKing", "TurboMax"]

if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = {
        "ProRacer": {"Wins": 3, "Total Points": 450, "Fastest Time (s)": 18.4, "Races": 3},
        "DriftKing": {"Wins": 1, "Total Points": 150, "Fastest Time (s)": 21.2, "Races": 2}
    }

if "current_user" not in st.session_state:
    st.session_state.current_user = "ProRacer"

if "sessions" not in st.session_state:
    st.session_state.sessions = {
        "Session #101 (Daylight Circuit)": {"host": "ProRacer", "players": ["ProRacer"], "max": 2, "status": "Waiting"},
        "Session #102 (Sunburst Oval)": {"host": "DriftKing", "players": ["DriftKing"], "max": 2, "status": "Waiting"}
    }

def record_race_results(winner, loser, winner_time, speed_lvl):
    if winner not in st.session_state.leaderboard:
        st.session_state.leaderboard[winner] = {"Wins": 0, "Total Points": 0, "Fastest Time (s)": 999.0, "Races": 0}
    w_entry = st.session_state.leaderboard[winner]
    w_entry["Wins"] += 1
    w_entry["Total Points"] += 150 * speed_lvl
    w_entry["Races"] += 1
    if winner_time < w_entry["Fastest Time (s)"]:
        w_entry["Fastest Time (s)"] = round(winner_time, 2)

    if loser not in st.session_state.leaderboard:
        st.session_state.leaderboard[loser] = {"Wins": 0, "Total Points": 0, "Fastest Time (s)": 999.0, "Races": 0}
    l_entry = st.session_state.leaderboard[loser]
    l_entry["Total Points"] += 50 * speed_lvl
    l_entry["Races"] += 1

st.title("🏎️ 3D Turbo Racing League")
st.caption("Arrow Keys: Steering & Throttle | Spacebar: Nitro Boost | WebAudio Engine & Live Leaderboards")

tab_player, tab_arena, tab_ranks, tab_lobbies = st.tabs([
    "👤 Player Setup", "🏁 3D Race Arena", "🏆 Live Leaderboard", "🌐 Game Lobbies"
])

# --- TAB 1: PLAYER SETUP ---
with tab_player:
    st.subheader("Register or Select Active Driver Profile")
    col_a, col_b = st.columns(2)
    
    with col_a:
        new_name = st.text_input("Create Driver Profile:", placeholder="e.g. ApexPredator")
        if st.button("Save & Select Name"):
            if new_name.strip():
                clean_name = new_name.strip()
                if clean_name not in st.session_state.registered_users:
                    st.session_state.registered_users.append(clean_name)
                st.session_state.current_user = clean_name
                st.success(f"Active Profile Set To: **{clean_name}**")
            else:
                st.warning("Please enter a valid name.")

    with col_b:
        selected_profile = st.selectbox(
            "Select Existing Driver Profile:",
            st.session_state.registered_users,
            index=0 if st.session_state.current_user not in st.session_state.registered_users 
            else st.session_state.registered_users.index(st.session_state.current_user)
        )
        if st.button("Switch Profile"):
            st.session_state.current_user = selected_profile
            st.info(f"Switched Driver To: **{selected_profile}**")

    st.divider()
    st.markdown(f"**Current Driver Active:** `{st.session_state.current_user}`")

# --- TAB 2: 3D ARENA ---
with tab_arena:
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.2, 1, 1, 1.2])
    
    with col1:
        p1_driver = st.text_input("Player 1 (Red Car):", value=st.session_state.current_user, key="p1_val")
    with col2:
        p2_input = st.text_input("Player 2 (Leave blank for AI):", value="", key="p2_val", placeholder="AI Bot (Auto-Drive)")
        p2_driver = p2_input.strip() if p2_input.strip() else "CPU_Bot (AI)"
        is_cpu = not bool(p2_input.strip())
    with col3:
        level_choice = st.selectbox("Track Level:", [1, 2, 3], format_func=lambda x: f"Level {x} " + ("(Oval)" if x==1 else "(Figure 8)" if x==2 else "(Circuit)"))
    with col4:
        speed_lvl = st.slider("Engine Power", 1, 5, 3, key="speed_setting")
    with col5:
        camera_view = st.selectbox("3D Camera:", ["Chase Cam (Behind)", "Third-Person (High)", "Top-Down (Map)"])

    # Three.js Game Engine with Bright Lighting
    threejs_html = f\"\"\"
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #87CEEB; font-family: 'Segoe UI', sans-serif; }}
            #hud {{ 
                position: absolute; top: 12px; left: 12px; color: #101828; 
                font-weight: bold; font-size: 14px; z-index: 10;
                background: rgba(255, 255, 255, 0.92); padding: 12px 18px; border-radius: 8px;
                border: 2px solid #2563EB; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            #start-btn {{
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                padding: 18px 42px; font-size: 24px; font-weight: bold; color: #fff;
                background: linear-gradient(45deg, #059669, #10B981); border: none; border-radius: 12px; cursor: pointer;
                box-shadow: 0 4px 20px rgba(16,185,129,0.5); z-index: 20; transition: all 0.2s;
            }}
            #start-btn:hover {{ transform: translate(-50%, -50%) scale(1.05); }}
            #end-modal {{
                display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                width: 80%; max-width: 500px; background: rgba(255, 255, 255, 0.98); border: 3px solid #2563EB;
                border-radius: 16px; padding: 24px; text-align: center; color: #1E293B; z-index: 30;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
            }}
            .winner-box {{ background: #ECFDF5; border: 2px solid #10B981; padding: 15px; border-radius: 10px; margin-bottom: 12px; color: #065F46; }}
            .loser-box {{ background: #FEF2F2; border: 2px solid #EF4444; padding: 15px; border-radius: 10px; color: #991B1B; }}
            canvas {{ display: block; width: 100vw; height: 550px; }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <button id="start-btn" onclick="startRace()">🔊 START RACE</button>
        <div id="hud">
            🏎️ Track Level {level_choice} | Power Level: {speed_lvl}<br>
            ⏱️ Time: <span id="timer-display" style="color:#2563EB;">0.0s</span><br>
            <span id="p1-hud" style="color: #DC2626;">{p1_driver}: Lap 0/3</span> | 
            <span id="p2-hud" style="color: #2563EB;">{p2_driver}: Lap 0/3</span><br>
            <span id="game-status" style="color: #D97706;">Click START RACE to begin!</span>
        </div>

        <div id="end-modal">
            <div class="winner-box">
                <h2 style="margin:0 0 8px 0;">🏆 CONGRATULATIONS!</h2>
                <div id="winner-text" style="font-size:18px; font-weight:bold;"></div>
            </div>
            <div class="loser-box">
                <h3 style="margin:0 0 6px 0;">💔 HARD LUCK!</h3>
                <div id="loser-text" style="font-size:15px;"></div>
            </div>
        </div>

        <script>
            let audioCtx, engineOsc1, engineOsc2, engineGain, squealGain, squealOsc, nitroGain, nitroNoise;

            function initAudio() {{
                if (audioCtx) return;
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();

                engineOsc1 = audioCtx.createOscillator();
                engineOsc2 = audioCtx.createOscillator();
                engineGain = audioCtx.createGain();

                engineOsc1.type = 'sawtooth';
                engineOsc2.type = 'triangle';
                
                engineOsc1.frequency.setValueAtTime(45, audioCtx.currentTime);
                engineOsc2.frequency.setValueAtTime(22.5, audioCtx.currentTime);
                engineGain.gain.setValueAtTime(0.08, audioCtx.currentTime);

                engineOsc1.connect(engineGain);
                engineOsc2.connect(engineGain);
                engineGain.connect(audioCtx.destination);

                engineOsc1.start();
                engineOsc2.start();

                squealOsc = audioCtx.createOscillator();
                squealGain = audioCtx.createGain();
                squealOsc.type = 'sine';
                squealOsc.frequency.setValueAtTime(850, audioCtx.currentTime);
                squealGain.gain.setValueAtTime(0.0, audioCtx.currentTime);

                squealOsc.connect(squealGain);
                squealGain.connect(audioCtx.destination);
                squealOsc.start();

                const bufferSize = audioCtx.sampleRate * 2;
                const noiseBuffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
                const output = noiseBuffer.getChannelData(0);
                for (let i = 0; i < bufferSize; i++) {{
                    output[i] = Math.random() * 2 - 1;
                }}

                nitroNoise = audioCtx.createBufferSource();
                nitroNoise.buffer = noiseBuffer;
                nitroNoise.loop = true;

                nitroGain = audioCtx.createGain();
                nitroGain.gain.setValueAtTime(0.0, audioCtx.currentTime);

                nitroNoise.connect(nitroGain);
                nitroGain.connect(audioCtx.destination);
                nitroNoise.start();
            }}

            function playCrashSound() {{
                if (!audioCtx) return;
                const crashOsc = audioCtx.createOscillator();
                const crashGain = audioCtx.createGain();
                crashOsc.type = 'square';
                crashOsc.frequency.setValueAtTime(100, audioCtx.currentTime);
                crashOsc.frequency.exponentialRampToValueAtTime(20, audioCtx.currentTime + 0.2);
                crashGain.gain.setValueAtTime(0.2, audioCtx.currentTime);
                crashGain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.2);

                crashOsc.connect(crashGain);
                crashGain.connect(audioCtx.destination);
                crashOsc.start();
                crashOsc.stop(audioCtx.currentTime + 0.2);
            }}

            function updateAudio(speedRatio, isTurning, isNitro) {{
                if (!audioCtx) return;
                const baseFreq = 45 + (speedRatio * 260);
                engineOsc1.frequency.setTargetAtTime(baseFreq, audioCtx.currentTime, 0.05);
                engineOsc2.frequency.setTargetAtTime(baseFreq * 0.5, audioCtx.currentTime, 0.05);

                const targetSqueal = (isTurning && speedRatio > 0.3) ? 0.08 : 0.0;
                squealGain.gain.setTargetAtTime(targetSqueal, audioCtx.currentTime, 0.05);

                const targetNitro = isNitro ? 0.15 : 0.0;
                nitroGain.gain.setTargetAtTime(targetNitro, audioCtx.currentTime, 0.05);
            }}

            // Three.js Scene Setup (High Visibility Light Environment)
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x99D9EA); // Bright Daylight Sky

            const camera = new THREE.PerspectiveCamera(60, window.innerWidth / 550, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, 550);
            renderer.shadowMap.enabled = true;
            document.body.appendChild(renderer.domElement);

            // Bright Daylight Lights
            const ambientLight = new THREE.AmbientLight(0xFFFFFF, 1.2);
            scene.add(ambientLight);
            
            const sunLight = new THREE.DirectionalLight(0xFFFFFF, 1.5);
            sunLight.position.set(50, 120, 50);
            sunLight.castShadow = true;
            scene.add(sunLight);

            // Grass Terrain
            const groundGeo = new THREE.PlaneGeometry(300, 300);
            const groundMat = new THREE.MeshStandardMaterial({{ color: 0x4CAF50, roughness: 0.8 }});
            const ground = new THREE.Mesh(groundGeo, groundMat);
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
            scene.add(ground);

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

            // High-Contrast Road Surface
            const trackGeo = new THREE.TubeGeometry(trackCurve, 150, trackWidth, 8, true);
            const trackMat = new THREE.MeshStandardMaterial({{ color: 0x333338, roughness: 0.3 }});
            const trackMesh = new THREE.Mesh(trackGeo, trackMat);
            trackMesh.scale.set(1, 0.01, 1);
            trackMesh.position.y = 0.02;
            scene.add(trackMesh);

            function createCar(colorHex) {{
                const carGroup = new THREE.Group();
                const bodyGeo = new THREE.BoxGeometry(2.0, 0.6, 3.8);
                const bodyMat = new THREE.MeshStandardMaterial({{ color: colorHex, roughness: 0.2, metalness: 0.6 }});
                const body = new THREE.Mesh(bodyGeo, bodyMat);
                body.position.y = 0.5;
                body.castShadow = true;
                carGroup.add(body);

                const cabinGeo = new THREE.BoxGeometry(1.5, 0.5, 1.8);
                const cabinMat = new THREE.MeshStandardMaterial({{ color: 0x111111 }});
                const cabin = new THREE.Mesh(cabinGeo, cabinMat);
                cabin.position.set(0, 0.9, -0.2);
                carGroup.add(cabin);

                scene.add(carGroup);
                return carGroup;
            }}

            const car1 = createCar(0xEF4444); // Bright Red
            const car2 = createCar(0x2563EB); // Bright Blue

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
            let raceEnded = false;
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
                        statusElem.innerText = "🟢 GO! DRIVE FOR THE WIN!";
                        raceStarted = true;
                        startTime = Date.now();
                    }}
                }}, 1000);
            }}

            const keys = {{}};
            window.addEventListener('keydown', e => keys[e.key] = true);
            window.addEventListener('keyup', e => keys[e.key] = false);

            function updatePhysics(carMesh, state, forwardKey, leftKey, rightKey, backKey, nitroKey) {{
                if (!raceStarted || raceEnded) return;

                const isNitro = keys[nitroKey];
                const currentMax = isNitro ? baseMaxSpeed * 1.4 : baseMaxSpeed;

                const nextSpeed = keys[forwardKey] ? Math.min(state.speed + 0.015, currentMax) :
                                  keys[backKey] ? Math.max(state.speed - 0.012, -currentMax * 0.4) :
                                  state.speed * 0.95;

                const isTurning = keys[leftKey] || keys[rightKey];
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
                    playCrashSound();
                    state.speed = -state.speed * 0.3;
                }}

                carMesh.position.set(state.x, 0, state.z);
                carMesh.rotation.y = state.angle;

                updateAudio(Math.abs(state.speed) / baseMaxSpeed, isTurning, isNitro);

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
                if (!raceStarted || raceEnded) return;
                
                const targetPt = trackPoints[p2State.progressIdx];
                const dx = targetPt.x - p2State.x;
                const dz = targetPt.z - p2State.z;
                
                mistakeTimer++;
                if (mistakeTimer % 120 === 0) botErrorOffset = (Math.random() - 0.5) * 0.3;

                const targetAngle = Math.atan2(dx, dz) + botErrorOffset;
                p2State.angle += (targetAngle - p2State.angle) * 0.1;
                
                const botMaxSpeed = baseMaxSpeed * 0.70;
                p2State.speed = Math.min(p2State.speed + 0.006, botMaxSpeed);

                p2State.x += Math.sin(p2State.angle) * p2State.speed;
                p2State.z += Math.cos(p2State.angle) * p2State.speed;

                car2.position.set(p2State.x, 0, p2State.z);
                car2.rotation.y = p2State.angle;

                if (new THREE.Vector3(p2State.x, 0, p2State.z).distanceTo(targetPt) < 5) {{
                    p2State.progressIdx = (p2State.progressIdx + 1) % trackPoints.length;
                    if (p2State.progressIdx === 0) p2State.lap++;
                }}
            }}

            function triggerRaceEnd(winner, loser) {{
                raceEnded = true;
                raceStarted = false;
                
                document.getElementById('game-status').innerText = "🏁 RACE FINISHED!";
                
                document.getElementById('winner-text').innerHTML = winner + "<br><span style='color:#334155; font-size:15px;'>Finished in " + elapsedTime + " seconds! Phenomenal victory!</span>";
                document.getElementById('loser-text').innerText = loser + " - Better luck next time! Keep practicing to claim the top spot.";
                document.getElementById('end-modal').style.display = 'block';
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

                if (raceStarted && !raceEnded) {{
                    elapsedTime = ((Date.now() - startTime) / 1000).toFixed(1);
                    document.getElementById('timer-display').innerText = elapsedTime + "s";
                }}

                document.getElementById('p1-hud').innerText = "{p1_driver}: Lap " + Math.min(p1State.lap, 3) + "/3";
                document.getElementById('p2-hud').innerText = "{p2_driver}: Lap " + Math.min(p2State.lap, 3) + "/3";

                if ((p1State.lap >= 3 || p2State.lap >= 3) && !raceEnded) {{
                    const winner = p1State.lap >= 3 ? "{p1_driver}" : "{p2_driver}";
                    const loser = p1State.lap >= 3 ? "{p2_driver}" : "{p1_driver}";
                    triggerRaceEnd(winner, loser);
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

    st.subheader("🏁 Save Match Result to Leaderboard")
    sc_col1, sc_col2, sc_col3 = st.columns([2, 2, 1])
    
    with sc_col1:
        winner_name = st.selectbox("Race Winner:", [p1_driver, p2_driver], key="winner_drop")
    with sc_col2:
        finish_sec = st.number_input("Finish Time (Seconds):", min_value=5.0, max_value=300.0, value=20.0, step=0.5)
    with sc_col3:
        st.write("")
        st.write("")
        if st.button("Post Result to Leaderboard", use_container_width=True):
            loser_name = p2_driver if winner_name == p1_driver else p1_driver
            record_race_results(winner_name, loser_name, finish_sec, speed_lvl)
            st.success(f"Score recorded for {winner_name} on the Leaderboard!")

# --- TAB 3: LEADERBOARD ---
with tab_ranks:
    st.subheader("🏆 Global Driver Rankings")
    
    if st.session_state.leaderboard:
        df_rank = pd.DataFrame.from_dict(st.session_state.leaderboard, orient="index")
        df_rank.index.name = "Driver Name"
        
        df_rank["Win Rate %"] = ((df_rank["Wins"] / df_rank["Races"]) * 100).round(1)
        df_rank = df_rank.sort_values(by=["Total Points", "Fastest Time (s)"], ascending=[False, True])
        
        st.dataframe(
            df_rank.style.highlight_max(axis=0, subset=["Total Points", "Wins"], color="#D1FAE5")
                   .highlight_min(axis=0, subset=["Fastest Time (s)"], color="#DBEAFE"),
            use_container_width=True
        )
    else:
        st.info("No recorded match results yet. Finish a race in the Arena to post scores!")

# --- TAB 4: GAME LOBBIES ---
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
        new_lobby_name = st.text_input("New Session Name:", placeholder="e.g. Speed Circuit #103")
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
"""

req_code = """streamlit>=1.28.0
pandas>=2.0.0
"""

with open("gameapp.py", "w") as f:
    f.write(app_code)

with open("requirements.txt", "w") as f:
    f.write(req_code)

print("Export Complete! 'gameapp.py' has been updated with a bright daylight theme.")