#!/bin/bash
# TokenGuard Benchmark Lite — 3 metrics, max score 55/100
# Measures your Claude Code setup efficiency
# Full benchmark (6 metrics, 100/100): https://gumroad.com/tokenguard

set -euo pipefail

SCORE=0
MAX=55
DETAILS=""

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   TokenGuard Benchmark Lite v1.0     ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ─── Metric 1: CLAUDE.md size (0-20 points) ───
if [ -f "CLAUDE.md" ]; then
  TOKENS=$(wc -w < CLAUDE.md)
  if [ "$TOKENS" -le 500 ]; then
    M1=20
  elif [ "$TOKENS" -le 1000 ]; then
    M1=15
  elif [ "$TOKENS" -le 2000 ]; then
    M1=10
  elif [ "$TOKENS" -le 4000 ]; then
    M1=5
  else
    M1=0
  fi
  DETAILS+="  CLAUDE.md         ${TOKENS} words → ${M1}/20 pts"$'\n'
else
  M1=0
  DETAILS+="  CLAUDE.md         not found → 0/20 pts"$'\n'
fi
SCORE=$((SCORE + M1))

# ─── Metric 2: .claudeignore (0-15 points) ───
if [ -f ".claudeignore" ]; then
  LINES=$(grep -c '[^[:space:]]' .claudeignore 2>/dev/null || echo 0)
  if [ "$LINES" -ge 20 ]; then
    M2=15
  elif [ "$LINES" -ge 10 ]; then
    M2=10
  elif [ "$LINES" -ge 5 ]; then
    M2=5
  else
    M2=2
  fi
  DETAILS+="  .claudeignore     ${LINES} rules → ${M2}/15 pts"$'\n'
else
  M2=0
  DETAILS+="  .claudeignore     not found → 0/15 pts"$'\n'
fi
SCORE=$((SCORE + M2))

# ─── Metric 3: MAX_THINKING_TOKENS (0-20 points) ───
SETTINGS_FILE=""
if [ -f ".claude/settings.json" ]; then
  SETTINGS_FILE=".claude/settings.json"
elif [ -f "settings.json" ]; then
  SETTINGS_FILE="settings.json"
fi

if [ -n "$SETTINGS_FILE" ]; then
  if command -v jq &>/dev/null; then
    THINKING=$(jq -r '.preferences.maxThinkingTokens // empty' "$SETTINGS_FILE" 2>/dev/null)
  else
    THINKING=$(grep '"maxThinkingTokens"' "$SETTINGS_FILE" 2>/dev/null | sed 's/[^0-9]//g' || echo "")
  fi

  if [ -n "$THINKING" ]; then
    if [ "$THINKING" -le 10000 ]; then
      M3=20
    elif [ "$THINKING" -le 20000 ]; then
      M3=15
    elif [ "$THINKING" -le 50000 ]; then
      M3=10
    else
      M3=5
    fi
    DETAILS+="  Thinking tokens   ${THINKING} max → ${M3}/20 pts"$'\n'
  else
    M3=0
    DETAILS+="  Thinking tokens   not configured → 0/20 pts"$'\n'
  fi
else
  M3=0
  DETAILS+="  Thinking tokens   no settings file → 0/20 pts"$'\n'
fi
SCORE=$((SCORE + M3))

# ─── Results ───
echo "Results:"
echo "$DETAILS"
echo "───────────────────────────────────────"
echo "  Score: ${SCORE}/${MAX}"
echo ""

# Visual bar
FILLED=$((SCORE * 30 / MAX))
BAR=""
for ((i=0; i<FILLED; i++)); do BAR+="█"; done
for ((i=FILLED; i<30; i++)); do BAR+="░"; done
echo "  [${BAR}] ${SCORE}/${MAX}"
echo ""

# Pro upsell (only for metrics not measured)
echo "  ┌─────────────────────────────────────"
echo "  │ 3 more metrics in Pro (max 100/100):"
echo "  │  · Subagent model configuration"
echo "  │  · MCP server count"
echo "  │  · Prevention hooks active"
echo "  │"
echo "  │ → https://gumroad.com/tokenguard"
echo "  └─────────────────────────────────────"
echo ""
