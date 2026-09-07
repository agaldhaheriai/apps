# Import required system libraries
import json  # Library to handle JSON serialization
import urllib.request  # Library to make HTTP API requests
import pandas as pd  # Library for data manipulation and tabular display
import streamlit as st  # Main web application framework
import streamlit.components.v1 as components  # Module to embed custom HTML5/JavaScript canvas

# Set page configuration to wide layout and custom title
st.set_page_config(
    page_title="2-Player Turbo Racers", layout="wide", page_icon="🏎️"
)


# Function to fetch employee data from external API endpoint
@st.cache_data(ttl=300)  # Cache API response for 5 minutes to reduce latency
def fetch_employees():  # Define API fetch routine
    url = "http://shelfcorp.atwebpages.com/api/employees.json"  # Target JSON API endpoint
    try:  # Handle network operations safely
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )  # Add user-agent header to avoid blocks
        with urllib.request.urlopen(req, timeout=5) as response:  # Send HTTP GET request with 5s timeout
            data = json.loads(
                response.read().decode()
            )  # Decode and parse JSON payload
            # Handle list or object response structure safely
            if isinstance(data, list):  # Check if response is array
                names = [
                    item.get("name") or item.get("employee_name") or str(item)
                    for item in data
                ]  # Extract name keys
            elif isinstance(data, dict):  # Check if response is dictionary object
                names = [
                    v.get("name") if isinstance(v, dict) else str(v)
                    for v in data.values()
                ]  # Extract values
            else:  # Fallback for alternative types
                names = []  # Default empty list
            return [n for n in names if n]  # Filter out empty entries
    except Exception as e:  # Catch network or parsing failures
        st.warning(
            f"Could not load live API data ({e}). Using local fallback drivers."
        )  # Display user notification
        return [
            "Alex Pro",
            "Sam Speed",
            "Jordan Drift",
            "Taylor Turbo",
            "Morgan Nitro",
        ]  # Return fallback driver names


# Initialize session state for persistent scoreboard and user stats
if (
    "leaderboard" not in st.session_state
):  # Check if leaderboard data exists in memory
    st.session_state.leaderboard = {}  # Initialize empty dictionary structure


# Function to record race results and update running scores dynamically
def update_scores(winner_name, race_time, speed_level):  # Define score update routine
    if winner_name not in st.session_state.leaderboard:  # Check if driver exists in records
        st.session_state.leaderboard[winner_name] = {  # Create new driver record entry
            "Wins": 0,  # Total win count
            "Total Score": 0,  # Aggregate points score
            "Fastest Time (s)": 999.0,  # Best recorded finish time
            "Races Played": 0,  # Total matches played
        }  # End dictionary assignment

    # Calculate points based on selected speed level multiplier (Speed Level 1 to 5)
    points_earned = 100 * speed_level  # Higher speed levels grant higher point rewards
    driver = st.session_state.leaderboard[winner_name]  # Get driver reference
    driver["Wins"] += 1  # Increment win count by 1
    driver["Total Score"] += points_earned  # Add earned points to running total
    driver["Races Played"] += 1  # Increment match counter
    if race_time < driver["Fastest Time (s)"]:  # Check if current time beats record
        driver["Fastest Time (s)"] = round(
            race_time, 2
        )  # Update fastest time record


# Fetch driver choices from API
driver_list = fetch_employees()  # Call API fetching function

# Render application header
st.title("🏎️ Interactive 2-Player Canvas Racing Engine")  # Main header text
st.caption(
    "Real-time dual-input arcade racer powered by Python & HTML5 Canvas"
)  # Subtitle caption

# Create navigation tabs for Game Arena and Leaderboard
tab1, tab2 = st.tabs(
    ["🏁 Race Track Arena", "🏆 Global Leaderboard"]
)  # Define Streamlit tabs

