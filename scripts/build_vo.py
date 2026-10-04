#!/usr/bin/env python3
"""Build src/vo.json (the film's only clock) and public/audio/vo/<id>.wav from per-line TTS takes.

  python scripts/build_vo.py --script script.json --lang en --whisper small.en
  python scripts/build_vo.py --script script.json --lang th --whisper large-v3-turbo   # Thai: use int16, not int8
  python scripts/build_vo.py ... --no-asr      # skip Whisper (proportional word times)

Each line:
- If <src>/<id>.wav exists: trim silence, convert to 48 kHz mono, level to -19 LUFS (static gain + soft limiter), and place it on the timeline.
  Word ("phrase" = a space-separated chunk of the script `text`) times come from faster-whisper word timestamps.
  These are mapped onto the script `text` (not `say`) character by character with difflib. Unmatched phrases are interpolated.
- If no wav exists: a PLACEHOLDER duration from `syllables` / --syl-rate (if the line has `syllables`) or words / (--wpm / 60),
  with proportional phrase times. vo.json then gets "placeholder": true, so the film can show a PREVIEW tag.
  Swapping in the real voice later = drop in the wavs, re-run, re-render.

Optional per-line fields in script.json:
- `gap_before` (s)
- `syllables` (for languages without word spaces)
- `off: true` (skip the line)

Optional top-level field `cer_aliases` {"from": "to"} normalises ref/ASR text before the approximate CER.
Deps: numpy soundfile librosa faster-whisper (and ffmpeg on PATH).
"""
import argparse, difflib, json, os, re, subprocess, unicodedata
import numpy as np, soundfile as sf, librosa

ap = argparse.ArgumentParser()
ap.add_argument('--script', default='script.json')
ap.add_argument('--src', default='scripts/vo/src', help='per-line takes: <id>.wav')
ap.add_argument('--out-audio', default='public/audio/vo')
ap.add_argument('--out-json', default='src/vo.json')
ap.add_argument('--fps', type=int, default=60)
ap.add_argument('--pre', type=float, default=1.0, help='pre-roll before line 1 (s)')
ap.add_argument('--hold', type=float, default=3.2, help='end hold incl. the loop back to the opening frame (s)')
ap.add_argument('--gap', type=float, default=0.45, help='default gap between lines (s)')
ap.add_argument('--syl-rate', type=float, default=3.5, help='placeholder syllables/s (measured: Thai TTS about 3.5)')
ap.add_argument('--wpm', type=float, default=145, help='placeholder words/min when a line has no `syllables`')
ap.add_argument('--lang', default='en')
ap.add_argument('--whisper', default='small.en', help='faster-whisper model name or local dir')
ap.add_argument('--compute', default='int8', help='int8 is fine for English; use int16 for Thai (int8 corrupted Thai tokens)')
ap.add_argument('--voice-label', default='synthetic TTS voice')
ap.add_argument('--no-asr', action='store_true')
a = ap.parse_args()

def lufs(path):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1])

def process(src, dst):
    x, sr = sf.read(src)
    if x.ndim > 1: x = x.mean(1)
    iv = librosa.effects.split(x, top_db=40)
    s0 = max(0, iv[0][0] - int(.04 * sr)); s1 = min(len(x), iv[-1][1] + int(.12 * sr)); y = x[s0:s1].copy()
    n = int(.008 * sr); y[:n] *= np.linspace(0, 1, n); y[-n:] *= np.linspace(1, 0, n)
    tmp = dst + '.tmp.wav'; sf.write(tmp, y, sr, subtype='PCM_24')
    g = -19 - lufs(tmp)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af',
                    f'aresample=192000,volume={g:.2f}dB,alimiter=limit=0.84:attack=3:release=60:level=disabled,aresample=48000:resampler=soxr',
                    '-ac', '1', '-c:a', 'pcm_s24le', dst], check=True)
    os.remove(tmp)
    return sf.info(dst).duration, round(g, 1)

def norm_chars(t):  # letters (incl. combining vowel/tone marks) and digits, lower-cased
    return [c.lower() for c in t if unicodedata.category(c)[0] in 'LMN']

