---
name: mimo-tts-wav
description: >
  Generate a spoken or sung WAV audio file using MiMo TTS.
  USE THIS SKILL whenever the user asks the model to speak, say something aloud,
  read text out, sing a song, or produce any audio/voice output — even if no
  explicit destination is mentioned. Save the result to the current working
  directory as a .wav file (default name: output.wav) unless the user specifies
  a different path. Supports any expressive style and custom voice cloning.
applyTo: "**"
---

# MiMo TTS → WAV File

Convert text to speech using the MiMo TTS API and save the result as a
standard WAV file (24 kHz, 16-bit PCM, mono) to any local path you choose.

---

## When to Use

| Situation | Use this skill? |
|---|---|
| User says "说..." / "读出来" / "大声念" / "speak" / "say" | ✅ Yes |
| User says "唱..." / "唱个歌" / "唱歌" / "sing" | ✅ Yes |
| User asks for any voice/audio output | ✅ Yes |
| No output path given — save to `$PWD/output.wav` | ✅ Yes |
| Need to send voice directly to Feishu | ❌ Use `mimo-tts-voice` instead |
| Need to post-process audio (ffmpeg, SoX …) | ✅ Yes — pipe the output |

---

## Prerequisites

| Requirement | Details |
|---|---|
| `jq` | JSON builder. Install: `brew install jq` |
| `python3` | Standard library only (json, base64, struct). Pre-installed on macOS. |
| `curl` | Pre-installed on macOS. |

---

## Usage

```bash
bash scripts/tts_to_wav.sh "<text>" "<output.wav>" [style] [voice_sample.wav]
```

### Arguments

| # | Name | Required | Description |
|---|---|---|---|
| 1 | `text` | ✅ | Text to synthesize. Apply TTS normalization rules before passing. **Singing mode:** pass a song name (looked up in `sing0301_dict.json`) or `LYRICS:<your lyrics>` to supply lyrics directly. |
| 2 | `output_path` | ✅ | Destination path for the WAV file. Parent directory must exist. |
| 3 | `style` | optional | Any natural-language style phrase (see Style Guide below). Pass `唱歌` to enable singing mode. |
| 4 | `voice_sample` | optional | Path to a WAV reference clip (24 kHz, 16-bit, mono, 5–15 s) for voice cloning. Omit to use the preset voice `mimo_default`. |

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MIMO_VOICE_SAMPLE` | — | Fallback voice sample path (used when `voice_sample` arg is omitted) |
| `MIMO_API_BASE_URL` | `https://api.xiaomimimo.com/v1` | Override API base URL (`/chat/completions` is appended automatically) |
| `MIMO_TTS_MODEL` | `mimo-v2.5-tts` | Override model name |
| `MIMO_SING_DICT` | `../../sing0301_dict.json` (relative to script) | Path to `sing0301_dict.json` song lyrics dictionary |

---

## Step-by-Step

1. **Normalize the text** — Apply TTS normalization (see section below) so
   numbers, symbols and formatting render as natural speech.

2. **Choose a voice**
   - _Preset_: omit `voice_sample` → uses `mimo_default`
   - _Custom clone_: pass a 5–15 s WAV clip as the 4th argument, or set
     `MIMO_VOICE_SAMPLE`

3. **Choose a style** (optional) — pass any descriptive phrase as the 3rd
   argument. Omit for neutral speech.

4. **Run the script**:
   ```bash
   bash scripts/tts_to_wav.sh "要说的内容" "/path/to/out.wav"
   ```

5. **Check the output** — the script exits `0` and prints
   `OK: <N> bytes written to <path>` on success. Any error is printed to
   stderr with a non-zero exit code.

---

## Examples

```bash
# Minimal — preset voice, no style
bash scripts/tts_to_wav.sh "今天天气不错" /tmp/hello.wav

# With a mood style
bash scripts/tts_to_wav.sh "恭喜你获得了一等奖！" /tmp/congrats.wav "开心激动"

# Slow delivery for an accessibility recording
bash scripts/tts_to_wav.sh "请系好安全带。" /tmp/safety.wav "语速慢 清晰"

# Custom voice clone + style
bash scripts/tts_to_wav.sh "大家好，我是小明。" /tmp/xiaoming.wav "热情" ~/voices/xiaoming.wav

# Singing — look up lyrics by song name (requires sing0301_dict.json)
bash scripts/tts_to_wav.sh "两只老虎" /tmp/song.wav "唱歌"

# Singing — supply lyrics directly with LYRICS: prefix
bash scripts/tts_to_wav.sh "LYRICS:两只老虎，两只老虎，跑得快，跑得快……" /tmp/song.wav "唱歌"

# Pipe straight into ffmpeg to get MP3
bash scripts/tts_to_wav.sh "你好" /tmp/tmp.wav && \
  ffmpeg -i /tmp/tmp.wav /tmp/out.mp3
```

---

## Style Guide

`style` accepts **any natural-language phrase** — the model interprets it
freely. There are no fixed values.

| Category | Examples |
|---|---|
| Emotion | `开心` / `悲伤` / `生气` / `平静` |
| Delivery | `语速慢` / `语速快` / `悄悄话` / `清晰有力` |
| Character | `像个大将军` / `像个小孩` / `孙悟空` / `林黛玉` |
| Dialect | `东北话` / `四川话` / `台湾腔` / `粤语` |
| Combinations | `慵懒 刚睡醒` / `撒娇 夹子音` / `深情款款 语速慢` |
| Singing | `唱歌` — text is a song name (looked up in `sing0301_dict.json`) or `LYRICS:<lyrics>` |

Omit the style argument entirely for neutral, natural-sounding speech.

---

## TTS Text Normalization

Preprocess the input text before passing it to the script. Replace
unspoken symbols with natural spoken Chinese (or English where appropriate).

### Numbers
| Input | Spoken |
|---|---|
| `3` | 三 |
| `3.14` | 三点一四 |
| `1/3` | 三分之一 |
| `14:30` | 下午两点半 |
| `95%` | 百分之九十五 |
| `2024` (year) | 二零二四年 |

### Common Symbols
| Symbol | Spoken |
|---|---|
| `+` | 加 |
| `-` | 减 |
| `×` / `*` | 乘以 |
| `÷` / `/` | 除以 |
| `=` | 等于 |
| `>` / `<` | 大于 / 小于 |
| `%` | 百分之… |
| `~` | 大约 |
| `...` / `…` | 等等 |
| `#` | 井号 (or 第, by context) |

### Formatting Artifacts
- Remove markdown (`**bold**`, `# heading`, `` `code` ``, `- bullet`)
- Convert numbered lists to prose: "有三点，第一……第二……第三……"
- Convert tables to sentences describing key values

---

## Output Format

The script always writes a standard RIFF WAV file:

| Property | Value |
|---|---|
| Format | WAV (RIFF) |
| Sample rate | 24 000 Hz |
| Bit depth | 16-bit PCM |
| Channels | Mono |

If the API returns raw PCM instead of WAV, the script automatically adds
the correct RIFF header before writing to disk.

---

## Error Reference

| Exit code | Meaning | Fix |
|---|---|---|
| `1` | Missing required argument | Provide `text` and `output_path` |
| `1` | Voice sample file not found | Check the path passed as arg 4 |
| `2` | API HTTP error | Check network access; API key is resolved automatically |
| `2` | Unexpected response shape | Inspect stderr for raw API response |
| `3` | Output file empty / not written | Check that the parent directory exists and is writable |
