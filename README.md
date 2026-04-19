# TokenGuard — Stop Burning Tokens in Claude Code

![TokenGuard Banner](banner-tokenguard-free.jpg)

> **20 people cloned this repo last week.** If it saves you money, [give it a ⭐](https://github.com/atalayaeps/tokenguard-claude-code)

**Cut 20-40% of your Claude Code token waste with 4 rules. Zero config. Just copy and go.**

---

## 💸 The Problem

Every Claude Code session silently burns tokens on patterns you don't notice:

- Spawning sub-agents instead of using Grep → **40K tokens wasted**
- Reimplementing code that already exists → **70K tokens wasted**
- Reading the same files over and over → **80K tokens wasted**
- Over-engineering simple tasks → **45K tokens wasted**

**One bad session = 300,000+ tokens burned.** That's real money.

## ⚡ 30-Second Setup

```bash
git clone https://github.com/atalayaeps/tokenguard-claude-code.git
cp tokenguard-claude-code/tokenguard.md your-project/.claude/rules/
cp tokenguard-claude-code/.claudeignore your-project/
cp tokenguard-claude-code/settings.json your-project/.claude/
```

**That's it.** Claude Code reads the rules automatically. No dependencies, no build step, no config.

## 📊 See Your Waste (Free Report)

```bash
python informe.py
```

Generates an HTML dashboard from your local logs — sessions analyzed, efficiency ratio, tokens wasted, most re-read files. **Zero tokens consumed** (reads local files only).

![Report Demo](reports/report-DEMO.html)

## 🛡️ What's Inside

| File | What it does |
|---|---|
| `tokenguard.md` | 4 battle-tested rules that change how Claude Code works |
| `informe.py` | Efficiency report generator (HTML dashboard) |
| `.claudeignore` | Excludes files Claude doesn't need to read |
| `settings.json` | Pre-configured thinking token limits |

## 📐 The Math

| Anti-pattern | Cost per occurrence |
|---|---|
| Build without checking first | 70,000 tokens |
| Sub-agent storm (×3) | 120,000 tokens |
| Context overflow (re-reading files) | 80,000 tokens |
| Over-engineering simple tasks | 112,000 tokens |
| **One bad session** | **300,000+ tokens** |

At Anthropic's pricing, preventing **one** bad session pays for itself.

## 🚀 Want More?

[**TokenGuard Pro**](https://4229038676731.gumroad.com/l/tokenguard-pro) — 15 rules, 3 real-time Python hooks, full benchmark (100 points), and unlocked Pro report.

---

**If TokenGuard saved you tokens, [star this repo ⭐](https://github.com/atalayaeps/tokenguard-claude-code)** — it helps others find it.

*Built by a solo developer who got tired of watching the bill go up.*

## License

MIT — Use it wherever you want.
