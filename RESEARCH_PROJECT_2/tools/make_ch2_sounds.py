"""Chapter 2's synthesised sounds (numpy), with Chapter 1's loop helpers (tools/make_sounds.py).

    python make_ch2_sounds.py      -> RESEARCH_PROJECT_2/export/sounds/*.wav

  underwater_loop   pressure in the ears: a deep muffled rumble that swells slowly, a faint fizz on top
  breath_loop       the thing in the basin breathing: a long low rattling inhale, a held beat, a sigh out
  hunter_loop       a dry clicking rattle (heard near its ring)
Every loop repeats without a click (see make_sounds.py).
"""
import os

import numpy as np

RP1_TOOL = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/tools/make_sounds.py"
ns = {"__name__": "ch1_sounds", "__file__": RP1_TOOL}
exec(open(RP1_TOOL, encoding="utf-8").read(), ns)
ns["OUT"] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "export", "sounds")
SR, shaped_noise, slow_env, save, stereo_wide = ns["SR"], ns["shaped_noise"], ns["slow_env"], ns["save"], ns["stereo_wide"]
rng = np.random.default_rng(2001)


def underwater_loop(seconds=40):
    n = SR * seconds
    low = shaped_noise(n, 18, 260, tilt=-1.6)
    swell = slow_env(n, seconds, 4, lo_cyc=1, hi_cyc=5, floor=0.45)
    fizz = shaped_noise(n, 2500, 7000, tilt=-0.5) * 0.04 * slow_env(n, seconds, 3, lo_cyc=2, hi_cyc=9, floor=0.2)
    return stereo_wide(low * swell + fizz)


def breath_loop(seconds=12):
    """One breath, 12 s: in for 4.5 s, hold, out for 5 s; low and rattling."""
    n = SR * seconds
    t = np.arange(n) / SR
    env = np.where(t < 4.5, np.sin(np.pi * t / 9.0) ** 2,                                    # swell in
          np.where(t < 6.0, 1.0, np.clip(np.cos(np.pi * (t - 6.0) / 12.0) ** 2, 0, 1)))       # hold, sigh out
    env *= np.clip(1.0 - np.maximum(0, t - 11.0), 0, 1)                                      # back to silence at the loop
    body = shaped_noise(n, 30, 420, tilt=-1.2)
    rattle = 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * (11 + 3 * env) * t))                   # a wet flutter in it
    return stereo_wide(body * env * rattle)


def hunter_loop(seconds=8):
    n = SR * seconds
    out = np.zeros(n)
    click = shaped_noise(int(SR * 0.012), 900, 5000, tilt=0.0) * np.hanning(int(SR * 0.012))
    t = 0.3
    while t < seconds - 0.2:
        burst = rng.integers(3, 9)
        for k in range(burst):
            i = int((t + k * rng.uniform(0.03, 0.06)) * SR)
            if i + len(click) < n:
                out[i:i + len(click)] += click * rng.uniform(0.5, 1.0)
        t += rng.uniform(0.6, 1.6)
    return stereo_wide(out + shaped_noise(n, 40, 180, tilt=-1.0) * 0.08)


if __name__ == "__main__":
    save("ch2_underwater_loop", underwater_loop())
    save("ch2_breath_loop", breath_loop())
    save("ch2_hunter_loop", hunter_loop())
    print("wrote", ns["OUT"])
