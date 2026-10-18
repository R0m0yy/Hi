"""Synthesises every sound in the game (original, procedural; no samples).

    /opt/bpyenv/bin/python tools/audio/make_audio.py      (needs numpy)

Writes 16-bit WAVs to game/assets/audio/sfx/ (one-shots, some with
variants name_1.wav ...) and game/assets/audio/loops/ (seamless ambience
loops and the music theme). Deterministic: fixed random seeds.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
ROOT = Path(__file__).resolve().parents[2] / "game" / "assets" / "audio"
SFX = ROOT / "sfx"
LOOPS = ROOT / "loops"
rng = np.random.default_rng(20261018)


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

def t_axis(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def noise(dur: float) -> np.ndarray:
    return rng.standard_normal(int(dur * SR))


def band(x: np.ndarray, lo: float, hi: float, soft: float = 0.25) -> np.ndarray:
    """Smooth band-pass by FFT masking (periodic: perfect for loops)."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    lo_m = 1.0 / (1.0 + np.exp(-(np.log(np.maximum(f, 1.0)) - np.log(max(lo, 1.0))) / soft)) if lo > 0 else 1.0
    hi_m = 1.0 / (1.0 + np.exp((np.log(np.maximum(f, 1.0)) - np.log(hi)) / soft))
    return np.fft.irfft(spec * lo_m * hi_m, len(x))


def env(n: int, attack: float, decay: float, sustain: float = 0.0) -> np.ndarray:
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    d = np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-4))
    return a * (sustain + (1 - sustain) * d)


def chirp(dur: float, f0: float, f1: float, curve: float = 1.0) -> np.ndarray:
    t = t_axis(dur)
    k = (t / dur) ** curve
    f = f0 + (f1 - f0) * k
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def tone(dur: float, freq: float, partials=((1, 1.0),), decay: float = 0.4) -> np.ndarray:
    t = t_axis(dur)
    x = sum(a * np.sin(2 * np.pi * freq * m * t) * np.exp(-t / (decay / m ** 0.5)) for m, a in partials)
    return x


def pluck(freq: float, dur: float, bright: float = 0.6, decay: float = 0.996) -> np.ndarray:
    """Karplus-Strong plucked string, processed a period at a time."""
    n = int(dur * SR)
    period = max(2, int(round(SR / freq)))
    buf = rng.uniform(-1, 1, period)
    buf = band(np.tile(buf, 4), 40, 2000 + 6000 * bright)[:period] * 2.5
    out = np.empty(n + period)
    out[:period] = buf
    pos = period
    prev = buf
    while pos < n + period:
        nxt = decay * 0.5 * (prev + np.roll(prev, 1))
        m = min(period, n + period - pos)
        out[pos:pos + m] = nxt[:m]
        prev = nxt
        pos += m
    return out[period:]


def place(dst: np.ndarray, src: np.ndarray, at: float, gain: float = 1.0) -> None:
    i = int(at * SR)
    if i >= len(dst):
        return
    m = min(len(src), len(dst) - i)
    dst[i:i + m] += src[:m] * gain


def norm(x: np.ndarray, peak: float = 0.85) -> np.ndarray:
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def fade(x: np.ndarray, fin: float = 0.004, fout: float = 0.03) -> np.ndarray:
    n = len(x)
    a = np.ones(n)
    i = int(fin * SR)
    o = int(fout * SR)
    if i:
        a[:i] = np.linspace(0, 1, i)
    if o:
        a[-o:] *= np.linspace(1, 0, o)
    return x * a


