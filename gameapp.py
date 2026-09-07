# Import system libraries
import streamlit as st  # Main web framework
import pandas as pd  # Data manipulation library
import streamlit.components.v1 as components  # Embedded HTML/JS renderer

# Set page configuration for 3D game layout
st.set_page_config(
    page_title="3D Turbo Racing League", layout="wide", page_icon="🏎️"
)

# Initialize Session State Data Structures
if "sessions" not in st.session_state:  # Open multi-player game lobbies
    st.session_state.sessions = {
        "Session #101 (Speedway)": {"host": "ProRacer", "players": ["ProRacer"], "max": 2, "status": "Waiting"},
        "Session #102 (Circuit)": {"host": "DriftKing", "players": ["DriftKing"], "max": 2, "status": "Waiting"}
    }

if "registered_users" not in st.session_state:  # Persistent player catalog
    st.session_state.registered_users = ["ProRacer", "DriftKing", "TurboMax"]

if "leaderboard" not in st.session_state:  # Global rank scoreboard
    st.session_state.leaderboard = {}

if "current_user" not in st.session_state:  # Active player name
    st.session_state.current_user = "Racer1"


# Helper function to process score updates
def record_win(winner, time_sec, speed_lvl):  # Update global rankings
    if winner not in st.session_state.leaderboard:  # Add user if missing
        st.session_state.leaderboard[winner] = {
            "Wins": 0, "Total Points": 0, "Fastest Time (s)": 999.0, "Races": 0
        }
    entry = st.session_state.leaderboard[winner]  # Access reference
    entry["Wins"] += 1  # Increment total wins
    entry["Total Points"] += 150 * speed_lvl  # Multiply score by speed level
    entry["Races"] += 1  # Increment race counter
    if time_sec < entry["Fastest Time (s)"]:  # Update personal record
        entry["Fastest Time (s)"] = round(time_sec, 2)


# App Header Setup
st.title("🏎️ 3D Low-Poly Multi-Player Racing Engine")  # Application Title
st.caption("Low-poly 3D graphics powered by Three.js & WebGL")  # Engine subtitle

# Primary Navigation Tabs
tab_player, tab_arena, tab_lobbies, tab_ranks = st.tabs([
    "👤 Player Setup", "🏁 3D Race Arena", "🌐 Game Lobbies", "🏆 Leaderboard"
])

# --- TAB 1: PLAYER REGISTRATION & SETUP ---
with tab_player:  # Configure User Name and Profile
    st.subheader("Register / Select Player Name")  # Section title
    col_a, col_b = st.columns(2)  # Two-column layout
    
    with col_a:  # New player registration form
        new_name = st.text_input("Enter New Player Name:", placeholder="e.g. SpeedDemon99")  # Input box
        if st.button("Save & Select Name"):  # Save action button
            if new_name.strip():  # Validate input string
                clean_name = new_name.strip()  # Clean whitespace
                if clean_name not in st.session_state.registered_users:  # Check duplicates
                    st.session_state.registered_users.append(clean_name)  # Register new name
                st.session_state.current_user = clean_name  # Set active driver
                st.success(f"Driver profile updated to: **{clean_name}**")  # Success notification
            else:  # Empty string warning
                st.warning("Please enter a valid player name.")  # Warning message

    with col_b:  # Dropdown selector for saved profiles
        selected_profile = st.selectbox(
            "Select Existing Player Profile:",
            st.session_state.registered_users,
            index=0 if st.session_state.current_user not in st.session_state.registered_users 
            else st.session_state.registered_users.index(st.session_state.current_user)
        )  # Dropdown choice
        if st.button("Switch Profile"):  # Switch action button
            st.session_state.current_user = selected_profile  # Set selected driver
            st.info(f"Switched driver to: **{selected_profile}**")  # Status info

    st.divider()  # Visual divider
    st.markdown(f"**Current Driver Active:** `{st.session_state.current_user}`")  # Active status banner

