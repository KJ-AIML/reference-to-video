# reference-to-video

An agent skill for turning a **reference video or reel** into a new, **code-rendered brand video** for your own product, studio or service.

The agent works out how the reference works (structure, motion, type, voice, sound, pacing), then rebuilds those techniques in [Remotion](https://www.remotion.dev/). It uses your real brand tokens, site copy and UI captures. Copy the technique, never the content.

It covers the whole job:
- site review and brand extraction
- a script with a claim-source table
- TTS voice, including Thai and other non-English voices
- word-synced captions
- re-composed 16:9 and 9:16 cuts
- an original synthesized music bed
- a −14 LUFS master with a colour-range check
- verification and handoff

It works with any agent that reads `SKILL.md` skills (Claude Code, Codex, Cursor and others).

Sibling skill: **[KJ-AIML/product-launch-film](https://github.com/KJ-AIML/product-launch-film)**. It covers product truth, anti-slop visuals, UI fidelity and a Remotion starter. This skill adds the reference analysis, reel formats, captions and the voice pipeline. Use both together.

## Workflow and checkpoints

Rendering and TTS usage are expensive, so the agent stops for approval at each ⏸:

| Step | Output |
|---|---|
| 0. Site review | `REVIEW.md` (Lighthouse, links, copy honesty) + `BRAND.md` (exact tokens, fonts, real vs concept work) ⏸ |
| 1. Decisions | every fact that changes the brief, asked as a choice: concept labels, reach claims, prices, format, voice ⏸ |
| R1–R2. Reference analysis | spec, cuts, transcript, wpm, shot table, techniques, recreation plan (runs alongside step 0) |
| 2. Script + storyboard + claims | `script.json`, storyboard per aspect, claim → source table ⏸ |
| 6. Voice | engine/voice choice by licence and clarity (band table + A/B clip), batched TTS, ASR check |
| 7. Timeline | `vo.json` as the only clock: line placement plus word times for captions |
| 7b. Placeholder clock | if the voice is blocked (quota, unpicked voice), build all visuals against estimated timings |
| 8. Remotion build | two compositions (1920×1080@60 and 1080×1920@60), genuinely re-composed |
| 9. Stills → one fix pass → render → master | −14 LUFS, TP ≤ −1.5 dBTP, tv/bt709 with range detection, covers |
| 9b. PREVIEW | quick render with placeholder voice + music bed, so the user can react early |
| 10. Verify | ffprobe, loudness, contact sheets, caption sync, brand pixel check, claims |
| 11. Handoff | absolute paths, git bundle (no push), checksums on both ends, cleanup report |

## Use it with an AI agent

Install the skill so that `SKILL.md` sits at `<skills-dir>/reference-to-video/SKILL.md`:

```bash
git clone https://github.com/KJ-AIML/reference-to-video.git ~/src/reference-to-video

# Claude Code (user level)
mkdir -p ~/.claude/skills && ln -s ~/src/reference-to-video ~/.claude/skills/reference-to-video

# Other Agent Skills tools: link or copy the folder into that tool's skills directory
```

Then ask, for example:

> Use the reference-to-video skill. Reference: <REF_URL>. Our site: <SITE_URL> (repo at <SITE_REPO>).
> Make a 45–60 s film in 16:9 and 9:16 with a warm female narrator. Stop at each checkpoint.

The agent should hand back `REVIEW.md` / `BRAND.md` first and wait for you. Nothing gets voiced or fully rendered before you approve the script.

## Helper scripts (`scripts/`)

These are generic. Run them from the Remotion project root; all paths are relative.

| Script | What it does |
|---|---|
| `gemini_tts.py` | Batched Gemini TTS: several lines per request with one `speech_metadata.style`, split at pauses. The key comes from an env var and is never printed. The split is heuristic, so listen to each part. |
| `build_vo.py` | Per-line takes → trimmed, 48 kHz, −19 LUFS WAVs + `src/vo.json` with word (phrase) times from faster-whisper. Lines without audio get placeholder timing (`--syl-rate`, `--wpm`). |
| `make_bed.py` | Original music bed synthesized with numpy/scipy (FM electric piano, plucked arpeggio, bass, soft kick, shaker, reverb). Its length comes from `vo.json`. |
| `master.sh` | Multi-pass −14 LUFS master (static gain + limiter) and ONE video re-encode to tagged tv/bt709. It detects the input range, so limited-range raws aren't squeezed twice. |
| `verify.sh` | Frame count, colour tags, loudness, a contact sheet and a background-pixel check on a final file. |

Requirements: Node + Remotion for the film; Python 3 with `numpy scipy soundfile librosa faster-whisper` for the scripts; `ffmpeg`.

TTS model names, voices and free-tier limits change. Check the provider's current docs and terms, and record the voice, licence and music method in your `CREDITS.md`.

## License

[MIT](LICENSE)
