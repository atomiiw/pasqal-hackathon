"""Record a real run of the tier-S pipeline and render it as a terminal-replay video.

1. runs `python -m cvrp.run_all --tier S`, capturing each stdout line with a timestamp
2. renders frames of a terminal window (text appears at the real, compressed timing)
3. writes demo/run_tier_S.mp4 (imageio-ffmpeg) and demo/run_tier_S.gif (PIL)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "demo"
LOG = OUT / "run_tier_S.log.json"
CMD = [sys.executable, "-u", "-W", "ignore", "-m", "cvrp.run_all", "--tier", "S"]


def capture():
    t0 = time.time()
    lines = [(0.0, "$ python -m cvrp.run_all --tier S")]
    p = subprocess.Popen(CMD, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", bufsize=1)
    for line in p.stdout:
        line = line.rstrip("\n")
        if "DeprecationWarning" in line or line.strip().startswith("res = sim.run()") or not line.strip():
            continue
        lines.append((round(time.time() - t0, 2), line))
        print(f"{lines[-1][0]:7.1f}s {line}")
    p.wait()
    lines.append((round(time.time() - t0, 2), f"$  (exit {p.returncode}, {time.time() - t0:.0f} s)"))
    LOG.write_text(json.dumps(lines, indent=0), encoding="utf-8")
    return lines


def render(lines, target_seconds=32.0, fps=12, width=1280, height=720, rows=24):
    from PIL import Image, ImageDraw, ImageFont

    try:
        font = ImageFont.truetype("consola.ttf", 20)
        bold = ImageFont.truetype("consolab.ttf", 20)
    except OSError:
        font = bold = ImageFont.load_default()
    real_T = lines[-1][0]
    speed = real_T / target_seconds
    n_frames = int(target_seconds * fps) + fps * 3  # hold the end 3 s
    frames = []
    shown = []
    bg, fg, dim, green, blue = (18, 18, 20), (230, 230, 225), (140, 140, 135), (90, 200, 120), (100, 170, 255)
    for k in range(n_frames):
        t = k / fps * speed
        while len(shown) < len(lines) and lines[len(shown)][0] <= t:
            shown.append(lines[len(shown)][1])
        img = Image.new("RGB", (width, height), bg)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, width, 34], fill=(40, 40, 44))
        d.text((14, 8), "Pasqal-Hackathon  —  python -m cvrp.run_all --tier S   (real run, replayed at %.0fx)" % speed,
               font=font, fill=dim)
        y = 46
        for line in shown[-rows:]:
            col = fg
            f = font
            if line.startswith("$"):
                col, f = green, bold
            elif line.lstrip().startswith("[B"):
                col = blue
            elif "done in" in line:
                col, f = green, bold
            d.text((14, y), line[:150], font=f, fill=col)
            y += 27
        if k % fps < fps // 2 and len(shown) < len(lines):
            d.rectangle([14, y, 26, y + 22], fill=fg)
        frames.append(img)
    return frames, speed


def write_video(frames, fps=12):
    import imageio
    import numpy as np

    mp4 = OUT / "run_tier_S.mp4"
    with imageio.get_writer(mp4, fps=fps, codec="libx264", quality=8, macro_block_size=None) as w:
        for fr in frames:
            w.append_data(np.asarray(fr))
    gif = OUT / "run_tier_S.gif"
    small = [fr.resize((960, 540)) for fr in frames[::2]]
    small[0].save(gif, save_all=True, append_images=small[1:], duration=int(2000 / fps), loop=0, optimize=True)
    return mp4, gif


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    if "--render-only" in sys.argv and LOG.exists():
        lines = [tuple(x) for x in json.loads(LOG.read_text(encoding="utf-8"))]
    else:
        lines = capture()
    frames, speed = render(lines)
    mp4, gif = write_video(frames)
    print("wrote", mp4, gif, "| replay speed %.1fx, %d frames" % (speed, len(frames)))
