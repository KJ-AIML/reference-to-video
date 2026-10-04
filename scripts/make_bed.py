"""Original music bed for a brand film, synthesized from scratch with numpy/scipy (no samples, no third-party loops).
Warm F-major lo-fi/acoustic feel, 92 BPM: FM 'Rhodes-style' electric piano chords, additive plucked-guitar
arpeggio, round sine bass, soft sine-sweep kick, brushed noise shaker, convolution reverb from a synthetic decaying-noise IR.
Length follows src/vo.json `total`, so a changed VO length only needs a re-run:
  python scripts/make_bed.py [--out public/audio/music/bed.wav]   (48 kHz stereo, peak -6 dBFS; deps: numpy scipy soundfile)
Run it from the Remotion project root. Change BPM/PROG/seed to taste; record the method in CREDITS."""
import json, os, numpy as np, soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt
import sys
ROOT = os.getcwd()
vo = json.load(open(os.path.join(ROOT, 'src/vo.json')))
SR = 48000; DUR = vo['total'] / vo['fps']; N = int(DUR * SR) + SR
BPM = 92; BEAT = 60 / BPM; BAR = 4 * BEAT
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
def add(sig, t0, pan=0.0, g=1.0):
    i = int(t0 * SR); j = min(N, i + len(sig))
    if i >= N: return
    s = sig[: j - i] * g
    L[i:j] += s * np.sqrt(0.5 * (1 - pan)); R[i:j] += s * np.sqrt(0.5 * (1 + pan))
def rhodes(m, d, v=1.0):
    t = np.arange(int((d + 1.2) * SR)) / SR; f = hz(m)
    idx = 1.6 * np.exp(-t * 3.0) + 0.25                      # bright bell attack, mellows out
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    s += 0.18 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 6)
    env = np.minimum(1, t / 0.004) * np.exp(-t * 0.9) * np.where(t < d, 1, np.exp(-(t - d) * 6))
    return s * env * v
def pluck(m, v=1.0):
    t = np.arange(int(1.6 * SR)) / SR; f = hz(m); s = np.zeros_like(t)
    for n in range(1, 9):
        s += np.sin(2 * np.pi * n * f * t * (1 + 0.0004 * n * n)) / n ** 1.4 * np.exp(-t * (2.2 + 1.6 * n))
    return s * np.minimum(1, t / 0.002) * v
def bass(m, d):
    t = np.arange(int((d + 0.2) * SR)) / SR; f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.15 * np.sin(4 * np.pi * f * t)
    return s * np.minimum(1, t / 0.01) * np.where(t < d, np.exp(-t * 1.2), np.exp(-d * 1.2) * np.exp(-(t - d) * 30))
def kick():
    t = np.arange(int(0.35 * SR)) / SR
    return np.sin(2 * np.pi * (48 * t + 60 / 25 * (1 - np.exp(-t * 25)))) * np.exp(-t * 11)
hp = butter(2, 6000, 'hp', fs=SR, output='sos')
def shaker(v):
    t = np.arange(int(0.09 * SR)) / SR
    return sosfilt(hp, rng.standard_normal(len(t))) * np.exp(-t * 55) * np.minimum(1, t / 0.012) * v
# Fmaj9 - Am7 - Dm9 - Bbmaj7(#11-ish) / C on the last bar of every 8; voicings in MIDI
PROG = [(41, [57, 60, 64, 67]), (45, [55, 60, 64, 67]), (38, [57, 60, 64, 65]), (46, [57, 62, 65, 69]),
        (41, [57, 60, 64, 67]), (45, [55, 60, 64, 67]), (38, [57, 60, 62, 65]), (48, [58, 62, 64, 67])]
ARP = [0, 2, 1, 3, 2, 1, 3, 2]
nbars = int(np.ceil(DUR / BAR))
for b in range(nbars):
    t0 = b * BAR; root, ch = PROG[b % 8]; full = b >= 1     # bar 0: keys only, groove enters at bar 1
    for k, m in enumerate(ch):                              # chord on 1, soft re-strike on the 'and' of 3 (syncopated)
        add(rhodes(m, BAR * 0.62, 0.22), t0 + k * 0.012, pan=-0.25 + 0.15 * k)
        add(rhodes(m + 12 if k == 3 else m, BAR * 0.3, 0.12), t0 + 2.5 * BEAT + k * 0.01, pan=-0.2 + 0.12 * k)
    if not full: continue
    add(bass(root, BEAT * 1.4), t0, g=0.32); add(bass(root + 7 if b % 2 else root, BEAT * 0.9), t0 + 2.5 * BEAT, g=0.26)
    add(bass(root + 12, BEAT * 0.4), t0 + 3.5 * BEAT, g=0.14)
    for e in range(8):                                      # eighth-note plucked arpeggio, light swing, sparse on bar ends
        if b % 4 == 3 and e >= 6: continue
        m = ch[ARP[e]] + 12; sw = 0.04 * BEAT if e % 2 else 0
        add(pluck(m, 0.11 * (1.0 if e % 2 == 0 else 0.75)), t0 + e * BEAT / 2 + sw, pan=0.35)
    for q in (0, 2):  add(kick(), t0 + q * BEAT, g=0.38)
    add(kick(), t0 + 3.5 * BEAT, g=0.16)
    for s16 in range(16):
        sw = 0.05 * BEAT if s16 % 2 else 0
        add(shaker(0.05 if s16 % 4 == 2 else 0.028), t0 + s16 * BEAT / 4 + sw, pan=0.15 * (1 if s16 % 2 else -1))
# reverb: 1.8 s decaying stereo noise IR, low-passed, 22% wet
ti = np.arange(int(1.8 * SR)) / SR; lp = butter(2, 5000, 'lp', fs=SR, output='sos')
irL = sosfilt(lp, rng.standard_normal(len(ti))) * np.exp(-ti * 3.2); irR = sosfilt(lp, rng.standard_normal(len(ti))) * np.exp(-ti * 3.2)
irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
L2 = L + 0.22 * fftconvolve(L, irL)[:N]; R2 = R + 0.22 * fftconvolve(R, irR)[:N]
out = np.stack([L2, R2], 1)[: int(DUR * SR)]
t = np.arange(len(out)) / SR
out *= np.minimum(1, t / 1.0)[:, None] * np.clip((DUR - t) / 2.5, 0, 1)[:, None]   # 1 s fade-in, 2.5 s fade-out
out *= 10 ** (-6 / 20) / np.abs(out).max()
dst = os.path.join(ROOT, sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'public/audio/music/bed.wav'); os.makedirs(os.path.dirname(dst), exist_ok=True); sf.write(dst, out.astype(np.float32), SR, subtype='PCM_24')
print(f'wrote {dst}  {DUR:.2f}s  {BPM} BPM  {nbars} bars')
