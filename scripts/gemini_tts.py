#!/usr/bin/env python3
"""Batched Gemini TTS for a script.json ({"lines":[{"id","text",...}]}).

Why batched: free tiers allow only a handful of requests per day (about 10). One request carries several text items
(one per line, all with the same speech_metadata.style), and the returned WAV is split at the N-1 longest pauses.
The split is heuristic. Listen to each part, and fall back to --ids <one id> (one request per line) if it fails.

  python scripts/gemini_tts.py --ids 01-hook,02-pain,03-reveal --voice <PrebuiltVoice> --style "warm, friendly, natural"
  python scripts/gemini_tts.py --ids 05-cta --suffix .take2 ...     # single retake

Put the delivery style in --style (sent as speech_metadata.style). A style written inside the text gets read aloud.
Key: read from the env var named by --key-env (default GEMINI_API_KEY), sent as a header, never printed.
Output: 24 kHz mono WAV per line in --out (default scripts/vo/src). Raw responses go in --out/../raw.
Deps: numpy soundfile librosa.
The model name and endpoint may change; check the current Gemini API docs.
"""
import argparse, base64, json, os, sys, urllib.error, urllib.request
import soundfile as sf, librosa

ap = argparse.ArgumentParser()
ap.add_argument('--script', default='script.json')
ap.add_argument('--ids', required=True, help='comma-separated line ids, in spoken order')
ap.add_argument('--voice', required=True, help='prebuilt voice name')
ap.add_argument('--style', required=True, help='one short delivery style for every line in the batch')
ap.add_argument('--model', default='gemini-3.8-flash-tts')
ap.add_argument('--endpoint', default='https://generativelanguage.googleapis.com/v1beta/interactions')
ap.add_argument('--key-env', default='GEMINI_API_KEY')
ap.add_argument('--out', default='scripts/vo/src')
ap.add_argument('--suffix', default='', help='e.g. .take2 for a retake')
ap.add_argument('--field', default='text', help="script field to speak: 'text' or 'say' (respelling)")
a = ap.parse_args()

def call(items):
    key = os.environ.get(a.key_env)
    if not key: sys.exit(f'{a.key_env} not set')
    body = {'model': a.model, 'input': [{'type': 'user_input', 'content': [
              {'type': 'text', 'text': t, 'annotations': [{'type': 'speech_metadata', 'style': a.style}]} for t in items]}],
            'response_format': {'type': 'audio'}, 'generation_config': {'speech_config': [{'voice': a.voice}]}}
    req = urllib.request.Request(a.endpoint, data=json.dumps(body).encode(),
                                 headers={'x-goog-api-key': key, 'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=300) as r: res = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f'HTTP {e.code}: ' + e.read().decode()[:1200].replace(key, '<KEY>'))
    aud = [c for s in res.get('steps', []) for c in s.get('content', []) if c.get('type') == 'audio']
    if not aud: sys.exit('no audio in response: ' + json.dumps(res)[:600])
    print('usage:', json.dumps(res.get('usage', {}))[:200])
    return base64.b64decode(aud[-1]['data'])

def split(path, n):
    x, sr = sf.read(path)
    if n == 1: return [x]
    hop = 240; rms = librosa.feature.rms(y=x, frame_length=1024, hop_length=hop)[0]; thr = max(rms.max() * 0.02, 1e-4)
    quiet = rms < thr; gaps = []; i = 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            gaps.append((j - i, (i + j) // 2 * hop)); i = j
        else: i += 1
    inner = [g for g in gaps if 0 < g[1] < len(x) - sr * 0.2]
    cuts = sorted(c for _, c in sorted(inner, reverse=True)[:n - 1])
    if len(cuts) != n - 1: sys.exit(f'could not find {n - 1} pauses; split by hand or request lines one by one')
    edges = [0] + cuts + [len(x)]
    return [x[p:q] for p, q in zip(edges, edges[1:])]

def main():
    lines = {l['id']: l for l in json.load(open(a.script))['lines']}
    ids = [i.strip() for i in a.ids.split(',') if i.strip()]
    missing = [i for i in ids if i not in lines]
    if missing: sys.exit(f'unknown ids: {missing}')
    raw_dir = os.path.join(os.path.dirname(os.path.abspath(a.out)), 'raw')
    os.makedirs(a.out, exist_ok=True); os.makedirs(raw_dir, exist_ok=True)
    raw = os.path.join(raw_dir, '+'.join(ids)[:80] + a.suffix + '.wav')
    open(raw, 'wb').write(call([lines[i].get(a.field) or lines[i]['text'] for i in ids]))
    x, sr = sf.read(raw); print('raw', raw, sr, 'Hz', round(len(x) / sr, 2), 's')
    for i, seg in zip(ids, split(raw, len(ids))):
        out = os.path.join(a.out, i + a.suffix + '.wav'); sf.write(out, seg, sr); print(' ', i, round(len(seg) / sr, 2), 's ->', out)
    print('next: listen, then build_vo.py (prints ASR + approximate CER per line)')

if __name__ == '__main__':
    main()
