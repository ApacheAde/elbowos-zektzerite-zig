# Zektzerite Zig

Full-colour Python 3 neon light-cycle arcade for [ElbowOS](https://x.com/ElbowOS).

Ribbon a wine-dark grid with a lime bike. Coral and ice rivals paint their own trails. Gold prisms score. Walls and ribbons both kill. Crash and you respawn — the circuit keeps moving.

Not a ROM, not an emulator, not a Tron clone: original grid, walls, prism pickups, and bike art.

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 zektzerite_zig.py --play
```

A / Left turn left. D / Right turn right. R restart. Esc quit.

## Record a 9:16 reel

```bash
python3 zektzerite_zig.py --record
```

Headless autoplay writes a 15s 1080x1920 H.264 MP4 (`SDL_VIDEODRIVER=dummy`, ffmpeg libx264 yuv420p CRF 20, +faststart). Override the path with `ELBOWOS_MP4`.

## Links

* Featured account: https://x.com/ElbowOS
* Drive reel: https://drive.google.com/file/d/1ltQ78CzkWRYE7h0-iJdq4EWplDukEPLt/view?usp=drivesdk
* Repo: https://github.com/ApacheAde/elbowos-zektzerite-zig