REPEAT_MARKS = {'ๆ'}  # attach a standalone repeat mark to the previous phrase
def phrase_times(text, dur, words):
    """words: [(word, start, end)] in seconds from ASR, or None. Returns [(phrase, s, e)] in seconds."""
    phr = []
    for p in text.split(' '):
        if not p.strip(): continue
        if p in REPEAT_MARKS and phr: phr[-1] += ' ' + p
        else: phr.append(p)
    lens = [max(1, len(norm_chars(p))) for p in phr]
    if not words:
        tot = sum(lens); t0 = 0.05 * dur; span = 0.92 * dur; out = []; acc = 0
        for p, l in zip(phr, lens):
            s = t0 + span * acc / tot; acc += l; out.append((p, s, t0 + span * acc / tot))
        return out
    a_chars, a_t = [], []
    for w, s, e in words:
        cs = norm_chars(w)
        for i, c in enumerate(cs):
            a_chars.append(c); a_t.append((s + (e - s) * i / max(1, len(cs)), s + (e - s) * (i + 1) / max(1, len(cs))))
    s_chars, owner = [], []
    for k, p in enumerate(phr):
        for c in norm_chars(p): s_chars.append(c); owner.append(k)
    sm = difflib.SequenceMatcher(None, s_chars, a_chars, autojunk=False)
    hit = [[] for _ in phr]
    for blk in sm.get_matching_blocks():
        for j in range(blk.size): hit[owner[blk.a + j]].append(a_t[blk.b + j])
    times = [(min(h[0] for h in hs), max(h[1] for h in hs)) if len(hs) >= max(1, lens[k] // 3) else None for k, hs in enumerate(hit)]
    k = 0; out = []
    while k < len(phr):  # interpolate unmatched phrases between matched neighbours, proportional to length
        if times[k]: out.append((phr[k], *times[k])); k += 1; continue
        j = k
        while j < len(phr) and not times[j]: j += 1
        left = out[-1][2] if out else words[0][1]
        right = times[j][0] if j < len(phr) else max(left + 0.2, words[-1][2])
        tot = sum(lens[k:j]); acc = 0
        for m in range(k, j):
            s = left + (right - left) * acc / tot; acc += lens[m]; out.append((phr[m], s, left + (right - left) * acc / tot))
        k = j
    return out

def asr_words(model, path):
    x, _ = librosa.load(path, sr=16000)
    segs, _ = model.transcribe(x, language=a.lang, beam_size=5, word_timestamps=True, condition_on_previous_text=False, temperature=0)
    ws = [(w.word, w.start, w.end) for s in segs for w in s.words]
    return ws, ''.join(w for w, _, _ in ws).strip()

def main():
    doc = json.load(open(a.script)); aliases = doc.get('cer_aliases', {})
    lines = [l for l in doc['lines'] if not l.get('off')]
    os.makedirs(a.out_audio, exist_ok=True); os.makedirs(os.path.dirname(os.path.abspath(a.out_json)), exist_ok=True)
    model = None
    if not a.no_asr and any(os.path.exists(os.path.join(a.src, l['id'] + '.wav')) for l in lines):
        from faster_whisper import WhisperModel
        model = WhisperModel(a.whisper, device='cpu', compute_type=a.compute)
    def alias(t):
        for k, v in aliases.items(): t = t.replace(k, v)
        return ''.join(norm_chars(t))
    t = a.pre; out = []; FPS = a.fps
    for i, l in enumerate(lines):
        if i: t += l.get('gap_before', a.gap)
        src = os.path.join(a.src, l['id'] + '.wav'); rec = {'id': l['id'], 'text': l['text']}
        if os.path.exists(src):
            dst = os.path.join(a.out_audio, l['id'] + '.wav'); dur, g = process(src, dst)
            ws, hyp = asr_words(model, dst) if model else (None, '')
            cer = round(1 - difflib.SequenceMatcher(None, alias(l['text']), alias(hyp), autojunk=False).ratio(), 3) if hyp else None
            rel = os.path.relpath(dst, 'public') if os.path.abspath(dst).startswith(os.path.abspath('public')) else dst
            rec.update(file=rel, placeholder=False, gain_db=g, asr=hyp, cer_approx=cer)
        else:
            dur = l['syllables'] / a.syl_rate if l.get('syllables') else len(l['text'].split()) / (a.wpm / 60); ws = None
            rec.update(file=None, placeholder=True)
        ph = phrase_times(l['text'], dur, ws)
        f0 = round(t * FPS)
        rec.update(start=f0, end=round((t + dur) * FPS), dur_s=round(dur, 2),
                   words=[{'w': p, 's': f0 + round(s * FPS), 'e': f0 + round(e * FPS)} for p, s, e in ph])
        out.append(rec); t += dur
        print(f"{l['id']:12s} {'PH ' if rec['placeholder'] else 'WAV'} {t - dur:6.2f}-{t:6.2f}s  cer~{rec.get('cer_approx')}  {rec.get('asr', '')}")
    total = round((t + a.hold) * FPS)
    vo = {'fps': FPS, 'total': total, 'placeholder': any(r['placeholder'] for r in out), 'voice': a.voice_label, 'lines': out}
    json.dump(vo, open(a.out_json, 'w'), ensure_ascii=False, indent=1)
    print('total', total, 'frames =', round(total / FPS, 2), 's ->', a.out_json)

if __name__ == '__main__':
    main()