def write(path: Path, x: np.ndarray, peak: float = 0.85) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(norm(x, peak), -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def write_stereo(path: Path, left: np.ndarray, right: np.ndarray, peak: float = 0.8) -> None:
    m = max(np.max(np.abs(left)), np.max(np.abs(right))) or 1.0
    st = np.stack([left, right], axis=1) / m * peak
    pcm = (np.clip(st, -1, 1) * 32767).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------------------
# One-shots
# ---------------------------------------------------------------------------

def sfx_pickup():
    x = np.zeros(int(0.22 * SR))
    place(x, tone(0.12, 660, ((1, 1), (2, 0.3)), 0.06), 0.0)
    place(x, tone(0.14, 990, ((1, 1), (2, 0.25)), 0.07), 0.06, 0.8)
    return fade(x)


def sfx_rustle(seed):
    n = noise(0.4)
    crackle = (rng.random(len(n)) < 0.02).astype(float) * rng.uniform(0.5, 1.0, len(n))
    am = band(crackle, 1, 40) * 6 + 0.25
    x = band(n, 1400, 6500) * np.clip(am, 0, None) * env(len(n), 0.03, 0.18)
    return fade(x)


def sfx_stone():
    x = np.zeros(int(0.2 * SR))
    place(x, band(noise(0.05), 1800, 5500) * env(int(0.05 * SR), 0.001, 0.012), 0.0)
    place(x, tone(0.15, 130 + rng.uniform(-10, 10), ((1, 1), (2.7, 0.3)), 0.04), 0.0, 0.7)
    place(x, band(noise(0.04), 2500, 6000) * env(int(0.04 * SR), 0.001, 0.008), 0.045, 0.5)
    return fade(x)


def sfx_chop():
    x = np.zeros(int(0.42 * SR))
    f0 = rng.uniform(120, 150)
    place(x, chirp(0.3, f0 * 1.6, f0, 0.3) * env(int(0.3 * SR), 0.001, 0.07), 0.0, 1.0)
    place(x, band(noise(0.06), 300, 2500) * env(int(0.06 * SR), 0.0005, 0.015), 0.0, 1.1)
    place(x, tone(0.3, rng.uniform(380, 460), ((1, 1), (2.3, 0.4)), 0.06), 0.0, 0.45)
    return fade(x)


def sfx_rock_hit():
    x = np.zeros(int(0.35 * SR))
    place(x, band(noise(0.08), 900, 4200) * env(int(0.08 * SR), 0.0005, 0.02), 0.0, 1.2)
    place(x, tone(0.3, rng.uniform(760, 880), ((1, 1), (2.76, 0.5), (5.4, 0.2)), 0.05), 0.0, 0.5)
    return fade(x)


def sfx_swing():
    n = noise(0.3)
    x = np.zeros_like(n)
    for k in range(6):  # sweep a band upward
        seg = band(n, 500 + k * 220, 900 + k * 330)
        w = np.exp(-((np.arange(len(n)) / SR - 0.04 - k * 0.025) / 0.04) ** 2)
        x += seg * w
    return fade(x * env(len(n), 0.04, 0.12))


def sfx_eat():
    x = np.zeros(int(0.6 * SR))
    for i in range(5):
        at = 0.05 + i * rng.uniform(0.07, 0.12)
        b = band(noise(0.06), 500, 3500) * env(int(0.06 * SR), 0.002, 0.02)
        place(x, b, at, rng.uniform(0.6, 1.0))
    return fade(x)


def sfx_drink():
    x = np.zeros(int(0.7 * SR))
    for i in range(3):
        g = chirp(0.12, 260, 150, 0.6) * env(int(0.12 * SR), 0.01, 0.04)
        place(x, g, 0.05 + i * 0.2, 1.0)
        place(x, band(noise(0.08), 300, 1200) * env(int(0.08 * SR), 0.01, 0.03), 0.07 + i * 0.2, 0.3)
    return fade(x)


def sfx_splash(dur=0.8, big=1.0):
    n = noise(dur)
    x = band(n, 300, 5000 * big + 1500) * env(len(n), 0.005, 0.18 * big)
    for i in range(int(6 * big)):
        b = chirp(0.05, rng.uniform(500, 1200), rng.uniform(1300, 2600)) * env(int(0.05 * SR), 0.002, 0.015)
        place(x, b, rng.uniform(0.05, dur * 0.7), 0.25)
    return fade(x)


def sfx_bubbles(dur=0.9, count=10, down=False):
    x = np.zeros(int(dur * SR))
    for i in range(count):
        f0 = rng.uniform(400, 900)
        f1 = f0 * (0.6 if down else 1.8)
        b = chirp(0.05, f0, f1) * env(int(0.05 * SR), 0.002, 0.015)
        place(x, b, rng.uniform(0.0, dur * 0.8), rng.uniform(0.3, 0.8))
    return fade(x)


def sfx_step(seed_gain=1.0, grass=False):
    n = noise(0.1)
    if grass:
        x = band(n, 1200, 5000) * env(len(n), 0.004, 0.03)
    else:
        x = band(n, 150, 1400) * env(len(n), 0.003, 0.025)
        x += band(noise(0.1), 2000, 5000) * env(len(n), 0.002, 0.01) * 0.2
    return fade(x * seed_gain)


def sfx_creak():
    t = t_axis(0.5)
    f = 170 + 40 * np.sin(2 * np.pi * 3 * t) + 30 * t
    saw = 2 * ((np.cumsum(f) / SR) % 1.0) - 1
    x = band(saw, 300, 2500) * env(len(t), 0.05, 0.2)
    place(x, tone(0.2, 110, ((1, 1),), 0.05), 0.35, 0.8)
    return fade(x)


def sfx_sizzle():
    n = noise(1.3)
    crack = (rng.random(len(n)) < 0.004) * rng.uniform(0.3, 1.0, len(n))
    x = band(n, 2500, 9000) * env(len(n), 0.05, 0.6) * 0.6 + band(crack, 1500, 8000) * 3
    return fade(x)


def sfx_knock(f=300):
    return tone(0.18, f, ((1, 1), (2.4, 0.5)), 0.04) + band(noise(0.18), 500, 3000) * env(int(0.18 * SR), 0.0005, 0.01) * 0.6


def sfx_hammer(n=2):
    x = np.zeros(int((0.25 * n + 0.2) * SR))
    for i in range(n):
        place(x, sfx_knock(rng.uniform(260, 320)), i * 0.25)
    return fade(x)


def sfx_chime(notes=(523.25, 659.25, 783.99), gap=0.07, dur=0.9):
    x = np.zeros(int((dur + gap * len(notes)) * SR))
    for i, f in enumerate(notes):
        place(x, tone(dur, f, ((1, 1), (2, 0.35), (3.01, 0.15), (4.2, 0.08)), 0.35), i * gap, 0.8)
    return fade(x)


def sfx_click():
    return fade(tone(0.04, 1500, ((1, 1),), 0.008) + band(noise(0.04), 3000, 8000) * env(int(0.04 * SR), 0.0005, 0.004) * 0.3)


def sfx_whoosh(up=True, dur=0.25):
    n = noise(dur)
    lo, hi = (400, 2500) if up else (2500, 400)
    x = np.zeros_like(n)
    for k in range(5):
        fl = lo + (hi - lo) * k / 4
        w = np.exp(-((np.arange(len(n)) / SR - dur * (0.15 + 0.15 * k)) / (dur * 0.12)) ** 2)
        x += band(n, fl * 0.7, fl * 1.4) * w
    return fade(x)


def sfx_plop(big=1.0):
    x = np.zeros(int(0.5 * SR))
    place(x, chirp(0.12, 700 * big ** -0.3, 220, 0.4) * env(int(0.12 * SR), 0.002, 0.04), 0.0)
    place(x, band(noise(0.3), 400, 3000) * env(int(0.3 * SR), 0.003, 0.06 * big), 0.0, 0.4 * big)
    return fade(x)


def sfx_reel_clicks(dur=0.4, rate=28):
    x = np.zeros(int(dur * SR))
    for i in range(int(dur * rate)):
        place(x, sfx_click() * 0.5, i / rate)
    return fade(x)


def sfx_twang():
    p = pluck(880, 0.6, 1.0, 0.993) * env(int(0.6 * SR), 0.001, 0.15)
    place(p, band(noise(0.08), 3000, 9000) * env(int(0.08 * SR), 0.0005, 0.01), 0.0, 0.6)
    return fade(p)


def sfx_error():
    x = np.zeros(int(0.35 * SR))
    place(x, tone(0.14, 220, ((1, 1), (3, 0.3)), 0.08), 0.0)
    place(x, tone(0.16, 175, ((1, 1), (3, 0.3)), 0.08), 0.13)
    return fade(x)


def sfx_crack():
    x = band(noise(0.25), 800, 6000) * env(int(0.25 * SR), 0.0005, 0.03)
    place(x, sfx_knock(200), 0.0, 0.8)
    return fade(x)


def sfx_thud():
    return fade(tone(0.3, 80, ((1, 1), (2.2, 0.3)), 0.07) + band(noise(0.3), 60, 600) * env(int(0.3 * SR), 0.002, 0.05))


# ---------------------------------------------------------------------------
# Loops (seamless: periodic FFT noise and LFOs that divide the length)
# ---------------------------------------------------------------------------

def loop_ocean(dur=24.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = []
    for ch in range(2):
        base = band(rng.standard_normal(n), 60, 900, 0.5)
        hiss = band(rng.standard_normal(n), 900, 7000, 0.4)
        swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 8.0 + ch * 0.9) ** 2
        swell2 = 0.6 + 0.4 * np.sin(2 * np.pi * t / 6.0 + 1.7 + ch * 0.5) ** 4
        crash = np.maximum(0, np.sin(2 * np.pi * t / 12.0 + ch)) ** 8
        out.append(base * swell * 1.0 + hiss * (0.15 + 0.6 * crash) * swell2)
    return out


def loop_wind(dur=24.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = []
    for ch in range(2):
        x = band(rng.standard_normal(n), 250, 1400, 0.35)
        am = 0.5 + 0.5 * np.sin(2 * np.pi * t / 12.0 + ch * 1.3) * np.sin(2 * np.pi * t / 4.0)
        out.append(x * (0.4 + 0.6 * am ** 2))
    return out


def loop_underwater(dur=12.0):
    n = int(dur * SR)
    rum = band(rng.standard_normal(n), 30, 280, 0.4)
    x = rum.copy()
    for i in range(20):
        place(x, sfx_bubbles(0.4, 3) * 0.2, rng.uniform(0, dur - 0.5))
    return [x, np.roll(x, int(0.013 * SR))]


def loop_fire(dur=8.0):
    n = int(dur * SR)
    base = band(rng.standard_normal(n), 80, 900, 0.5) * 0.25
    crack = np.zeros(n)
    for i in range(140):
        b = band(noise(0.03), 1200, 7000) * env(int(0.03 * SR), 0.0005, 0.004)
        place(crack, b, rng.uniform(0, dur - 0.05), rng.uniform(0.2, 1.0))
    x = base + crack
    return [x, np.roll(x, int(0.02 * SR))]


# ---------------------------------------------------------------------------
# Music: a gentle island strum (Karplus-Strong ukulele, bass, marimba, shaker)
# ---------------------------------------------------------------------------

NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def hz(name: str, octave: int) -> float:
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave + 1) - 69) / 12)


