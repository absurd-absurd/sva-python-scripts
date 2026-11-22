"""Prepare the user's downloaded freesound recordings for the game (2026-11-22).

The originals live in sounds/downloads/ (gitignored: the wind alone is 200 MB). This decodes each with ffmpeg
(some are 32-bit float or 4-channel), cuts what the game needs, makes the loops seamless (the end cross-faded
into the start), levels them and writes 44.1 kHz 16-bit stereo wavs to export/sounds/rec_<name>.wav, which
unreal/place_sounds.py imports.

    python tools/prep_sounds.py

What each one is for (credits: sounds/README.md):
  music_loop     hualdk (timkahn)            ambient music under the whole game, not the one-year-later shot
  title_loop     yemxid (timkahn)            the title screen
  warp_bass      bass synth 98 (cvltiv8r)    plays with the warp
  growl          creature deep growl         the thing in the lake
  lake_rec_loop  lake shore ambience (mick)  the shore
  wind_rec_loop  wind through a door crack   wind everywhere
  bugs_loop      chicharras and bugs         night insects in the woods / lot
  car            car turning on and off      the opening
  step_grass_*   footsteps on grass          cut into single steps
  step_wood_*    footsteps on wooden floor   cut into single steps
  paper          picking up one paper        reading a note
  door_creak     door creak                  opening a door
  keys           jingling keys               picking up a key
"""
import os
import subprocess
import numpy as np
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "sounds", "downloads")
OUT = os.path.join(HERE, "..", "export", "sounds")
SR = 44100

FILES = {
    "hualdk": "879900__timkahn__hualdk.wav",
    "yemxid": "874213__timkahn__yemxid.wav",
    "bass": "797286__cvltiv8r__bass-synth-98-by-cvltiv8r.wav",
    "growl": "435150__vykroft__creature-deep-growl.wav",
    "lake": "705034__mick__2023-10-03-lake-shore-ambience.wav",
    "wind": "687450__zumbidos__strong-wind-through-door-crack.wav",
    "bugs": "397824__adrienpola__chicharras-and-bugs-on-the-road-to-minca-from-nuevo-mundo.wav",
    "car": "370897__sjturia__car_turning-on-and-off_interior.wav",
    "grass": "807862__designerschoice__feethmn-mcu_footsteps-on-grass_nicholas-judy_tdc.wav",
    "wood": "119913__ftpalad__footsteps-on-wooden-floor-and-carpet.aiff",
    "paper": "463689__usamah__picking-up-one-paper.wav",
    "door": "460542__coosemek__door-creak.wav",
    "keys": "444267__karinalarasart__jingling-keys.wav",
}


def load(key, start=None, dur=None, af=None):
    """Decode to float32 stereo at 44.1 kHz (ffmpeg downmixes 4 channels, converts float/24-bit)."""
    cmd = ["ffmpeg", "-v", "error"]
    if start is not None:
        cmd += ["-ss", str(start)]
    if dur is not None:
        cmd += ["-t", str(dur)]
    cmd += ["-i", os.path.join(SRC, FILES[key])]
    if af:
        cmd += ["-af", af]
    cmd += ["-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)


def level(x, rms=-20.0, peak=-1.0):
    """To a target loudness (RMS dB), but never past the peak limit."""
    g = 10 ** ((rms - rms_db(x)) / 20)
    g = min(g, 10 ** (peak / 20) / (np.abs(x).max() + 1e-9))
    return x * g


def loop(x, fade=3.0):
    """Seamless loop: the last `fade` seconds cross-faded (equal power) into the first ones, then cut off."""
    n = int(fade * SR)
    t = np.linspace(0, 1, n)[:, None]
    head, tail = x[:n], x[-n:]
    out = x[:-n].copy()
    out[:n] = head * np.sin(t * np.pi / 2) + tail * np.cos(t * np.pi / 2)
    return out


def trim_start(x, pre=0.01, rel=0.1):
    """Cut the silence before the sound (user 2026-11-22: sounds lagged behind the action - the keys started
    1 s late, the paper 0.6 s): start `pre` s before the first sample above `rel` of the peak."""
    a = np.abs(x).max(axis=1)
    i = int(np.argmax(a > a.max() * rel))
    return x[max(0, i - int(pre * SR)):]


def fades(x, a=0.01, b=0.05):
    na, nb = int(a * SR), int(b * SR)
    x = x.copy()
    x[:na] *= np.linspace(0, 1, na)[:, None]
    x[-nb:] *= np.linspace(1, 0, nb)[:, None]
    return x


def save(name, x):
    os.makedirs(OUT, exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(os.path.join(OUT, f"rec_{name}.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"rec_{name}.wav  {len(x) / SR:6.1f}s  rms {rms_db(x):6.1f} dB  peak {20 * np.log10(np.abs(x).max() + 1e-9):5.1f} dB")


def steps(x, name, n=4, gate_db=-32.0, min_gap=0.25):
    """Cut single footsteps out of a recording: find onsets on the loudness envelope."""
    mono = np.abs(x).mean(axis=1)
    win = int(0.01 * SR)
    env = np.convolve(mono, np.ones(win) / win, mode="same")
    thr = 10 ** (gate_db / 20) * env.max() / (10 ** (-6 / 20))
    above = env > thr
    starts, last = [], -1e9
    for i in np.flatnonzero(above[1:] & ~above[:-1]):
        if (i - last) / SR > min_gap:
            starts.append(i)
            last = i
    cut = []
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < len(starts) else len(x)
        seg = x[max(0, s - int(0.02 * SR)):min(e, s + int(0.45 * SR))]
        if len(seg) > 0.08 * SR:
            cut.append(seg)
    cut = sorted(cut, key=lambda s: -np.abs(s).max())[:n]    # the clearest ones
    for k, seg in enumerate(cut):
        save(f"{name}_{k + 1}", fades(trim_start(level(seg, -18, -3), 0.005), 0.003, 0.12))
    return len(starts)


if __name__ == "__main__":
    save("music_loop", loop(level(load("hualdk"), -24), 6.0))
    save("title_loop", loop(level(load("yemxid"), -22), 6.0))
    # user 2026-11-22: "really bad... lower it and stretch it out and warp it a little": a fifth lower and
    # about twice as long (asetrate + atempo), a slow pitch wobble (vibrato), quieter, long fade in/out
    WARPED = "asetrate=44100*0.66,aresample=44100,atempo=0.8,vibrato=f=2.5:d=0.35,aecho=0.6:0.5:180:0.25"
    save("warp_bass", fades(level(load("bass", af=WARPED), -24, -4), 0.4, 1.5))
    save("growl", fades(trim_start(level(load("growl"), -14, -1))))
    save("lake_rec_loop", loop(level(load("lake", 20, 66), -24), 4.0))
    save("wind_rec_loop", loop(level(load("wind", 120, 64), -26), 4.0))
    save("bugs_loop", loop(level(load("bugs", 10, 64), -28), 4.0))
    save("car", fades(trim_start(level(load("car"), -18, -1))))
    save("paper", fades(trim_start(level(load("paper", 0, 3.0), -20, -3))[:int(1.6 * SR)]))
    save("door_creak", fades(trim_start(level(load("door"), -18, -2))))
    save("keys", fades(trim_start(level(load("keys", 0, 3.5), -20, -3))[:int(1.6 * SR)]))
    print("grass steps found:", steps(load("grass"), "step_grass"))
    print("wood steps found:", steps(load("wood"), "step_wood"))
