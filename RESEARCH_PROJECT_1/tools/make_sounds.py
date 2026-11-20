"""Synthesised sounds for MARROW (numpy only, no samples).

Makes the sounds that synthesis does well; real recordings (footsteps,
paper, car, door creak) are downloaded separately into sounds/.

    python tools/make_sounds.py            -> export/sounds/*.wav

Loops are built so they repeat without a click: every noise is made in the
frequency domain (an FFT noise is periodic by nature) and every envelope is
a sum of whole-cycle sines, so the end of the file runs straight into the
start.
"""
import os
import wave

import numpy as np

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "export", "sounds")
rng = np.random.default_rng(1702)


# ---------------------------------------------------------------- helpers
def shaped_noise(n, lo, hi, tilt=-1.0, soft=0.25):
    """Periodic noise, n samples, band lo..hi Hz with smooth edges.
    tilt = spectral slope in dB/oct-ish (-1 pinkish, -2 brownish)."""
    f = np.fft.rfftfreq(n, 1.0 / SR)
    spec = rng.normal(size=f.size) + 1j * rng.normal(size=f.size)
    f1 = np.maximum(f, 1.0)
    gain = f1 ** (tilt / 2.0)
    # soft band edges (in octaves)
    lo_e = 1.0 / (1.0 + np.exp(-(np.log2(f1 / lo)) / soft))
    hi_e = 1.0 / (1.0 + np.exp((np.log2(f1 / hi)) / soft))
    spec *= gain * lo_e * hi_e
    spec[0] = 0
    x = np.fft.irfft(spec, n)
    return x / (np.abs(x).max() + 1e-9)


def band(x, lo, hi, soft=0.2):
    """Filter any signal (treated as periodic) to lo..hi Hz."""
    n = x.size
    f = np.maximum(np.fft.rfftfreq(n, 1.0 / SR), 1.0)
    lo_e = 1.0 / (1.0 + np.exp(-(np.log2(f / lo)) / soft))
    hi_e = 1.0 / (1.0 + np.exp((np.log2(f / hi)) / soft))
    return np.fft.irfft(np.fft.rfft(x) * lo_e * hi_e, n)


def slow_env(n, seconds, parts, lo_cyc=1, hi_cyc=8, floor=0.0):
    """Periodic random envelope 0..1 made of whole-cycle sines."""
    t = np.arange(n) / n
    e = np.zeros(n)
    for _ in range(parts):
        c = rng.integers(lo_cyc, hi_cyc + 1)
        e += rng.uniform(0.3, 1.0) * np.sin(2 * np.pi * c * t + rng.uniform(0, 6.28))
    e = (e - e.min()) / (e.max() - e.min() + 1e-9)
    return floor + (1 - floor) * e


def adsr(n, a, d, curve=3.0):
    """One-shot envelope: attack a s, decay d s (exponential-ish)."""
    t = np.arange(n) / SR
    up = np.clip(t / max(a, 1e-4), 0, 1) ** 1.5
    down = np.exp(-np.clip(t - a, 0, None) * curve / max(d, 1e-4))
    return up * down


def add_wrapped(dst, src, start):
    """Add src into dst at start, wrapping past the end (for loops)."""
    n = dst.size
    idx = (start + np.arange(src.size)) % n
    np.add.at(dst, idx, src)


def stereo_wide(x, delay_ms=11):
    """Cheap width: right channel = slightly delayed, re-filtered copy."""
    d = int(SR * delay_ms / 1000)
    r = np.roll(x, d) * 0.9 + band(x, 80, 9000) * 0.1
    return np.stack([x, r], axis=1)


