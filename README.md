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
| Mute | M |
| Recover onto the racing line | R |
| Player 2 (hot seat) | I J K L, U for nitro |

Phones get on-screen touch buttons automatically. Click the arena once so it
takes keyboard focus.

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
* **Winner** — a five-note fanfare (a lower three-note one if you didn't win).

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

## Multiplayer with a QR code

1. On the lobby screen choose **Create room** — you get a 5-character code
   (ambiguity-free alphabet, no O/0/I/1) and a QR code.
2. Others scan the QR, or open the app and use **Join with a code**.
3. Everyone lands on the same circuit. The first driver to press START begins
   the countdown for the whole room.

Each browser posts its car position ~12 times a second to a small JSON API that
runs alongside Streamlit (port `8765` by default, override with
`RACE_API_PORT`). Everyone sees everyone else's car, name plate and gap live.

**For players on other devices**, set *Host / LAN IP* in the room panel to your
machine's LAN address (not `localhost`) and allow ports **8501** and **8765**
through your firewall. If you're on a hosted/HTTPS Streamlit deployment, browsers
block the plain-HTTP API call — run it on your own network, or put the API behind
the same HTTPS origin.

---

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
python3 tests/test_core.py       # player store + room API
python3 tests/run_headless.py    # full race in headless Chromium, checks for JS errors
```

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