CHORDS = {  # ukulele voicings, low to high (G4 C4 E4 A4 re-entrant feel)
    "C": [hz("G", 4), hz("C", 4), hz("E", 4), hz("C", 5)],
    "Am": [hz("A", 4), hz("C", 4), hz("E", 4), hz("A", 4)],
    "F": [hz("A", 4), hz("C", 4), hz("F", 4), hz("A", 4)],
    "G": [hz("G", 4), hz("D", 4), hz("G", 4), hz("B", 4)],
    "Em": [hz("G", 4), hz("E", 4), hz("G", 4), hz("B", 4)],
    "Dm": [hz("A", 4), hz("D", 4), hz("F", 4), hz("A", 4)],
}
BASS = {"C": hz("C", 2), "Am": hz("A", 1), "F": hz("F", 1), "G": hz("G", 1), "Em": hz("E", 2), "Dm": hz("D", 2)}
PROGRESSION = ["C", "Am", "F", "G", "C", "Em", "F", "G", "Am", "F", "C", "G", "Dm", "F", "G", "C"]
PENTA = [hz(n, o) for o, n in [(5, "C"), (5, "D"), (5, "E"), (5, "G"), (5, "A"), (6, "C"), (6, "D"), (6, "E")]]


def music_theme() -> list:
    bpm = 96
    beat = 60.0 / bpm
    bar = beat * 4
    dur = bar * len(PROGRESSION)
    n = int(dur * SR) + 1
    L = np.zeros(n)
    R = np.zeros(n)
    strum = [(0.0, 1, 1.0), (1.0, 1, 0.8), (1.5, -1, 0.55), (2.5, -1, 0.6), (3.0, 1, 0.8), (3.5, -1, 0.5)]
    for bi, ch in enumerate(PROGRESSION):
        t0 = bi * bar
        for (b, direction, vel) in strum:
            strings = CHORDS[ch] if direction > 0 else list(reversed(CHORDS[ch]))
            for si, f in enumerate(strings):
                p = pluck(f, 1.2, 0.55, 0.9965) * vel
                at = t0 + b * beat + si * 0.012
                place(L, p, at, 0.55 - si * 0.04)
                place(R, p, at + 0.004, 0.45 + si * 0.04)
        # bass on 1 and 3
        for b in (0, 2):
            bt = tone(beat * 1.6, BASS[ch], ((1, 1), (2, 0.25)), 0.5)
            place(L, bt, t0 + b * beat, 0.5)
            place(R, bt, t0 + b * beat, 0.5)
        # shaker on 8ths
        for k in range(8):
            s = band(noise(0.06), 5000, 11000) * env(int(0.06 * SR), 0.004, 0.02)
            g = 0.06 if k % 2 else 0.035
            place(L, s, t0 + k * beat / 2, g)
            place(R, s, t0 + k * beat / 2 + 0.01, g * 0.8)
    # Marimba melody: a calm pentatonic phrase every two bars (deterministic).
    mel_rng = np.random.default_rng(7)
    idx = 2
    for bi in range(0, len(PROGRESSION), 2):
        t0 = bi * bar
        rhythm = [0, 1, 1.5, 2.5, 3, 4.5, 5, 6] if bi % 4 == 0 else [0, 0.5, 1.5, 2, 3.5, 4, 6]
        for r in rhythm:
            idx = int(np.clip(idx + mel_rng.integers(-2, 3), 0, len(PENTA) - 1))
            m = tone(1.2, PENTA[idx], ((1, 1), (4.0, 0.35), (9.8, 0.08)), 0.45)
            pan = 0.5 + 0.3 * np.sin(idx)
            place(L, m, t0 + r * beat, 0.32 * (1 - pan) * 2)
            place(R, m, t0 + r * beat, 0.32 * pan * 2)
    # Wrap the tail into the start so the loop is seamless, then a light room reverb.
    total = int(dur * SR)
    for ch in (L, R):
        ch[:n - total] += ch[total:]
    L, R = L[:total], R[:total]
    for ch in (L, R):
        wet = np.zeros_like(ch)
        for d, g in ((0.031, 0.35), (0.053, 0.28), (0.077, 0.22), (0.113, 0.15)):
            wet += np.roll(ch, int(d * SR)) * g
        ch += wet * 0.5
    return [L, R]