# --- TAB 2: 3D RACE ARENA ---
with tab_arena:  # Main 3D Low-Poly Game Loop
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])  # Configuration columns
    
    with col1:  # Player 1 designation
        p1_driver = st.text_input("Player 1 (Red Car):", value=st.session_state.current_user, key="p1_val")  # P1 Name
    with col2:  # Player 2 designation
        p2_driver = st.text_input("Player 2 (Blue Car):", value="Racer2", key="p2_val")  # P2 Name
    with col3:  # Game Speed level selection
        speed_lvl = st.slider("Speed Engine Level (1-5)", 1, 5, 3, key="speed_setting")  # Speed level
    with col4:  # Camera perspective view selector
        camera_view = st.selectbox("3D Camera Perspective:", ["Chase Cam (Behind)", "Third-Person (High)", "Top-Down (Map)"])  # Camera view

    st.markdown(
        "**🎮 Controls:** **P1 (Red):** `W` (Gas), `A` (Left), `D` (Right), `S` (Reverse) | **P2 (Blue):** `Up Arrow` (Gas), `Left Arrow`, `Right Arrow`, `Down Arrow`"
    )  # Controls bar

    # Embed Three.js 3D Racing Engine HTML/JS Code
    threejs_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #87CEEB; font-family: sans-serif; }}
            #hud {{ position: absolute; top: 10px; left: 10px; color: white; font-weight: bold; font-size: 16px; text-shadow: 2px 2px 4px #000; z-index: 10; }}
            canvas {{ display: block; width: 100vw; height: 520px; }}
        </style>
        <!-- Import Three.js via CDN -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <div id="hud">
            🏁 3D Low-Poly Circuit | Speed Lvl: {speed_lvl}<br>
            <span id="p1-hud" style="color: #ff4444;">{p1_driver}: Lap 0/3</span> | 
            <span id="p2-hud" style="color: #4488ff;">{p2_driver}: Lap 0/3</span><br>
            <span id="game-status" style="color: #yellow;">Press W/Up to Start Race!</span>
        </div>
        <script>
            // Scene & Renderer Setup
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x87CEEB); // Sky blue background
            scene.fog = new THREE.Fog(0x87CEEB, 20, 150); // Environmental fog effect

            const camera = new THREE.PerspectiveCamera(60, window.innerWidth / 520, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, 520);
            renderer.shadowMap.enabled = true; // Enable shadow maps
            document.body.appendChild(renderer.domElement);

            // Lighting setup (Low-Poly aesthetic lighting)
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);

            const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
            dirLight.position.set(50, 80, 50);
            dirLight.castShadow = true;
            scene.add(dirLight);

            // Track Circuit Parameters (Oval Loop)
            const trackRadiusX = 40;
            const trackRadiusZ = 25;

            // Generate Low-Poly Ground & Track
            const groundGeo = new THREE.PlaneGeometry(200, 200);
            const groundMat = new THREE.MeshLambertMaterial({{ color: 0x55aa55 }}); // Green grass
            const ground = new THREE.Mesh(groundGeo, groundMat);
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
            scene.add(ground);

            // Create Oval Track Shape
            const trackShape = new THREE.Shape();
            trackShape.absellipse(0, 0, trackRadiusX + 6, trackRadiusZ + 6, 0, Math.PI * 2, false, 0);
            const holePath = new THREE.Path();
            holePath.absellipse(0, 0, trackRadiusX - 6, trackRadiusZ - 6, 0, Math.PI * 2, true, 0);
            trackShape.holes.push(holePath);

            const trackGeo = new THREE.ShapeGeometry(trackShape);
            const trackMat = new THREE.MeshLambertMaterial({{ color: 0x333333 }}); // Dark asphalt track
            const trackMesh = new THREE.Mesh(trackGeo, trackMat);
            trackMesh.rotation.x = -Math.PI / 2;
            trackMesh.position.y = 0.01;
            scene.add(trackMesh);

            // Add Red/White Curb Edges
            const curbGeo = new THREE.RingGeometry(trackRadiusX - 6.5, trackRadiusX - 6, 64);
            const curbMat = new THREE.MeshBasicMaterial({{ color: 0xff2222, side: THREE.DoubleSide }});
            const curb = new THREE.Mesh(curbGeo, curbMat);
            curb.rotation.x = -Math.PI / 2;
            curb.position.y = 0.02;
            scene.add(curb);

            // Low-Poly Pine Trees Environment Setup
            function createPineTree(x, z) {{
                const group = new THREE.Group();
                const trunkGeo = new THREE.CylinderGeometry(0.3, 0.5, 2, 5);
                const trunkMat = new THREE.MeshLambertMaterial({{ color: 0x8B4513 }});
                const trunk = new THREE.Mesh(trunkGeo, trunkMat);
                trunk.position.y = 1;
                group.add(trunk);

                const leavesGeo = new THREE.ConeGeometry(2, 5, 5); // 5-sided low-poly cone
                const leavesMat = new THREE.MeshLambertMaterial({{ color: 0x2e6f40 }});
                const leaves = new THREE.Mesh(leavesGeo, leavesMat);
                leaves.position.y = 3.5;
                group.add(leaves);

                group.position.set(x, 0, z);
                scene.add(group);
            }}

            // Place Pine Trees around perimeter
            for (let i = 0; i < 20; i++) {{
                const angle = (i / 20) * Math.PI * 2;
                createPineTree(Math.cos(angle) * (trackRadiusX + 15), Math.sin(angle) * (trackRadiusZ + 15));
                createPineTree(Math.cos(angle) * (trackRadiusX - 12), Math.sin(angle) * (trackRadiusZ - 12));
            }}

            // Low-Poly Car Factory Function
            function createCar(colorHex) {{
                const carGroup = new THREE.Group();
                
                // Chassis Box
                const bodyGeo = new THREE.BoxGeometry(1.8, 0.7, 3.2);
                const bodyMat = new THREE.MeshLambertMaterial({{ color: colorHex }});
                const body = new THREE.Mesh(bodyGeo, bodyMat);
                body.position.y = 0.5;
                body.castShadow = true;
                carGroup.add(body);

                // Cabin Glass
                const cabinGeo = new THREE.BoxGeometry(1.4, 0.6, 1.6);
                const cabinMat = new THREE.MeshLambertMaterial({{ color: 0x111111 }});
                const cabin = new THREE.Mesh(cabinGeo, cabinMat);
                cabin.position.set(0, 1.0, -0.2);
                carGroup.add(cabin);

                // 4 Wheels
                const wheelGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.3, 8);
                const wheelMat = new THREE.MeshLambertMaterial({{ color: 0x222222 }});
                const positions = [[-0.95, 0.35, 1], [0.95, 0.35, 1], [-0.95, 0.35, -1], [0.95, 0.35, -1]];
                
                positions.forEach(pos => {{
                    const wheel = new THREE.Mesh(wheelGeo, wheelMat);
                    wheel.rotation.z = Math.PI / 2;
                    wheel.position.set(pos[0], pos[1], pos[2]);
                    carGroup.add(wheel);
                }});

                scene.add(carGroup);
                return carGroup;
            }}

            // Create Player 1 (Red) and Player 2 (Blue) Cars
            const car1 = createCar(0xff3333); // Red P1
            const car2 = createCar(0x3388ff); // Blue P2

            // Initial Car Placement
            car1.position.set(0, 0, trackRadiusZ);
            car2.position.set(0, 0, trackRadiusZ + 2.5);

            // Game State Variables
            const p1State = {{ x: 0, z: trackRadiusZ, angle: Math.PI/2, speed: 0, lap: 0, crossed: false }};
            const p2State = {{ x: 0, z: trackRadiusZ + 2.5, angle: Math.PI/2, speed: 0, lap: 0, crossed: false }};
            const maxSpeed = 0.3 + ({speed_lvl} * 0.12);
            const keys = {{}};

            // Keyboard Listeners
            window.addEventListener('keydown', e => keys[e.key] = true);
            window.addEventListener('keyup', e => keys[e.key] = false);

            // Physics Update Logic
            function updatePhysics(carMesh, state, forwardKey, leftKey, rightKey, backKey) {{
                if (keys[forwardKey]) state.speed = Math.min(state.speed + 0.01, maxSpeed);
                else if (keys[backKey]) state.speed = Math.max(state.speed - 0.01, -maxSpeed * 0.5);
                else state.speed *= 0.95; // Friction

                if (keys[leftKey] && Math.abs(state.speed) > 0.01) state.angle += 0.04;
                if (keys[rightKey] && Math.abs(state.speed) > 0.01) state.angle -= 0.04;

                state.x += Math.sin(state.angle) * state.speed;
                state.z += Math.cos(state.angle) * state.speed;

                carMesh.position.set(state.x, 0, state.z);
                carMesh.rotation.y = state.angle;

                // Simple Lap Detection (Crossing X=0 Line)
                if (Math.abs(state.x) < 3 && state.z > 15) {{
                    if (!state.crossed) {{
                        state.lap++;
                        state.crossed = true;
                    }}
                }} else {{
                    state.crossed = false;
                }}
            }}

            // Selected Camera View Mode Logic
            const camView = "{camera_view}";

            function updateCamera() {{
                if (camView === "Chase Cam (Behind)") {{
                    // Follow Red Car from Behind
                    camera.position.x = car1.position.x - Math.sin(p1State.angle) * 12;
                    camera.position.z = car1.position.z - Math.cos(p1State.angle) * 12;
                    camera.position.y = car1.position.y + 6;
                    camera.lookAt(car1.position.x, car1.position.y + 1, car1.position.z);
                }} else if (camView === "Third-Person (High)") {{
                    // High Isometric Angle
                    camera.position.set(0, 45, 45);
                    camera.lookAt(0, 0, 0);
                }} else {{
                    // Overhead Map View
                    camera.position.set(0, 70, 0.1);
                    camera.lookAt(0, 0, 0);
                }}
            }}

            // Main Animation Render Loop
            function animate() {{
                requestAnimationFrame(animate);

                // Update Player Controls
                updatePhysics(car1, p1State, 'w', 'a', 'd', 's');
                updatePhysics(car2, p2State, 'ArrowUp', 'ArrowLeft', 'ArrowRight', 'ArrowDown');

                // Update HUD Text
                document.getElementById('p1-hud').innerText = "{p1_driver}: Lap " + Math.min(p1State.lap, 3) + "/3";
                document.getElementById('p2-hud').innerText = "{p2_driver}: Lap " + Math.min(p2State.lap, 3) + "/3";

                if (p1State.lap >= 3) {{
                    document.getElementById('game-status').innerText = "🎉 {p1_driver} (Red Car) WINS THE RACE!";
                }} else if (p2State.lap >= 3) {{
                    document.getElementById('game-status').innerText = "🎉 {p2_driver} (Blue Car) WINS THE RACE!";
                }}

                updateCamera();
                renderer.render(scene, camera);
            }}

            animate(); // Start animation loop
        </script>
    </body>
    </html>
    """

    # Render HTML5/3D Component in Streamlit
    components.html(threejs_html, height=550)  # Embedded webgl component

    # Score recording section
    st.subheader("🏁 Submit Match Score")  # Section title
    sc_col1, sc_col2, sc_col3 = st.columns([2, 2, 1])  # Column layout
    
    with sc_col1:  # Winner selection dropdown
        winner_name = st.selectbox("Race Winner:", [p1_driver, p2_driver], key="winner_drop")  # Winner name
    with sc_col2:  # Race duration time input
        finish_sec = st.number_input("Finish Time (Seconds):", min_value=5.0, max_value=300.0, value=22.5, step=0.5)  # Time
    with sc_col3:  # Submit button
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Save Result", use_container_width=True):  # Save trigger
            record_win(winner_name, finish_sec, speed_lvl)  # Record scores
            st.success(f"Score recorded for {winner_name}!")  # Display confirmation

# --- TAB 3: GAME LOBBIES ---
with tab_lobbies:  # Open Multi-Player Sessions
    st.subheader("🌐 Active Open Racing Lobbies")  # Section subheader
    
    # Display table of active sessions
    lobby_data = []  # List for session objects
    for session_id, details in st.session_state.sessions.items():  # Iterate sessions
        lobby_data.append({
            "Session Name": session_id,
            "Host Player": details["host"],
            "Players Joined": f"{len(details['players'])} / {details['max']}",
            "Status": details["status"]
        })
    
    st.dataframe(pd.DataFrame(lobby_data), use_container_width=True)  # Display session dataframe

    st.divider()  # Divider bar
    st.subheader("Create or Join a Session")  # Create or Join section
    l_col1, l_col2 = st.columns(2)  # 2 columns

    with l_col1:  # Create session form
        new_lobby_name = st.text_input("New Session Name:", placeholder="e.g. Session #103")  # Input lobby name
        if st.button("Create Open Session"):  # Button to create session
            if new_lobby_name.strip():  # Check valid input
                st.session_state.sessions[new_lobby_name.strip()] = {
                    "host": st.session_state.current_user,
                    "players": [st.session_state.current_user],
                    "max": 2,
                    "status": "Waiting"
                }  # Register new lobby
                st.success(f"Session '{new_lobby_name}' created successfully!")  # Show alert
            else:  # Empty input prompt
                st.warning("Please provide a session title.")  # Warning banner

    with l_col2:  # Join session selector
        target_lobby = st.selectbox("Select Lobby to Join:", list(st.session_state.sessions.keys()))  # Select lobby
        if st.button("Join Gaming Session"):  # Button to join session
            lobby = st.session_state.sessions[target_lobby]  # Get session object
            if len(lobby["players"]) < lobby["max"]:  # Check room space
                if st.session_state.current_user not in lobby["players"]:  # Prevent duplicate entry
                    lobby["players"].append(st.session_state.current_user)  # Add user to player list
                    if len(lobby["players"]) == lobby["max"]:  # Set state to full
                        lobby["status"] = "In Progress"  # Change status
                    st.success(f"Joined {target_lobby}!")  # Show alert
                else:  # Already joined warning
                    st.info("You are already in this session.")  # Info prompt
            else:  # Session full error
                st.error("Session is already full!")  # Error banner

# --- TAB 4: LEADERBOARD ---
with tab_ranks:  # Global Scoreboard Tab
    st.subheader("🏆 Driver Global Rankings")  # Subheader
    
    if st.session_state.leaderboard:  # Check if scores exist
        df_rank = pd.DataFrame.from_dict(st.session_state.leaderboard, orient="index")  # Build dataframe
        df_rank.index.name = "Driver Name"  # Index column title
        df_rank = df_rank.sort_values(by=["Total Points", "Fastest Time (s)"], ascending=[False, True])  # Sort ranks
        st.dataframe(df_rank.style.highlight_max(axis=0, subset=["Total Points"], color="#2e7d32"), use_container_width=True)  # Highlight top score
    else:  # Empty scores fallback
        st.info("No recorded match results yet. Complete a race in the Arena to post scores!")  # Empty info banner
