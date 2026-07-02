#!/usr/bin/env bash
# tts_to_wav.sh — Generate a WAV file from text using MiMo TTS API
#
# Usage:
#   tts_to_wav.sh <text> <output_path> [style] [voice_sample]
#
# Arguments:
#   text          Text to synthesize (required).
#                 Singing mode: pass a song name to look up lyrics automatically,
#                 or pass "LYRICS:<lyrics>" to provide lyrics directly.
#   output_path   Destination WAV file path (required)
#   style         Speaking style (optional). Any natural language phrase, e.g.
#                 开心 / 悲伤 / 慵懒 / 语速慢 / 东北话 / 像个大将军
#                 Use "唱歌" to enable singing mode.
#   voice_sample  Path to a WAV voice clone sample (optional).
#                 If omitted, uses the preset voice mimo_default.
#
# Environment variables:
#   MIMO_API_KEY      (required) MiMo platform API key
#   MIMO_API_BASE_URL (optional) Override API base URL (e.g. https://api.xiaomimimo.com/v1)
#   MIMO_TTS_MODEL    (optional) Override model name
#   MIMO_SING_DICT    (optional) Path to sing0301_dict.json (song lyrics dictionary)
#
# Exit codes:
#   0  Success — WAV written to output_path
#   1  Missing required argument or environment variable
#   2  API request failed or returned an error
#   3  Output file could not be written

set -euo pipefail

# ── Arguments ──────────────────────────────────────────────────────────────
TEXT="${1:-}"
OUTPUT_PATH="${2:-}"
STYLE="${3:-}"
VOICE_SAMPLE="${4:-${MIMO_VOICE_SAMPLE:-}}"

# ── Validation ─────────────────────────────────────────────────────────────
if [[ -z "$TEXT" ]]; then
  echo "Error: <text> is required" >&2
  echo "Usage: $(basename "$0") <text> <output_path> [style] [voice_sample]" >&2
  exit 1
fi

if [[ -z "$OUTPUT_PATH" ]]; then
  echo "Error: <output_path> is required" >&2
  echo "Usage: $(basename "$0") <text> <output_path> [style] [voice_sample]" >&2
  exit 1
fi