def save(name, x, peak=0.89):
    os.makedirs(OUT, exist_ok=True)
    x = np.asarray(x, dtype=np.float64)
    x = x / (np.abs(x).max() + 1e-9) * peak
    if x.ndim == 1:
        x = x[:, None]
    pcm = (x * 32767).astype("<i2")
    path = os.path.join(OUT, name + ".wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(pcm.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    rms = np.sqrt((x ** 2).mean())
    print(f"{name:22s} {x.shape[0]/SR:6.2f} s  ch {pcm.shape[1]}  rms {20*np.log10(rms):6.1f} dBFS")


# ---------------------------------------------------------------- sounds
def wind_loop(seconds=48):
    """Night wind through trees: low roar + gusts + a thin whistle."""
    n = SR * seconds
    roar = shaped_noise(n, 60, 900, tilt=-1.6)
    gust_env = slow_env(n, seconds, 6, 2, 9, floor=0.25)
    hiss = shaped_noise(n, 900, 5000, tilt=-1.0) * slow_env(n, seconds, 5, 4, 14, floor=0.0) ** 2
    # whistle: two narrow bands that swell with the strongest gusts
    whistle = (shaped_noise(n, 640, 700, soft=0.03) * 0.6 +
               shaped_noise(n, 1020, 1090, soft=0.03) * 0.4)
    whistle *= np.clip(gust_env - 0.6, 0, None) * 2.5
    leaves = shaped_noise(n, 2500, 9000, tilt=-0.5) * (gust_env ** 3) * 0.35
    left = roar * gust_env + hiss * 0.35 + whistle * 0.25 + leaves
    # right channel: same wind, gusts arrive a little later
    gust_r = np.roll(gust_env, int(SR * 0.7))
    roar_r = shaped_noise(n, 60, 900, tilt=-1.6)
    right = (0.6 * roar + 0.4 * roar_r) * gust_r + hiss * 0.3 + np.roll(whistle, 900) * 0.25 + np.roll(leaves, 2000)
    save("wind_loop", np.stack([left, right], axis=1))


def lake_loop(seconds=36):
    """Small waves lapping on the shore / dock posts."""
    n = SR * seconds
    out = np.zeros(n)
    bed = shaped_noise(n, 80, 600, tilt=-2.0) * 0.08  # constant low water
    t = 0.0
    while t < seconds:
        dur = rng.uniform(0.6, 1.4)
        m = int(SR * dur)
        body = band(rng.normal(size=m), 150, rng.uniform(900, 1600), soft=0.3)
        env = adsr(m, rng.uniform(0.08, 0.18), dur, curve=4.0)
        lap = body * env * rng.uniform(0.5, 1.0)
        # splash tail: brighter, shorter
        s = int(SR * 0.35)
        splash = band(rng.normal(size=s), 1800, 7000) * adsr(s, 0.01, 0.3, 5) * 0.35
        add_wrapped(out, lap, int(t * SR))
        add_wrapped(out, splash, int((t + rng.uniform(0.05, 0.15)) * SR))
        # droplets / plinks against wood
        for _ in range(rng.integers(0, 3)):
            k = int(SR * 0.06)
            f0 = rng.uniform(700, 1800)
            tt = np.arange(k) / SR
            drop = np.sin(2 * np.pi * (f0 * tt + 2500 * tt * tt)) * np.exp(-tt * 70) * 0.15
            add_wrapped(out, drop, int((t + rng.uniform(0.1, 0.8)) * SR))
        t += rng.uniform(1.3, 3.2)
    x = out + bed
    save("lake_loop", stereo_wide(x, 17))


def drone_loop(seconds=40):
    """Low unease under everything; beating sines + dark rumble."""
    n = SR * seconds
    tt = np.arange(n) / SR
    x = np.zeros(n)
    # frequencies chosen so each fits a whole number of cycles in the loop
    for f, a in [(41.0, 1.0), (41.25, 0.8), (61.5, 0.35), (82.05, 0.25), (123.0, 0.08)]:
        x += a * np.sin(2 * np.pi * f * tt)
    x *= 0.6 + 0.4 * slow_env(n, seconds, 3, 1, 4)
    rumble = shaped_noise(n, 25, 160, tilt=-2.0) * 0.5
    air = shaped_noise(n, 300, 1400, tilt=-1.0) * slow_env(n, seconds, 4, 2, 6) * 0.12
    save("drone_loop", stereo_wide(x * 0.55 + rumble + air, 23), peak=0.7)


def rattle_breath(cycles=1, seed_shift=0):
    """The lake thing breathing: slow wet inhale, rattling exhale.
    The rattle = noise chopped by an irregular ~22-34 Hz click train."""
    parts = []
    for c in range(cycles):
        inhale = rng.uniform(1.6, 2.2)
        hold = rng.uniform(0.15, 0.4)
        exhale = rng.uniform(2.2, 3.0)
        gap = rng.uniform(0.6, 1.4)
        total = inhale + hold + exhale + gap
        n = int(SR * total)
        t = np.arange(n) / SR
        x = np.zeros(n)
        # inhale: airy, rising pitch-ish band
        ni = int(SR * inhale)
        air = band(rng.normal(size=ni), 300, 2600, soft=0.35)
        env_i = np.sin(np.linspace(0, np.pi, ni)) ** 1.5
        x[:ni] += air * env_i * 0.45
        # exhale with the rattle
        s0 = int(SR * (inhale + hold))
        ne = int(SR * exhale)
        te = np.arange(ne) / SR
        rate = 26 + 6 * np.sin(2 * np.pi * te / exhale * 1.5) + rng.normal(0, 1.5)
        phase = np.cumsum(rate / SR + rng.normal(0, 0.004, ne))
        clicks = (np.sin(2 * np.pi * phase) > 0.55).astype(float)
        clicks = band(clicks, 60, 2200, soft=0.4)
        breath = band(rng.normal(size=ne), 120, 1800, soft=0.35)
        throat = np.sin(2 * np.pi * np.cumsum(np.full(ne, 74.0) + 6 * np.sin(2 * np.pi * te * 0.7)) / SR)
        env_e = np.clip(te / 0.25, 0, 1) * np.exp(-te * 0.55) * (1 - np.clip((te - exhale + 0.4) / 0.4, 0, 1))
        rattle = (breath * (0.25 + 0.75 * np.abs(clicks) / (np.abs(clicks).max() + 1e-9)) * 0.9
                  + throat * np.abs(clicks) / (np.abs(clicks).max() + 1e-9) * 0.35)
        x[s0:s0 + ne] += rattle * env_e
        parts.append(x)
    return np.concatenate(parts)


def rattle_sounds():
    one = rattle_breath(1)
    save("rattle_breath", one)                 # mono one-shot: spatialised in Unreal
    loop = rattle_breath(4)
    # loop it: crossfade the last 0.3 s into the start
    k = int(SR * 0.3)
    fade = np.linspace(0, 1, k)
    loop[:k] = loop[:k] * fade + loop[-k:] * (1 - fade)
    save("rattle_loop", loop[:-k])
    # far version: darker, quieter, smeared (heard from across the lake)
    far = band(loop[:-k], 80, 900, soft=0.5)
    far = far + 0.4 * np.roll(far, int(SR * 0.09)) + 0.25 * np.roll(far, int(SR * 0.23))
    save("rattle_far_loop", far, peak=0.6)


def flashlight_click():
    """Two-part plastic switch click."""
    n = int(SR * 0.12)
    x = np.zeros(n)
    for start, amp, f in [(0, 1.0, 3200), (int(SR * 0.035), 0.6, 2400)]:
        k = int(SR * 0.02)
        tt = np.arange(k) / SR
        c = (band(rng.normal(size=k), 1200, 8000) * np.exp(-tt * 400)
             + 0.4 * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 300))
        x[start:start + k] += amp * c
    save("flashlight_click", x, peak=0.7)


def warp_sting():
    """Short swell for the wrong-hand warp flashes: reversed rattle + sub drop."""
    n = int(SR * 2.4)
    t = np.arange(n) / SR
    r = rattle_breath(1)[: n][::-1]
    if r.size < n:
        r = np.pad(r, (n - r.size, 0))
    swell = np.clip(t / 2.0, 0, 1) ** 3
    sub = np.sin(2 * np.pi * (55 * t - 8 * t * t)) * np.exp(-np.clip(t - 1.9, 0, None) * 6) * swell
    hiss = band(rng.normal(size=n), 2000, 9000) * swell ** 2 * 0.3
    x = r * swell * 0.8 + sub * 0.7 + hiss
    x[int(SR * 2.05):] *= np.linspace(1, 0, n - int(SR * 2.05))
    save("warp_sting", stereo_wide(x, 9))


if __name__ == "__main__":
    wind_loop()
    lake_loop()
    drone_loop()
    rattle_sounds()
    flashlight_click()
    warp_sting()
    print("->", os.path.normpath(OUT))