with tab1:  # Game Arena Tab Context
    col1, col2, col3 = st.columns(
        [1, 1, 1]
    )  # Setup 3-column layout for player selections

    with col1:  # Player 1 configuration column
        p1_name = st.selectbox(
            "Select Player 1 (Red Car)",
            driver_list,
            index=0,
            key="p1_select",  # Dropdown menu for Player 1
        )  # Assign selected driver

    with col2:  # Player 2 configuration column
        # Ensure default index doesn't conflict if list contains multiple items
        default_p2 = 1 if len(driver_list) > 1 else 0  # Fallback index check
        p2_name = st.selectbox(
            "Select Player 2 (Blue Car)",
            driver_list,
            index=default_p2,
            key="p2_select",  # Dropdown menu for Player 2
        )  # Assign selected driver

    with col3:  # Engine performance selection column
        speed_level = st.slider(
            "🏎️ Engine Speed Level (1-5)",
            min_value=1,
            max_value=5,
            value=3,
            key="speed_lvl",  # Speed level selection slider
        )  # Assign speed multiplier

    st.markdown(
        "**🎮 Controls:** **P1 (Red):** `W` (Accelerate), `A` (Steer Left), `D` (Steer Right) | **P2 (Blue):** `Up Arrow` (Accelerate), `Left Arrow` (Steer Left), `Right Arrow` (Steer Right)"
    )  # On-screen control instructions

    # HTML5/JS Game Loop injected directly into Streamlit
    game_html = f"""
    <!DOCTYPE html> <!-- HTML5 Document Type Declaration -->
    <html> <!-- Root HTML Element -->
    <head> <!-- Header Element -->
        <style> /* CSS Styling for Canvas Arena */
            body {{ margin: 0; padding: 0; background-color: #111; font-family: sans-serif; color: white; text-align: center; }} /* Page Body Setup */
            canvas {{ background: #222; border: 4px solid #444; border-radius: 8px; display: block; margin: 10px auto; }} /* Canvas Styling */
            .ui-panel {{ font-size: 18px; font-weight: bold; margin-bottom: 5px; }} /* HUD Text Styling */
        </style> <!-- End CSS Styling -->
    </head> <!-- End Header -->
    <body> <!-- Body Element -->
        <div class="ui-panel"> Race Status: <span id="status" style="color: #00FF00;">Ready to Start! Drive 3 Laps!</span></div> <!-- HUD Status Text -->
        <canvas id="raceCanvas" width="800" height="500"></canvas> <!-- Game Canvas Rendering Target -->

        <script> /* Start Embedded JavaScript Arcade Engine */
            const canvas = document.getElementById("raceCanvas"); /* Get Canvas DOM Reference */
            const ctx = canvas.getContext("2d"); /* Obtain 2D Rendering Context */

            // Game Settings & Configuration Parameters
            const speedMultiplier = {speed_level}; /* Speed Level set from Python Slider */
            const baseSpeed = 1.5 + (speedMultiplier * 0.8); /* Calculate max velocity threshold */
            const turnSpeed = 0.05; /* Steering sensitivity angle increment */
            const totalLaps = 3; /* Total laps required to win race */

            // Key Input Listener States
            const keys = {{}}; /* Object tracking held key events */

            // Player 1 Object State (Red Car)
            const p1 = {{
                name: "{p1_name}", x: 380, y: 430, angle: 0, speed: 0, 
                color: "#FF3333", lap: 0, crossed: false, finishTime: null
            }};

            // Player 2 Object State (Blue Car)
            const p2 = {{
                name: "{p2_name}", x: 420, y: 430, angle: 0, speed: 0, 
                color: "#3388FF", lap: 0, crossed: false, finishTime: null
            }};

            let raceStartTime = Date.now(); /* Record timestamp at game load */
            let gameOver = false; /* Master race state flag */

            // Keydown Event Listener
            window.addEventListener("keydown", (e) => {{ keys[e.key] = true; }}); /* Flag key pressed */
            // Keyup Event Listener
            window.addEventListener("keyup", (e) => {{ keys[e.key] = false; }}); /* Flag key released */

            // Track Finish Line Parameters (Coordinates)
            const finishLine = {{ x1: 350, y1: 400, x2: 450, y2: 460 }}; /* Define start/finish checkpoint zone */

            // Main Physics & Movement Update Loop Function
            function updateCar(car, upKey, leftKey, rightKey) {{
                if (gameOver) return; /* Freeze physics updates if race finished */

                // Acceleration Logic
                if (keys[upKey]) {{
                    car.speed = Math.min(car.speed + 0.1, baseSpeed); /* Accelerate car up to baseSpeed limit */
                }} else {{
                    car.speed = Math.max(car.speed - 0.05, 0); /* Apply natural deceleration friction */
                }}

                // Steering Logic
                if (keys[leftKey] && car.speed > 0) {{ car.angle -= turnSpeed; }} /* Rotate counter-clockwise */
                if (keys[rightKey] && car.speed > 0) {{ car.angle += turnSpeed; }} /* Rotate clockwise */

                // Position Translation based on Angular Vector Trigonometry
                car.x += Math.sin(car.angle) * car.speed; /* Calculate X delta movement */
                car.y -= Math.cos(car.angle) * car.speed; /* Calculate Y delta movement */

                // Outer Boundary Collision Checks (Canvas Walls)
                if (car.x < 20 || car.x > 780 || car.y < 20 || car.y > 480) {{
                    car.speed = -0.5; /* Bounce back penalty on wall crash */
                }}

                // Lap Counter Detection Logic
                if (car.x > finishLine.x1 && car.x < finishLine.x2 && car.y > finishLine.y1 && car.y < finishLine.y2) {{
                    if (!car.crossed) {{ /* Check for new lap trigger */
                        car.lap++; /* Increment completed lap count */
                        car.crossed = true; /* Set crossing lock flag */
                        if (car.lap >= totalLaps && !gameOver) {{ /* Winner check condition */
                            gameOver = true; /* Set race finished flag */
                            car.finishTime = ((Date.now() - raceStartTime) / 1000).toFixed(2); /* Compute final duration */
                            document.getElementById("status").innerText = car.name + " WINS in " + car.finishTime + "s!"; /* Display HUD message */
                        }}
                    }}
                }} else {{
                    car.crossed = false; /* Reset crossing lock flag once car exits line */
                }}
            }}

            // Drawing Engine Routine (Canvas Graphics Context)
            function drawTrack() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height); /* Clear previous frame */

                // Outer Grass Background
                ctx.fillStyle = "#2e7d32"; /* Dark Green background color */
                ctx.fillRect(0, 0, canvas.width, canvas.height); /* Fill full canvas */

                // Outer Race Track Oval Circuit
                ctx.fillStyle = "#555555"; /* Asphalt gray color */
                ctx.beginPath(); /* Begin vector path */
                ctx.ellipse(400, 250, 350, 200, 0, 0, 2 * Math.PI); /* Outer oval path */
                ctx.fill(); /* Render asphalt filled shape */

                // Inner Field Grass Island
                ctx.fillStyle = "#2e7d32"; /* Center island grass color */
                ctx.beginPath(); /* Begin vector path */
                ctx.ellipse(400, 250, 200, 100, 0, 0, 2 * Math.PI); /* Inner oval path */
                ctx.fill(); /* Cut out inner field */

                // Start/Finish Line Indicator
                ctx.strokeStyle = "#FFFFFF"; /* White line color */
                ctx.lineWidth = 6; /* Set stroke width */
                ctx.beginPath(); /* Begin vector path */
                ctx.moveTo(400, 350); /* Start position */
                ctx.lineTo(400, 450); /* End position */
                ctx.stroke(); /* Render check line */
            }}

            // Render Car Vehicle Graphics Representation
            function drawCar(car) {{
                ctx.save(); /* Save canvas state context */
                ctx.translate(car.x, car.y); /* Translate origin to car coordinates */
                ctx.rotate(car.angle); /* Rotate canvas context to car heading */
                
                // Vehicle Body Box
                ctx.fillStyle = car.color; /* Set specific player car color */
                ctx.fillRect(-10, -18, 20, 36); /* Draw main chassis rectangle */

                // Windshield Detail
                ctx.fillStyle = "#111"; /* Dark windshield color */
                ctx.fillRect(-7, -8, 14, 10); /* Draw glass block */

                ctx.restore(); /* Restore base canvas context */

                // Render Overhead Driver Name Tag and Lap HUD
                ctx.fillStyle = "#FFFFFF"; /* White text color */
                ctx.font = "12px sans-serif"; /* Font styling */
                ctx.fillText(car.name + " (Lap " + Math.min(car.lap, totalLaps) + "/" + totalLaps + ")", car.x - 30, car.y - 25); /* Draw label above car */
            }}

            // Primary RequestAnimationFrame Game Loop Engine
            function gameLoop() {{
                // Update Player Physics
                updateCar(p1, "w", "a", "d"); /* Process P1 W/A/D keyboard state */
                updateCar(p2, "ArrowUp", "ArrowLeft", "ArrowRight"); /* Process P2 Arrow keys state */

                // Render Scene Frame
                drawTrack(); /* Draw background circuit */
                drawCar(p1); /* Draw P1 vehicle */
                drawCar(p2); /* Draw P2 vehicle */

                requestAnimationFrame(gameLoop); /* Schedule next frame render step */
            }}

            // Kick off game loop execution engine
            gameLoop(); /* Begin rendering execution */
        </script> <!-- End JavaScript Arcade Engine -->
    </body> <!-- End Body Element -->
    </html> <!-- End HTML Document -->
    """  # End Python multi-line format string containing HTML/JS payload

    # Render HTML5 Canvas Game Inside Streamlit App Component Interface
    components.html(
        game_html, height=560
    )  # Embed HTML5 canvas frame using Streamlit components API

    # Race completion recording interface section
    st.subheader("🏁 Record Match Outcome")  # Subheader for manual sync
    res_col1, res_col2, res_col3 = st.columns(
        [2, 2, 1]
    )  # Setup column grid for reporting

    with res_col1:  # Winner selection dropdown
        winner_selected = st.selectbox(
            "Select Race Winner", [p1_name, p2_name], key="win_select"
        )  # Pick winner name

    with res_col2:  # Finish time input field
        time_elapsed = st.number_input(
            "Race Finish Duration (Seconds)",
            min_value=1.0,
            max_value=300.0,
            value=15.0,
            step=0.5,
            key="time_input",
        )  # Capture race time

    with res_col3:  # Submit score button column
        st.write("")  # Spacing placeholder
        st.write("")  # Spacing placeholder
        if st.button("Submit Result", use_container_width=True):  # Click submit
            update_scores(
                winner_selected, time_elapsed, speed_level
            )  # Execute points system update routine
            st.success(
                f"Updated statistics for {winner_selected}!"
            )  # Show confirmation banner

with tab2:  # Global Leaderboard Tab Context
    st.subheader("🏆 Driver Standings & Ranking System")  # Leaderboard header

    if st.session_state.leaderboard:  # Check if records exist in system
        # Convert dictionary state into structured Pandas DataFrame
        df_lb = pd.DataFrame.from_dict(
            st.session_state.leaderboard, orient="index"
        )  # Convert dictionary keys into rows
        df_lb.index.name = "Driver Name"  # Name driver column index

        # Sort leaderboard by Total Score descending, then by Fastest Time ascending
        df_lb = df_lb.sort_values(
            by=["Total Score", "Fastest Time (s)"], ascending=[False, True]
        )  # Execute multi-column sort

        # Display formatted Streamlit DataFrame
        st.dataframe(
            df_lb.style.highlight_max(axis=0, subset=["Total Score"], color="#2e7d32"),
            use_container_width=True,
        )  # Render styled data table
    else:  # Render notice if no matches played yet
        st.info(
            "No races recorded yet. Complete a race in the Arena and submit scores to populate ranks!"
        )  # Render informational prompt banner
