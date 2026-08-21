# atak-plugin-omhud

OneMind HUD (OMHud) — tactical AR overlay plugin for ATAK. Three rendering modes built in Kivy, subscribes to OneMind NATS for live detections and CoT data.

---

## Modes

| Mode | Description |
|------|-------------|
| **GROUND** | IVAS-style soldier HUD — yellow oval reticle, range rings, bearing/range to target, MGRS position, compass heading |
| **ORBITAL** | Space tracking HUD — trajectory lines, orbital altitude, pass timing data |
| **ISR** | Airborne targeting pod — thermal inset frame, bearing/range readout, MGRS grid, target lock indicator |

---

## Architecture

```
Android device (ATAK)
└── atak-plugin-omhud  (Kivy app via Buildozer)
    ├── TacticalHUD widget  — Kivy canvas, 30fps draw loop
    ├── NATS subscriber     — fabric.vision.*.detect
    │   └── nats-py async   → detections injected into HUD
    └── GPS / CoT feed      — replace simulated coords with android.gps
```

The HUD renders on a transparent window (`clearcolor = 0,0,0,0`) so it overlays directly on the ATAK map.

---

## NATS integration

Subscribes to `fabric.vision.*.detect` for AI vision detections. Each message is a JSON object:

```json
{
  "label": "person",
  "confidence": 0.94,
  "bearing": 104,
  "range_m": 489,
  "mgrs": "11SPA1234567890"
}
```

Up to 20 detections are kept in memory and rendered as targeting overlays.

Set the NATS URL via environment:

```bash
NATS_URL=nats://localhost:4222 python main.py
```

---

## Build & deploy

Requires [Buildozer](https://buildozer.readthedocs.io/):

```bash
pip install buildozer
buildozer android debug deploy run
```

Config is in `buildozer.spec`. Target: Android 8+ (API 26+).

**Dependencies:**
- `kivy[full]` — UI framework
- `nats-py` — async NATS client

---

## Development

Run on desktop for fast iteration:

```bash
pip install kivy nats-py
python main.py
```

Swap modes at runtime by setting `self.mode` to `"GROUND"`, `"ORBITAL"`, or `"ISR"`.

---

## License

Apache 2.0 — OneMind OS