# Resolve API key: env var → openclaw.json → error
if [[ -z "${MIMO_API_KEY:-}" ]]; then
  _OPENCLAW="$HOME/.openclaw/openclaw.json"
  if [[ -f "$_OPENCLAW" ]]; then
    MIMO_API_KEY=$(python3 -c "
import json, sys
try:
    d = json.load(open('$_OPENCLAW'))
    print(d['models']['providers']['xiaomi']['apiKey'])
except (KeyError, TypeError):
    sys.exit(1)
" 2>/dev/null) || true
  fi
fi
if [[ -z "${MIMO_API_KEY:-}" ]]; then
  echo "Error: MiMo API key not found." >&2
  echo "  Set MIMO_API_KEY env var, or add models.providers.xiaomi.apiKey to ~/.openclaw/openclaw.json" >&2
  exit 1
fi

TTS_ENDPOINT="${MIMO_API_BASE_URL:-https://api.xiaomimimo.com/v1}"
TTS_ENDPOINT="${TTS_ENDPOINT%/}/chat/completions"
MODEL="${MIMO_TTS_MODEL:-mimo-v2.5-tts}"
SING_DICT="${MIMO_SING_DICT:-$(dirname "$0")/../sing0301_dict.json}"

WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

# ── Singing mode — resolve song name → lyrics ───────────────────────────────
if [[ "$STYLE" == "唱歌" ]]; then
  if [[ "$TEXT" == LYRICS:* ]]; then
    # Direct lyrics supplied with LYRICS: prefix
    TEXT="${TEXT#LYRICS:}"
  else
    # Look up song name in dictionary
    if [[ ! -f "$SING_DICT" ]]; then
      echo "Error: song dictionary not found: $SING_DICT" >&2
      echo "Set MIMO_SING_DICT to point to sing0301_dict.json, or prefix lyrics with LYRICS:" >&2
      exit 1
    fi
    LOOKUP_RESULT=$(python3 -c "
import json, sys
d = json.load(open('$SING_DICT'))
key = sys.argv[1]
if key in d:
    print(d[key]); sys.exit(0)
for k in d:
    if key in k or k in key:
        print(d[k]); sys.exit(0)
sys.exit(1)
" "$TEXT" 2>/dev/null) || true
    if [[ -z "$LOOKUP_RESULT" ]]; then
      echo "Error: song '${TEXT}' not found in dictionary" >&2
      echo "Pass lyrics directly with prefix: LYRICS:<your lyrics>" >&2
      exit 1
    fi
    TEXT="$LOOKUP_RESULT"
  fi
fi

# ── Build assistant content ─────────────────────────────────────────────────
if [[ -n "$STYLE" ]]; then
  CONTENT="<style>${STYLE}</style>${TEXT}"
else
  CONTENT="${TEXT}"
fi

# ── Build request payload ───────────────────────────────────────────────────
if [[ -n "$VOICE_SAMPLE" ]]; then
  if [[ ! -f "$VOICE_SAMPLE" ]]; then
    echo "Error: voice_sample file not found: $VOICE_SAMPLE" >&2
    exit 1
  fi
  AUDIO_B64=$(base64 -i "$VOICE_SAMPLE")
  PAYLOAD=$(jq -n \
    --arg model "$MODEL" \
    --arg data "$AUDIO_B64" \
    --arg content "$CONTENT" \
    '{model: $model,
      audio: {format: "wav", voice_audio: {format: "wav", data: $data}},
      messages: [{role: "assistant", content: $content}]}')
else
  PAYLOAD=$(jq -n \
    --arg model "$MODEL" \
    --arg content "$CONTENT" \
    '{model: $model,
      audio: {format: "wav", voice: "mimo_default"},
      messages: [{role: "assistant", content: $content}]}')
fi

# ── Call TTS API ────────────────────────────────────────────────────────────
HTTP_CODE=$(curl -s -w "%{http_code}" \
  -o "$WORK_DIR/resp.json" \
  -H "Content-Type: application/json" \
  -H "api-key: $MIMO_API_KEY" \
  -d "$PAYLOAD" \
  "$TTS_ENDPOINT")

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "Error: API returned HTTP $HTTP_CODE" >&2
  cat "$WORK_DIR/resp.json" >&2
  exit 2
fi

# ── Decode audio data ───────────────────────────────────────────────────────
DECODE_SCRIPT="$WORK_DIR/decode.py"
cat > "$DECODE_SCRIPT" << 'PYEOF'
import json, base64, struct, io, sys

resp_path, out_path = sys.argv[1], sys.argv[2]

with open(resp_path) as f:
    data = json.load(f)

# Surface API-level errors
if data.get('error'):
    print(f"Error: API error: {data['error']}", file=sys.stderr)
    sys.exit(2)

try:
    audio = data['choices'][0]['message']['audio']
    raw = base64.b64decode(audio['data'])
except (KeyError, IndexError, TypeError) as e:
    print(f"Error: unexpected response shape — {e}", file=sys.stderr)
    print(json.dumps(data, ensure_ascii=False)[:400], file=sys.stderr)
    sys.exit(2)

# Handle both WAV (RIFF header present) and raw PCM
if raw[:4] == b'RIFF':
    wav_bytes = raw
else:
    # Wrap raw PCM: 24kHz, 16-bit, mono
    sr, bps, ch = 24000, 16, 1
    br = sr * ch * bps // 8
    buf = io.BytesIO()
    buf.write(b'RIFF')
    buf.write(struct.pack('<I', 36 + len(raw)))
    buf.write(b'WAVEfmt ')
    buf.write(struct.pack('<IHHIIHH', 16, 1, ch, sr, br, ch * bps // 8, bps))
    buf.write(b'data')
    buf.write(struct.pack('<I', len(raw)))
    buf.write(raw)
    wav_bytes = buf.getvalue()

with open(out_path, 'wb') as f:
    f.write(wav_bytes)

print(f"OK: {len(wav_bytes)} bytes written to {out_path}")
PYEOF

python3 "$DECODE_SCRIPT" "$WORK_DIR/resp.json" "$OUTPUT_PATH"
DECODE_EXIT=$?
if [[ $DECODE_EXIT -ne 0 ]]; then
  exit $DECODE_EXIT
fi

# ── Verify output ───────────────────────────────────────────────────────────
if [[ ! -s "$OUTPUT_PATH" ]]; then
  echo "Error: output file is empty or was not created: $OUTPUT_PATH" >&2
  exit 3
fi