# ---------------------------------------------------------------------------

def main() -> None:
    one = {
        "pickup": sfx_pickup(), "stone_pick": sfx_stone(), "swing": sfx_swing(), "eat": sfx_eat(),
        "drink": sfx_drink(), "splash": sfx_splash(0.9, 1.0), "dive": sfx_splash(0.6, 0.6) + np.pad(sfx_bubbles(0.6, 10, True), (0, 0))[:int(0.6 * SR)],
        "surface": sfx_splash(0.5, 0.5), "jump": sfx_whoosh(True, 0.18) * 0.5, "chest_open": sfx_creak(),
        "sizzle": sfx_sizzle(), "rummage": np.concatenate([sfx_rustle(1), sfx_knock(260)]), "hammer": sfx_hammer(2),
        "build": sfx_hammer(3), "boat_board": np.concatenate([sfx_creak()[:int(0.3 * SR)], sfx_splash(0.4, 0.4)]),
        "boat_bump": sfx_thud(), "error": sfx_error(), "ui_open": sfx_whoosh(True, 0.2) * 0.4,
        "ui_close": sfx_whoosh(False, 0.2) * 0.4, "ui_click": sfx_click(), "craft": sfx_chime(),
        "cast": np.concatenate([sfx_whoosh(True, 0.25), sfx_reel_clicks(0.35)]), "plop": sfx_plop(1.0),
        "nibble": sfx_plop(0.4) * 0.5, "bite": sfx_plop(1.6) + np.pad(sfx_splash(0.3, 0.4), (0, int(0.2 * SR))),
        "hook": np.concatenate([sfx_whoosh(True, 0.15), sfx_reel_clicks(0.25, 40)]), "line_snap": sfx_twang(),
        "catch": np.concatenate([sfx_splash(0.35, 0.6), sfx_chime((659.25, 783.99, 1046.5), 0.06, 0.8)]),
        "spear_whoosh": sfx_whoosh(True, 0.16), "spear_hit": sfx_plop(1.2) + np.pad(sfx_thud()[:int(0.3 * SR)], (0, int(0.2 * SR))),
        "break": sfx_crack(),
    }
    for name, x in one.items():
        write(SFX / f"{name}.wav", x, 0.8)
    for i in range(1, 4):
        write(SFX / f"rustle_{i}.wav", sfx_rustle(i), 0.7)
        write(SFX / f"chop_{i}.wav", sfx_chop(), 0.85)
    for i in range(1, 3):
        write(SFX / f"rock_hit_{i}.wav", sfx_rock_hit(), 0.85)
    for i in range(1, 5):
        write(SFX / f"step_sand_{i}.wav", sfx_step(rng.uniform(0.8, 1.0)), 0.6)
        write(SFX / f"step_grass_{i}.wav", sfx_step(rng.uniform(0.8, 1.0), True), 0.5)
    o = loop_ocean()
    write_stereo(LOOPS / "ocean.wav", o[0], o[1], 0.7)
    w = loop_wind()
    write_stereo(LOOPS / "wind.wav", w[0], w[1], 0.6)
    u = loop_underwater()
    write_stereo(LOOPS / "underwater.wav", u[0], u[1], 0.7)
    f = loop_fire()
    write_stereo(LOOPS / "fire.wav", f[0], f[1], 0.7)
    m = music_theme()
    write_stereo(LOOPS / "theme.wav", m[0], m[1], 0.8)
    print("audio ->", ROOT)


if __name__ == "__main__":
    main()
