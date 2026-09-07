# 🏁 Turbo Racing League

A 3D top-down/chase arcade racer that runs inside Streamlit. Rebuilt from
`gameapp.py` with a real circuit, synthesised sound, a start/finish gantry,
QR-code multiplayer rooms and a player database saved as JSON.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open <http://localhost:8501>.

---

## What's in the box

| File | What it does |
|---|---|
| `app.py` | Streamlit UI: lobby, race setup, leaderboard, QR invites |
| `race_core.py` | `players.json` store + multiplayer room API (standard library only) |
| `game_html.py` | The Three.js / Web Audio racing client |
| `tests/test_core.py` | Unit tests for the player store and room API |
| `tests/run_headless.py` | Drives a whole race in headless Chromium and checks for JS errors |
| `players.json` | Created on first race — every driver, every result |

---

## Controls

| Action | Keys |
|---|---|
| Throttle / brake | ↑ ↓ or W S |
| Steer | ← → or A D |
| Nitro | Space (meter refills when you're off it) |
| Camera (chase / top-down / cinematic) | C |
| Fullscreen | F or the ⛶ button |
| Sound / music | M / B |
| Recover onto the racing line | R |
| Player 2 (hot seat) | I J K L, U for nitro |

Click the arena once so it takes keyboard focus.

### On a phone or tablet

Touch devices get a purpose-built layout: steering under the left thumb, a large
GAS pad plus BRAKE and NITRO under the right, haptic feedback where the device
supports it, and a prompt to turn the phone landscape. The HUD rearranges for a
small screen, page scroll and pinch-zoom are locked out while you drive, and
shadows and antialiasing switch off automatically so the frame rate holds up.

---

## Sound

Every effect is synthesised in the browser with the Web Audio API — there are no
audio files to download or ship:

* **Engine** — three detuned oscillators through a low-pass filter; pitch and
  filter cutoff follow speed and throttle, so you hear the revs build.
* **Acceleration / wind** — filtered noise that rises with the square of speed.
* **Tyre screech** — band-passed noise when you slide, run wide or turn hard at speed.
* **Crash** — a low noise burst plus a thud; harder hits are louder and shake the camera.
* **Nitro** — a rising whoosh sweep.
* **Crowd** — a pink-noise grandstand bed that swells when you complete a lap,
  crash or take the flag.
* **Start lights** — three beeps and a long tone on GO.
* **Overtake** — a passing whoosh, a chime and a crowd swell the moment you take
  a place off someone, with the position call-out on screen.
* **Winner** — a five-note fanfare (a lower three-note one if you didn't win).

**Music.** An original drift-style loop — four-on-the-floor kick, off-beat hats, a
driving bass line and a minor-pentatonic arp, all synthesised — sits under the
race. It ducks automatically as you accelerate and dips on impacts so the engine
and crashes always cut through, and it has its own volume slider. **B** toggles
it. To race to your own music instead, upload an mp3/ogg/wav in the sidebar; it
plays through the same ducking mix. (No commercial tracks are bundled — use your
own files for anything you have the rights to.)

Audio starts on the first click (browsers require a gesture), and M mutes it.

---

## The circuit

Three layouts — Sunset Oval, Harbour Sweep and Grand Circuit — built as closed
Catmull-Rom curves and checked so no part of the track passes within 37 m of
another part (the old version's layouts overlapped themselves).

Each circuit has tarmac with lane markings, red/white curbs, tyre-wall barriers,
three grandstands with an animated crowd, trees, and a **start/finish gantry**:
a lit board carrying the circuit name and lap count, five start lights that go
red through the countdown, and the checkered line painted across the track.

A lap only counts when you pass all eight sectors **in order**, so reversing
back over the line or cutting the corner behind it does nothing.

---

## Two players

**Same computer** — tick *Local 2-player (hot seat)* in the sidebar. Player 1 uses
the arrows, Player 2 uses I / J / K / L with U for nitro, and each picks their own
paint colour.

**Two devices**

1. Choose **Create room** — you get a 5-character code (no O/0/I/1, so it's easy
   to read aloud) and a QR code.
2. The other player scans it, or opens the app and uses **Join with a code**.
3. The room's host sets circuit, laps and engine class; anyone joining is matched
   to those settings automatically, so you're always racing the same event.
4. The first driver to press START begins the countdown for everyone.

Each browser posts its car position ~12×/sec, and the chip above the arena shows
how many drivers are connected. The API is mounted on **Streamlit's own port**, so
one open port (8501) covers everything and HTTPS deployments stay same-origin. If
that mount ever fails on a future Streamlit release, it falls back to a standalone
server on port 8765 (`RACE_API_PORT`) and the game finds it automatically.

### If the QR code doesn't open on a phone

Almost always one of these:

* **Both devices must be on the same Wi-Fi.** Mobile data or a guest network
  cannot reach your computer.
* **The address must be your LAN IP**, not `localhost` — a QR pointing at
  `localhost` opens the phone's own machine. Pick a `192.168.x` / `10.x` address
  in the room panel's dropdown; it lists every address this machine has, so avoid
  VPN and virtual-adapter ones.
* **Streamlit must listen on all interfaces**:
  `streamlit run app.py --server.address 0.0.0.0`
* **The firewall must allow port 8501** (Windows: allow Python on private networks).

The room panel has a **Check that phones can reach this** button that tests the
address and port for you and says which of the above is wrong.

---

## Cars, colours and names

Player 1 and Player 2 each choose from twelve paints in the sidebar; the AI takes
whatever colours are left, so no two cars look alike. Every driver's name floats
above their car during the race, scaled by camera distance so it stays readable
from the chase camera and from the top-down view, and your own car carries a
coloured ground ring so you can find yourself in a pack.

## Player data

`players.json` sits next to `app.py` and looks like this:

```json
{
  "version": 2,
  "updated": 1757203200.0,
  "drivers": {
    "Amna": {"name": "Amna", "wins": 3, "races": 7, "points": 1840,
             "best_time": 58.42, "best_lap": 18.91, "top_speed": 241,
             "crashes": 4, "first_seen": 1757200000.0, "last_seen": 1757203200.0}
  },
  "races": [
    {"ts": 1757203200.0, "driver": "Amna", "position": 1, "field": 4,
     "total_time": 58.42, "best_lap": 18.91, "laps": 3, "track": 2,
     "power": 4, "room": "K7QD2"}
  ]
}
```

* Written the moment a race ends, with an atomic replace, so it's never
  half-saved. A corrupt file is moved to `players.json.broken` rather than lost.
* Points are Formula-style: `(field − position + 1) × 40`, a 60-point win bonus,
  all scaled by engine class.
* Change the location with `RACE_DATA_PATH=/somewhere/players.json`.
* The browser also keeps a `localStorage` copy as a backup, so a solo race still
  records something if the server is unreachable.

---

## Bugs fixed from the original `gameapp.py`

* Results were sent by rewriting the parent URL (`window.parent.location.search`),
  which reloaded the whole app mid-race and could re-apply the same result on
  every rerun. Results now POST to a real endpoint.
* Cars started **on** the start point, so lap 1 was credited instantly and the
  race could end in a few seconds. Laps are now sector-validated.
* The AI incremented a lap every time its waypoint index wrapped, whether or not
  it had driven the lap.
* `Win Rate %` divided by zero for a driver with no races.
* The camera never handled window resize, so the canvas stretched.
* There was no track collision at all — cars could drive across the grass and
  still trip the finish check.
* The leaderboard lived in `st.session_state` and vanished on refresh.
* `loser` was computed and never used; `Best Time` was compared against a missing
  key for new drivers.
* First lap time was discarded and the finish time double-subtracted the
  countdown (both found and fixed during testing).

---

## Testing

```bash
python3 tests/test_core.py        # player store + room API (25 checks)
python3 tests/run_headless.py     # full race in headless Chromium, checks for JS errors
python3 tests/run_multiplayer.py  # two real browsers in one room
```

`run_multiplayer.py` opens two headless browsers against a real room server and
asserts that each sees the other's car moving, that the host pressing START also
starts the joiner, that chosen paint colours survive, and that both results land
in `players.json`.

`run_headless.py` swaps in a small maths-only stand-in for three.js, puts the AI
in charge of the player car and asserts that the race starts, laps are credited,
a best lap is recorded and the results screen appears with no JavaScript errors.

---

## Troubleshooting

**Black arena / "Could not load the 3D engine"** — three.js is loaded from a CDN;
the machine needs internet the first time. The app tries cdnjs, then jsDelivr,
then unpkg.

**Keyboard does nothing** — click inside the arena once; the game lives in an
iframe and needs focus.

**Fullscreen won't open** — some browsers block fullscreen inside a Streamlit
iframe. The button falls back to a theatre mode that expands the frame to fill
the page; press F again to come back.

**No sound** — browsers need a gesture first, so audio starts when you press
START. Check the M toggle and the volume slider.

**Port 8765 already in use** — the app falls back to a random free port
automatically; the sidebar shows which one is live.
