# Save this code as app.py and run: streamlit run app.py

import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="3D Top-Down Racing League", layout="wide", page_icon="🏎️"
)

# High-contrast bright styling
st.markdown(
    """
<style>
    .stApp {
        background-color: #F8FAFC;
    }
    html, body, [class*="css"], .stMarkdown, h1, h2, h3, h4, h5, h6, p, span, label {
        color: #0F172A !important;
    }
    div[data-testid="stMetricValue"] {
        color: #2563EB !important;
    }
    input, select {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E0 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Persistent Leaderboard Initialization
if "leaderboard_data" not in st.session_state:
    st.session_state.leaderboard_data = [
        {
            "Driver": "ProRacer",
            "Wins": 4,
            "Total Points": 600,
            "Best Time (s)": 14.2,
            "Races": 4,
        },
        {
            "Driver": "SpeedyAI",
            "Wins": 1,
            "Total Points": 150,
            "Best Time (s)": 16.8,
            "Races": 3,
        },
    ]

# Hidden Input Handler to Receive Auto-Finished Race Results
if "auto_finish_payload" in st.query_params:
    try:
        data = json.loads(st.query_params["auto_finish_payload"])
        winner = data["winner"]
        loser = data["loser"]
        time_sec = float(data["time"])
        power_lvl = int(data.get("power", 3))

        # Update or create winner record
        w_found = False
        for entry in st.session_state.leaderboard_data:
            if entry["Driver"] == winner:
                entry["Wins"] += 1
                entry["Total Points"] += 150 * power_lvl
                entry["Races"] += 1
                if time_sec < entry["Best Time (s)"]:
                    entry["Best Time (s)"] = time_sec
                w_found = True
                break
        if not w_found:
            st.session_state.leaderboard_data.append(
                {
                    "Driver": winner,
                    "Wins": 1,
                    "Total Points": 150 * power_lvl,
                    "Best Time (s)": time_sec,
                    "Races": 1,
                }
            )

        # Clear query parameter after processing
        st.query_params.clear()
        st.toast(f"🏆 Victory Recorded! {winner} won in {time_sec}s!")
    except Exception:
        pass

st.title("🏎️ Top-Down 3D Turbo Racing")
st.caption(
    "Use **Arrow Keys** to steer and drive | **Spacebar** for Nitro Boost | Automated Win Detection"
)

# --- TOP SECTION: PLAYER PROFILE & MATCH CONFIG ---
col_profile, col_settings = st.columns([1, 2])

with col_profile:
    st.markdown("**👤 Player Profile & Storage**")
    player_name = st.text_input(
        "Enter Driver Name:", value="Player1", key="active_player_input"
    )
    p2_name = st.text_input(
        "P2 / AI Name:", value="SpeedyAI", key="p2_player_input"
    )

with col_settings:
    st.markdown("**⚙️ Track & Engine Controls**")
    c1, c2 = st.columns(2)
    with c1:
        track_level = st.selectbox(
            "Track Layout:", [1, 2, 3], format_func=lambda x: f"Layout {x}"
        )
    with c2:
        power_level = st.slider("Engine Power:", 1, 5, 3)

st.divider()

# --- MAIN SECTION: TOP-DOWN GAME ARENA & LEADERBOARD ---
game_col, board_col = st.columns([2.2, 1.3])

with game_col:
    st.markdown("**🏁 Live 3D Top-View Arena**")

    # Three.js Canvas with Top-Down Camera View & Auto-Finish Post
    threejs_canvas = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #7DD3FC; font-family: sans-serif; }}
            #hud {{ 
                position: absolute; top: 10px; left: 10px; color: #0F172A; 
                font-weight: bold; font-size: 13px; z-index: 10;
                background: rgba(255, 255, 255, 0.95); padding: 10px 14px; border-radius: 8px;
                border: 2px solid #2563EB; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            #start-btn {{
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                padding: 16px 36px; font-size: 22px; font-weight: bold; color: #fff;
                background: #10B981; border: none; border-radius: 10px; cursor: pointer;
                box-shadow: 0 4px 15px rgba(16,185,129,0.4); z-index: 20;
            }}
            canvas {{ display: block; width: 100vw; height: 500px; }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <button id="start-btn" onclick="startRace()">🟢 START RACE</button>
        <div id="hud">
            ⏱️ Time: <span id="timer" style="color:#2563EB;">0.0s</span><br>
            <span id="p1-hud" style="color: #DC2626;">{player_name}: Lap 0/3</span> | 
            <span id="p2-hud" style="color: #2563EB;">{p2_name}: Lap 0/3</span>
        </div>

        <script>
            // LocalStorage Player Saving
            localStorage.setItem('last_active_driver', "{player_name}");

            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xBAE6FD); // High visibility sky color

            // Fixed Top-Down Camera Setup
            const camera = new THREE.PerspectiveCamera(50, window.innerWidth / 500, 0.1, 1000);
            camera.position.set(0, 85, 0);
            camera.lookAt(0, 0, 0);

            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, 500);
            document.body.appendChild(renderer.domElement);

            const ambientLight = new THREE.AmbientLight(0xFFFFFF, 1.3);
            scene.add(ambientLight);
            
            const sunLight = new THREE.DirectionalLight(0xFFFFFF, 1.2);
            sunLight.position.set(20, 100, 20);
            scene.add(sunLight);

            // Ground
            const groundGeo = new THREE.PlaneGeometry(250, 250);
            const groundMat = new THREE.MeshStandardMaterial({{ color: 0x4ADE80 }});
            const ground = new THREE.Mesh(groundGeo, groundMat);
            ground.rotation.x = -Math.PI / 2;
            scene.add(ground);

            // Track Curves
            let trackCurve;
            const level = {track_level};
            if (level === 1) {{
                trackCurve = new THREE.CatmullRomCurve3([
                    new THREE.Vector3(-30, 0, 20), new THREE.Vector3(30, 0, 20),
                    new THREE.Vector3(40, 0, 0), new THREE.Vector3(30, 0, -20),
                    new THREE.Vector3(-30, 0, -20), new THREE.Vector3(-40, 0, 0)
                ], true);
            }} else if (level === 2) {{
                trackCurve = new THREE.CatmullRomCurve3([
                    new THREE.Vector3(-35, 0, 25), new THREE.Vector3(0, 0, 0),
                    new THREE.Vector3(35, 0, -25), new THREE.Vector3(35, 0, 25),
                    new THREE.Vector3(-35, 0, -25)
                ], true);
            }} else {{
                trackCurve = new THREE.CatmullRomCurve3([
                    new THREE.Vector3(-40, 0, 30), new THREE.Vector3(20, 0, 30),
                    new THREE.Vector3(35, 0, 0), new THREE.Vector3(-20, 0, -30),
                    new THREE.Vector3(-35, 0, 0)
                ], true);
            }}

            const trackGeo = new THREE.TubeGeometry(trackCurve, 120, 7, 8, true);
            const trackMat = new THREE.MeshStandardMaterial({{ color: 0x334155 }});
            const trackMesh = new THREE.Mesh(trackGeo, trackMat);
            trackMesh.scale.set(1, 0.01, 1);
            trackMesh.position.y = 0.02;
            scene.add(trackMesh);

            function createCar(colorHex) {{
                const group = new THREE.Group();
                const body = new THREE.Mesh(
                    new THREE.BoxGeometry(2.2, 0.8, 4.0),
                    new THREE.MeshStandardMaterial({{ color: colorHex }})
                );
                body.position.y = 0.5;
                group.add(body);
                scene.add(group);
                return group;
            }}

            const car1 = createCar(0xEF4444);
            const car2 = createCar(0x2563EB);

            const trackPoints = trackCurve.getSpacedPoints(150);
            const startPt = trackPoints[0];

            const p1 = {{ x: startPt.x - 2, z: startPt.z, angle: 0, speed: 0, lap: 0, crossed: false }};
            const p2 = {{ x: startPt.x + 2, z: startPt.z, angle: 0, speed: 0, lap: 0, progressIdx: 0 }};
            
            const maxSpeed = 0.25 + ({power_level} * 0.08);
            let raceStarted = false, raceFinished = false, startTime = 0, elapsed = 0;

            function startRace() {{
                document.getElementById('start-btn').style.display = 'none';
                raceStarted = true;
                startTime = Date.now();
            }}

            const keys = {{}};
            window.addEventListener('keydown', e => keys[e.key] = true);
            window.addEventListener('keyup', e => keys[e.key] = false);

            function updatePhysics() {{
                if (!raceStarted || raceFinished) return;

                // Player 1 Driving Logic
                const speedCap = keys[' '] ? maxSpeed * 1.35 : maxSpeed;
                if (keys['ArrowUp']) p1.speed = Math.min(p1.speed + 0.012, speedCap);
                else if (keys['ArrowDown']) p1.speed = Math.max(p1.speed - 0.01, -speedCap * 0.3);
                else p1.speed *= 0.95;

                if (keys['ArrowLeft']) p1.angle += 0.045;
                if (keys['ArrowRight']) p1.angle -= 0.045;

                p1.x += Math.sin(p1.angle) * p1.speed;
                p1.z += Math.cos(p1.angle) * p1.speed;
                car1.position.set(p1.x, 0, p1.z);
                car1.rotation.y = p1.angle;

                // Simple AI Driving Logic
                const targetPt = trackPoints[p2.progressIdx];
                const dx = targetPt.x - p2.x;
                const dz = targetPt.z - p2.z;
                p2.angle = Math.atan2(dx, dz);
                p2.speed = maxSpeed * 0.72;
                p2.x += Math.sin(p2.angle) * p2.speed;
                p2.z += Math.cos(p2.angle) * p2.speed;
                car2.position.set(p2.x, 0, p2.z);
                car2.rotation.y = p2.angle;

                if (new THREE.Vector3(p2.x, 0, p2.z).distanceTo(targetPt) < 4) {{
                    p2.progressIdx = (p2.progressIdx + 1) % trackPoints.length;
                    if (p2.progressIdx === 0) p2.lap++;
                }}

                // Check Lap Progress P1
                if (new THREE.Vector3(p1.x, 0, p1.z).distanceTo(startPt) < 6) {{
                    if (!p1.crossed) {{ p1.lap++; p1.crossed = true; }}
                }} else {{ p1.crossed = false; }}

                // Automatic Match Finish Handler
                if ((p1.lap >= 3 || p2.lap >= 3) && !raceFinished) {{
                    raceFinished = true;
                    const winner = p1.lap >= 3 ? "{player_name}" : "{p2_name}";
                    const loser = p1.lap >= 3 ? "{p2_name}" : "{player_name}";
                    
                    // Send Payload back to Streamlit URL to record results automatically
                    const payload = JSON.stringify({{ winner: winner, loser: loser, time: elapsed, power: {power_level} }});
                    window.parent.location.search = '?auto_finish_payload=' + encodeURIComponent(payload);
                }}
            }}

            function animate() {{
                requestAnimationFrame(animate);
                updatePhysics();

                if (raceStarted && !raceFinished) {{
                    elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                    document.getElementById('timer').innerText = elapsed + "s";
                }}

                document.getElementById('p1-hud').innerText = "{player_name}: Lap " + Math.min(p1.lap, 3) + "/3";
                document.getElementById('p2-hud').innerText = "{p2_name}: Lap " + Math.min(p2.lap, 3) + "/3";

                renderer.render(scene, camera);
            }}

            animate();
        </script>
    </body>
    </html>
    """

    components.html(threejs_canvas, height=520)

with board_col:
    st.markdown("**🏆 Live Updating Leaderboard**")

    # Format Leaderboard Table
    df = pd.DataFrame(st.session_state.leaderboard_data)
    df["Win Rate %"] = ((df["Wins"] / df["Races"]) * 100).round(1)
    df = df.sort_values(
        by=["Total Points", "Best Time (s)"], ascending=[False, True]
    )

    st.dataframe(
        df[["Driver", "Wins", "Total Points", "Best Time (s)"]],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.markdown("** Driver Local Stats**")
    active_record = df[df["Driver"] == player_name]
    if not active_record.empty:
        st.metric("Total Points", int(active_record["Total Points"].iloc[0]))
        st.metric("Best Lap Time", f"{active_record['Best Time (s)'].iloc[0]}s")
    else:
        st.info("No recorded races for the current player yet.")