---
name: reference-to-video
description: >-
  Use when the user gives a reference video/reel and wants a new video for their
  own product, studio or service company in that style, built as code (Remotion)
  from their real brand, site and UI. Covers the site review, brand extraction,
  script approval, voice (TTS, incl. Thai/non-English), word-synced captions,
  16:9 + 9:16 cuts, placeholder-timed previews with an original music bed,
  mastering, verification and handoff.
---
# Reference → brand video (code-rendered)

Goal: work out HOW a reference clip works (structure, motion, type, voice, sound, pacing). Then rebuild those techniques for the user's product in Remotion, using the product's real brand, copy and components. Copy technique, never content.

This complements `product-launch-film` (product truth, anti-slop visuals, UI fidelity). This skill adds the site review, reference analysis, reel formats, word-synced captions and the voice pipeline.

Placeholders: `<SITE_URL>`, `<SITE_REPO>` (brand source, pinned commit), `<REF_URL>`, `<WORK>` (analysis dir), `<VIDEO_REPO>` (Remotion), `<COMP_169>`/`<COMP_916>`, `<OUT>`, `<USER_DEST>` (absolute path on the user's machine).

## Workflow order and checkpoints (usage is expensive: stop at each ⏸)
0. **Site review** (if the product has a website) → deliver `REVIEW.md` + `BRAND.md`. ⏸
1. **Decisions**: surface every fact that changes the brief as an explicit question. ⏸
2. **Script + storyboard + claim-source table** for approval BEFORE any voice or render work. ⏸
3. **Build**: voice → timeline → stills review → ONE fix pass → render → verify → handoff.
   - If the voice is blocked (TTS quota, an unpicked voice), don't wait. Build every visual against a placeholder `vo.json` (Phase 7b) and ship a **PREVIEW** (Phase 9b). When the real voice arrives, only the audio and word times get swapped.

**Sharing audio in chat:** chat won't take audio attachments. Wrap each sample as an mp4 on a still image and set the length with `-t`, not `-shortest`:
`ffmpeg -loop 1 -i card.png -i a.wav -t <dur> -c:v libx264 -tune stillimage -r 10 -pix_fmt yuv420p -c:a aac -b:a 256k -movflags +faststart a.mp4`

Reference analysis (phases R1–R2) can run in parallel with step 0. Never generate a voice or run a full render on an unapproved script.

## Step 0: Review the site first
1. Pin the source: `git -C <SITE_REPO> rev-parse HEAD`. Build or export it if needed so you can cite `file:line`.
2. Lighthouse (mobile + desktop): `npx lighthouse <SITE_URL> --output=json --output=html --output-path=<WORK>/lh-mobile --chrome-flags="--headless=new"` (add `--preset=desktop` for the desktop run). Record Perf/A11y/BP/SEO and the top 3 fixes.
3. Links: `npx linkinator <SITE_URL> --recurse --skip "mailto:|tel:"` (or `lychee`). Also check meta/OG tags, favicon, 404 page and the contact path.
4. Copy honesty: list every claim (client work, numbers, locations such as "worldwide", prices, testimonials, partners). Mark each one *supported / concept / unsupported*. Flag concept work that reads like shipped client work.
5. `BRAND.md` from the source, not from screenshots:
   - exact hex values (paper, ink, accent, full-bleed band colour, functional colours)
   - font families, weights and files plus their licences
   - radius/corner style, grid
   - logo/mark files (SVG paths)
   - section list with real headings
   - taglines verbatim
   - the services list
   - real vs concept work, each with `file:line`
6. Deliver `REVIEW.md` (scores, broken links, honesty flags, quick fixes) and `BRAND.md`. ⏸

## Step 1: Decisions that change the brief
Ask, don't assume. Present each one as a choice with a recommendation:
- **No shipped work:** if there's only concept work, the example must be labelled **CONCEPT** on screen. Is a hidden or draft concept off-limits?
- **Location/reach claims:** "Bangkok-based" vs "worldwide".
- **Prices:** none unless explicitly approved. "Free call" / "fixed price" are allowed only if the site says them.
- **Other products/brands:** feature them or leave them out.
- **Format:** aspect ratios, target length, platform (IG/TikTok/YouTube/LinkedIn), voice gender/accent/language.
- **Service/SaaS demos with sample data:** prices get blurred in every capture, and every UI shot carries a small "Demo · sample data" label (in the video's language). Confirm both.

## Phase R1: Measure the reference
1. `yt-dlp -o <WORK>/ref.mp4 --write-info-json --write-thumbnail <REF_URL>`. If it needs a login, ask; never lift browser cookies.
2. Spec: `ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate -show_entries format=duration -of compact ref.mp4`. Loudness: `ffmpeg -nostats -i ref.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12`.
3. Audio: `-vn -ac 1 -ar 16000 audio16k.wav`. Spectrum: `-lavfi showspectrumpic=s=1920x800` shows where the music bed starts and where the SFX hits land.
4. Cuts: `-vf "select='gt(scene,0.3)',metadata=print:file=scenes.txt" -vsync vfr`. Few cuts usually means the changes happen inside one screen.
5. Frames: `fps=2,scale=270:-1,tile=8x6` contact sheets, plus full-res key frames at interesting times.
6. Transcribe with faster-whisper large-v3-turbo (CPU int8, `word_timestamps=True`). Read every segment: text over music tails or silence is a hallucination. Measure wpm over the speech span, the gaps between lines, and line length.

## Phase R2: Decode (`<WORK>/REPORT.md`, no building yet)
- **Spec table:** length, resolution, fps, LUFS, LRA, cuts.
- **What it actually is**, each point with evidence and a confidence level: screen recording vs code graphics vs AI video; AI vs human voice.
- **Shot table:** time | on screen | type | motion | voice line | music/SFX.
- **Techniques:** palette, type, caption behaviour, motion vocabulary (draw-on, typewriter, pops, slams, stamps, counters, morphs), pattern breaks, hook/retention, loop ending.
- **Recreation plan** with a component list.

## Brand-site style rules
- **Rhythm beats:** use the site's own full-bleed colour (e.g. its brand blue band) instead of defaulting to near-black. Agree the exact count (e.g. 2 beats).
- **Signature moment:** take it from the site (e.g. the logo mark assembling from the name's letters, or the hero animation), and land it on the reveal.
- **Rebuild real components:** the site's contact card, "how we start" band, service tiles, process strip and section eyebrows, with real copy, corner style (square, notched) and tokens. Don't invent generic cards.
- **Accent colour:** keep it sparing, as a signal only (markers, one keyword). Mostly light, no glow, few pills, no invented numbers.

## Step 2: Script, storyboard, claim sources (⏸ approval)
Beats for products: hook question → objection ("And no, this isn't …") → reveal (name + tagline) → concrete example → "this is where it gets crazy" → how it works → old vs new → control loop → honest concession → payoff → CTA/title that loops.

For **service/agency companies**:
- concrete example = a site concept labelled **CONCEPT**
- how it works = the site's process stages (verbatim names)
- how we start = only what the site says (free call / scope / fixed price, no amounts)
- concession = an honest one about AI ("Will AI run your business? Honestly, no. A person on your team makes the final call.")
- payoff = the site's tagline
- CTA = the URL spoken and typed

Rules:
- 120–145 words for 45–60 s. Aim for ~145 wpm; ~160 felt rushed.
- **Non-English pace:** Thai TTS runs at about **3.5 syllables/s**, slower than a 4.3 syl/s plan. A 61 s estimate became ~75 s. Count syllables for languages without word spaces, then re-estimate once you have a real sample. **Confirm the new length with the user** rather than speeding the voice up.
- Store the script as JSON: `{"lines":[{"id":"01-hook","style":"…","text":"…","say":"optional TTS respelling"}]}`.
- Storyboard: one row per line covering visual, layout per aspect, motion, SFX, and caption on/off.
- **Claim table:** claim | exact site line (verbatim) | `file:line`. Drop or reword anything without a source. Watch absolute words ("every", "never") and unnamed integrations. No claims beyond the site.

## Phase 6: Voice
0. **Thai/non-English voices.** Test the language before committing to an engine. Findings:
   - **Fine-tuned LoRA voices** (e.g. the SiangTTS LoRA on VoxCPM2) can come out narrow-band, like a speakerphone (3–5 kHz down 9–13 dB vs real speech). The cause is the LoRA and its reference voice.
   - **Base VoxCPM2** is clearer, but it encodes at 16 kHz internally, so the top end stays dull.
   - **Gemini TTS gave the clearest Thai.**
     - Access: an AI Studio key works with the Gemini API (`v1beta`). Cloud Text-to-Speech is a separate API that must be enabled on its own project, or it returns 403 SERVICE_DISABLED.
     - Model `gemini-3.8-flash-tts`, prebuilt voices, 24 kHz mono output.
     - Put the delivery style in `speech_metadata.style`. **A style written inside the text gets read aloud.**
     - The free tier allows about **10 requests/day** (it resets daily).
   - **Budget the requests:** pick the voice from 3–4 short samples, then **batch the lines** into 1–2 requests (one text item per line, same style) and split them at the long silences. Keep a per-line retake mode and leave quota for 1–2 retakes.
   - Keep the API key in an env var and only ever test it with `test -n "$KEY" && echo set`. Never print it.
   - **Compare candidates objectively.** For each voice, build a band-energy table (e.g. 0–300 Hz, 300–1k, 1–3k, 3–5k, 5–8k, 8–12k; Welch PSD on voiced frames, dB relative to the 300–1k band) next to a real-speech reference in the same language. Also make one **A/B clip**: the same sentence from each voice, separated by a short gap, wrapped as an mp4. Let the user pick by ear, and use the table to explain why.
1. Choose TTS by licence first, then expressiveness. Options tested: VoxCPM2 (Apache-2.0); the SiangTTS LoRA on VoxCPM2 (CC-BY-SA-4.0, attribution); Kokoro-82M (Apache-2.0); Gemini TTS (API terms). Run `df -h` before downloading weights (several GB).
2. Narrator: ONE synthetic designed voice (`"(warm, confident male narrator)" + neutral sentence`, 2 tries, keep the best). Save it as `ref-voice.wav`.
   - **Reuse a proven ref voice across one brand's films.** A new design can come out too high or too thin.
   - It's synthetic, so there's no clone-consent issue. Say so in CREDITS.
3. Per line: `generate(text=f"({style}){say or text}", reference_wav_path=ref, cfg_value=2.5, inference_timesteps=10)`. **Max 2 takes.** Skip take 2 when take 1 is clean (WER 0, voiced > 0.45, range > 9 st, f0 within ±20 % of the ref median).
4. Scoring:
   - **Whisper:** base.en WER against `text` (large-v3-turbo CER for Thai). Normalise brand respellings, "dot com" and number words.
   - **Pitch:** `librosa.pyin(x, fmin=60, fmax=400, sr=16000)` gives median f0, range (p95 − p5 in semitones) and voiced fraction.
   - **Pick order:** WER → not whispered (voiced ≥ 0.3) → f0 in the narrator band → wider range.
5. **Respell for TTS only.** `say` gets the phonetic form ("Ah-kmee Labs", "Production-ize", "S-S-H-ing", "brand dot com"). Captions and on-screen text keep the real spelling. Whisper-check every brand name, the URL, acronyms (API) and coined verbs.
6. **Outlier take** (f0 far off and take 2 unusable): pitch-correct sparingly with `ffmpeg -af "rubberband=pitch=0.72:formant=preserved:pitchq=quality"`. Keep the shift ≤ ~6 st and re-run Whisper, because a bigger shift can change words. Note the correction in CREDITS.
7. Delete weights, LoRA and HF caches after generation. Keep the scripts and the picked WAVs.

## Phase 7: Timeline + captions (`vo.json` is the only clock)
1. Per line: trim silence, level to ≈ −19 LUFS, resample to 48 kHz, place with 0.35–0.5 s gaps (longer after the reveal, slam and process beats, and before the CTA).
2. Get word times with faster-whisper small.en. Map words onto the script `text` (not `say`) with `difflib.SequenceMatcher`, and interpolate the unmatched ones.
3. `vo.json`: fps, total, and per line id/file/start/end/words[{w,s,e}] in absolute frames. Scenes use `S(id)`/`E(id)`/`W(id,word)`, never hard-coded seconds.
4. Captions:

   | Aspect | Chunk size | Font size |
   |---|---|---|
   | 9:16 | ≤ 4 words / 20 chars | ≥ 70 px |
   | 16:9 | ≤ 6 words / 30 chars | ≈ 64 px |

   - Break chunks at punctuation and merge a trailing one-word chunk into the previous one.
   - Each word pops in ~2 frames early. A per-line keyword map gets the fill.
   - **Turn captions off** wherever the visual is the words: reveal, slams, end title, and any headline that already fills word by word with the VO. A duplicate caption overlaps it and reads twice.

## Phase 7b: Placeholder clock (while the voice is blocked)
- Build `vo.json` with the same schema from estimated timings: syllables ÷ measured syl/s (or words ÷ wpm), plus the usual gaps.
  - Use any approved sample WAVs as real lines and timing references.
  - Give placeholder words evenly spaced times within each line so captions still fill.
  - Set `placeholder: true` at the top level.
- The timeline script should take real audio for whichever lines exist and estimate the rest. Swapping in the real voice is then just: drop in the WAVs, re-run, re-render.
- While `placeholder` is true, show a small on-screen tag (e.g. "PREVIEW · partial audio").

## Phase 8: Remotion build
- **Dual aspect:** ONE audio mix and ONE `vo.json`; two compositions (`<COMP_169>` 1920×1080@60, `<COMP_916>` 1080×1920@60) get a layout object `L` as props. **Genuinely re-compose** for each aspect, don't crop:

  | Aspect | Layout | Safe area | Captions |
  |---|---|---|---|
  | 16:9 | horizontal paths, side-by-side windows, 4-col tiles | x 96–1824, y 64–1016 | y ≈ 930 |
  | 9:16 | vertical timelines, stacked windows, 2-col tiles | x 72–980, y 250–1560 (keep clear of IG/TikTok UI) | y ≈ 1300–1330 |

- **Fonts:** load the site's own font files via `FontFace` + `delayRender`, and set `fontFamily` on the root. Reused parts otherwise fall back to serif.
- **Helpers:**
  - `p01(f,a,d)`: clamped ease-out with bezier (0.16,1,0.3,1)
  - `pop`: spring with damping 12, stiffness 220, mass 0.6
  - `Draw`: `pathLength=1` with dashoffset
  - `Marker`: wavy strike
  - `Stamp`: 2.4→1, −9°, multiply
  - `Letters`: per-letter stagger. Put spaces inside the string as NBSP; a JSX space between components collapses.
  - `FillWord`: clipPath driven over the word's s→e
  - counters
- **Mock windows:** fill them with real site copy, not grey placeholder bars.
- **Text sizes:** mono labels ≥ 24 px on phone; no grey-on-grey 1 px detail.
- **Particle/letter assemblies:** keep particles legible (fewer, bigger glyphs) and land a solid mark quickly. Mid-assembly frames must not read as noise.
- **Loop:** the last 1–2 s return to the exact opening frame.
- **Sound:** a music bed at ~0.3, ducked to ~0.08 around each line. SFX on draws, stamps and slams. Original/synthesized or properly licensed audio only, with the source recorded.
  - **Original synthesized bed** (a seeded numpy/scipy script in the repo):
    - Warm major key at 85–100 BPM, light and not dark, no EDM.
    - Instruments: FM "Rhodes-style" chords with a decaying mod index; an additive-harmonic plucked arpeggio with light swing; sine bass; a sine-sweep kick; a high-passed-noise shaker.
    - Mix: a convolution reverb from a synthetic decaying-noise IR, a 1 s fade-in, a 2–3 s fade-out, peak −6 dBFS.
    - Read the length from `vo.json` total, so a change in the VO only means re-running the script.
    - Record the method in CREDITS.
  - Duck from `vo.json`: `volume={(f) => …}` on the bed's `<Audio>`, ramping over ~10 frames around each line that has audio.
- **Demo captures:** pin the clock, blur prices, blur `document.activeElement` before each shot (no focus rings), and wait out toasts. Label sample data on every UI shot. In 9:16, use the product's real mobile view instead of a cropped desktop.

## Phase 9: Stills → fix pass → render → encode → master
1. **Stills before the full render:** bundle once, then `renderStill` both comps at the end of each line −4 frames, plus the reveal, the mid-assembly and the last frame, at scale 0.5. Tile and look at them. Do **one** fix pass, then re-check only the fixed frames.
2. **Render:** `npx remotion render <COMP> out/<name>.raw.mp4 --codec=h264 --crf=18 --pixel-format=yuv420p --image-format=jpeg --jpeg-quality=95 --audio-codec=aac --audio-bitrate=320k`
3. **Master to −14 LUFS:**
   - Apply a static gain, then a look-ahead limiter (ceiling ≈ −2.3 dB sample peak → TP ≤ −1.5 dBTP), and re-measure.
   - The limiter eats about 1–1.5 LU on dynamic VO. Re-measure after limiting and apply the shortfall again (up to ~4 passes, stop within ±0.3 LU).
   - Mux with `-c:v copy` and WITHOUT `-shortest`.
   - **Don't over-limit.** If the limiter works through most of the mix or LRA ≈ 2, the mix is too dense. Lower the bed/SFX peaks before mastering and aim for LRA 4–7.
4. **Colour range: detect the input range first.**
   - JPEG frames give full-range `yuvj420p`/`pc`.
   - PNG frames (`--image-format=png`) give **limited-range** `yuv420p` with no tag.
   - Squeezing an already-limited raw again ("double squeeze") turns a cream background grey (e.g. #FBF8F3 → #E8E3E0).

   Detect the range: `ffprobe -select_streams v:0 -show_entries stream=pix_fmt,color_range -of csv=p=0 in.mp4`. If it's `yuvj*` or `pc`, use `INR=pc`; otherwise use `INR=tv`. Then re-encode once:
   `ffmpeg -i in.mp4 -map 0 -vf "scale=in_range=$INR:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709:flags=accurate_rnd+full_chroma_int+bitexact,format=yuv420p" -c:v libx264 -preset slow -crf 16 -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a copy -movflags +faststart <OUT>/<name>.mp4`
   - Then sample a full-bleed brand pixel (`-ss <t> -frames:v 1 px.png`, PIL `getpixel`). It should be within about ±4 of the brand hex.
   - **Check the first real render**, not just a short smoke test made with different settings.
5. **Covers per aspect:** render the strongest brand frame (e.g. the full-bleed reveal with the mark formed) at scale 1 to `cover-16x9.jpg` / `cover-9x16.jpg`.

## Phase 9b: PREVIEW delivery (placeholder voice)
- Render both comps quickly (`--crf 18 --x264-preset veryfast`, raw), then master them (−14 LUFS, colour fix at `CRF=20`, preset medium).
- Also export the music bed alone as an mp4 (still image + audio, `-t`) for the user to judge.
- Run the Phase 10 checks on the preview too; the bg-pixel check catches range bugs.
- Keep the bed in the repo for the final.

## Phase 10: Verify (each aspect)
- [ ] `ffprobe -count_frames …`: size, 60/1, `yuv420p` + `color_range=tv`, frame count = composition, AAC 48 kHz.
- [ ] `ebur128`: I ≈ −14 LUFS, TP ≤ −1.5 dBTP, LRA not crushed.
- [ ] 12–14 frames from the FINAL file → a contact sheet per aspect (`scale=480:270` or `360:640`, `tile=7x2`). Look at both.
- [ ] Safe areas respected; nothing overlaps, including mid-animation and after stamps land.
- [ ] Captions ≥ 70 px (9:16); labels ≥ 24 px; no single-word chunks.
- [ ] Caption sync: for each sampled t, the last `vo.json` words with `s ≤ t·fps` match the frame.
- [ ] Brand fonts only (no serif fallback); brand colours only, hex verified by pixel sample.
- [ ] Full-bleed beat count matches what was agreed; CONCEPT label visible; no prices or unapproved claims; every claim is in the claim table.
- [ ] Demo films: prices blurred in every capture; the sample-data label is on every UI shot; no PLACEHOLDER/PREVIEW tag left in the final.
- [ ] The brand name, URL and acronyms are heard correctly (Whisper on the final mix).
- [ ] wpm measured (≤ ~150), or syl/s for Thai.
- [ ] CREDITS covers TTS model + licence + attribution, narrator (synthetic, reused?), corrections, music/SFX source, font licences, Remotion licence.

## Phase 11: Handoff hygiene
- Copy to `<USER_DEST>` with **absolute paths** (a literal `~` can create a `~/` folder). Split large files into chunks if the transfer tool has a size limit, and retry one file at a time if the machine is flaky.
- Ship the repo as a git bundle, then on the user's machine: clone it, `git remote remove origin`, **no push**. Deliverables go in `out/` (gitignored).
- Verify both ends: `ls -la` + `shasum -a 256` must match.
- Clean up: delete weights, LoRAs and HF caches. The HF hub may use a shared `blobs/` store, so deleting one model dir frees nothing. Keep the scripts, `script.json`, the picked WAVs and the logs.
- Report: spec, loudness, file list with paths, respellings, corrections, weak spots, and leftovers (temp files you couldn't or didn't delete, envs still on disk).

## Pitfalls
- Whisper hallucinates on music tails and silence; never trust the last segment blindly.
- One designed ref voice for all lines; mild style notes; check voicing and pitch, not just WER.
- A take can jump an octave-ish (f0 ≫ narrator band) and still pass WER. Gate the "first take is clean" shortcut on f0 too.
- A headline that fills with the VO plus a caption of the same words = duplicate text and overlaps on 9:16.
- Strikes and stamps timed to the line end land after the cut. Time them to a word inside the line.
- An empty first frame (from the loop) makes a weak thumbnail, so always ship covers.
- IG re-encodes everything: flat graphics are fine, fine 1 px detail is not.
- A LoRA/fine-tuned TTS voice can sound like a phone call even when WER is perfect. Look at the band table, not just ASR.
- A TTS style or prompt placed inside the spoken text gets read aloud. Use the API's style field.
- Free TTS tiers run out mid-project. Count requests before sampling, and batch lines.
- Colour "fixes" can double-squeeze: detect the raw range before converting, and pixel-check the real render.
