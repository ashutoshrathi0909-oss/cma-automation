# AutoResearch + Claude Peers — Reference Document
*Created: 2026-03-31*

---

## Part 1 — Karpathy's AutoResearch (Claude Code Skill)

### Origin

Andrej Karpathy published ~630 lines of Python to GitHub on **March 6, 2026**. The original was designed for ML research — autonomously tuning hyperparameters overnight. It hit **42,000 GitHub stars in two weeks**, which prompted several developers to port the concept into a generalized Claude Code skill.

The most prominent port is by **Udit Goenka** ([uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch)), released March 13, 2026, which generalizes the pattern to any domain with a measurable outcome.

---

### What It Is

AutoResearch is a **Claude Code skill** that turns Claude into a self-directed improvement loop. You give it a goal and a metric. It runs forever (or for N iterations), making one change at a time, measuring the result, and keeping or discarding the change — with no human in the loop between iterations.

**The loop in full:**

```
GOAL + METRIC defined by you
         ↓
Claude reviews current state + git history + results log
         ↓
Claude proposes ONE atomic change
         ↓
Change is committed to git
         ↓
Metric is evaluated (tests, benchmarks, scores, build output)
         ↓
KEEP → commit stays  |  DISCARD → git reset (auto-revert)
         ↓
Repeat from top
```

The key principle borrowed from Karpathy: **one change per iteration, always commit before verify, auto-revert on failure.** No manual cleanup, no interrupted state.

---

### Core Principles (7 Rules)

1. **One change per iteration** — No bundled changes. Each commit is atomic and independently verifiable.
2. **Commit before verify** — Change is committed first; if metric fails, the commit is reverted. Clean git history of what worked.
3. **Auto-revert on failure** — `git reset --hard HEAD~1` runs automatically if the metric regresses.
4. **Real metrics only** — No vibes. Must be a number: test pass rate, benchmark score, build time, lint count, etc.
5. **Log everything** — Every iteration is written to a `.tsv` log file: iteration number, commit hash, metric value, delta, status (keep/discard), description.
6. **Progress summary every 10 iterations** — Claude prints a structured summary automatically.
7. **MCP servers are available in the loop** — Database queries, API calls, analytics — all accessible during the loop.

---

### What "Metric" Means

Instead of a loss function (like in ML), you define an **eval file** — a collection of input/expected-output pairs. The metric is the **pass rate** (what % of eval cases Claude gets right).

- **Binary assertions** (deterministic yes/no) are preferred over LLM-based scoring — they are stable, comparable across runs, and easy to debug.
- Metrics can also be: number of passing tests, a benchmark score, build output, lint warnings count, or any other shell-evaluable number.
- The metric must be **mechanically measurable** — Claude cannot self-report whether it improved.

---

### Domains It Works In

The skill is not ML-specific. It works for any domain with a measurable signal:

| Domain | Example Metric |
|---|---|
| Code quality | Pytest pass rate, lint count |
| Prompt engineering | Eval file pass rate (%) |
| Classification rules | Accuracy on a labelled dataset |
| Content / marketing | A/B score, readability score |
| DevOps | Build time, image size |
| Search algorithms | Precision/recall on test queries |
| Sales copy | Conversion score via eval |

---

### Typical Results

A full overnight run of **30–50 cycles** typically pushes pass rates from **40–50% → 75–85%**. One reported result: a landing page skill improved from **41% → 92% in 4 rounds**. Shopify's CEO reportedly ran it overnight and got a **19% improvement**.

---

### Available Commands

| Command | What It Does |
|---|---|
| `/autoresearch` | Main loop — improve anything with a metric |
| `/autoresearch:security` | Read-only security analysis; produces structured report; `--fix` flag opts into auto-remediation of Critical/High findings |
| `Iterations: N` | Add to inline config to cap the loop at N iterations instead of running forever |
| `Ctrl+C` | Stops the loop at any point |

---

### Repository Variants

| Repo | Notes |
|---|---|
| [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) | Primary generalized skill. MIT license. |
| [proyecto26/autoresearch-ai-plugin](https://github.com/proyecto26/autoresearch-ai-plugin) | Plugin variant |
| [drivelineresearch/autoresearch-claude-code](https://github.com/drivelineresearch/autoresearch-claude-code) | Port of Karpathy's original pi-autoresearch |
| [zhongpei/autoresearch-skills](https://github.com/zhongpei/autoresearch-skills) | Fork of uditgoenka's skill |
| [alvinunreal/awesome-autoresearch](https://github.com/alvinunreal/awesome-autoresearch) | Curated list of all autoresearch-style systems |

---

### Installation in This Project

**Option A — Plugin Marketplace (recommended)**

Inside a Claude Code session:
```
/plugin marketplace add uditgoenka/autoresearch
```

Then **start a new Claude Code session** before using it. (Reference files are not resolvable in the same session where installation happened — this is a Claude Code platform limitation.)

**Option B — Manual copy**

```bash
# Clone the repo
git clone https://github.com/uditgoenka/autoresearch.git ~/autoresearch-skill

# Copy the skill into this project's .claude directory
cp -r ~/autoresearch-skill/.claude/skills/autoresearch \
      "C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/.claude/skills/"
```

Then start a new Claude Code session.

**Verification:**

Once installed, in a fresh Claude Code session you should see `/autoresearch` listed when you type `/`.

---

---

## Part 2 — Claude Peers MCP

### Origin

Released by **Louis Lva** ([louislva/claude-peers-mcp](https://github.com/louislva/claude-peers-mcp)) in March 2026, as part of a wave of open-source tools that emerged after Anthropic shipped experimental **Agent Teams** (peer-to-peer Claude Code coordination) in February 2026.

It was featured in the "5 Open Source Repos That Make Claude Code Unstoppable" roundup and is listed on [mcpmarket.com](https://mcpmarket.com/server/claude-peers).

---

### What It Is

Claude Peers is an **MCP server** (Model Context Protocol server) that runs locally on your machine. It creates a shared communication bus that allows every Claude Code session currently open on your machine to:

- Discover each other (see what other sessions are running and what they're working on)
- Send and receive messages between sessions in real time
- Coordinate across different terminal windows without manual copy-paste

It solves the **silo problem**: when you have multiple Claude Code terminals open across different parts of the same project (or different projects), they normally have zero awareness of each other. Claude Peers gives them a shared channel.

---

### Architecture

```
Terminal 1 (Claude Code)          Terminal 2 (Claude Code)
       ↓                                  ↓
  MCP server instance               MCP server instance
       ↓                                  ↓
       └──────────→ BROKER DAEMON ←───────┘
                   localhost:7899
                   SQLite database
```

- The **broker daemon** starts automatically the first time any session connects. It runs on `localhost:7899` backed by a SQLite database.
- Each Claude Code session spawns its own **MCP server instance** that registers with the broker.
- Each instance **polls for messages every second**.
- Inbound messages arrive via Claude's `claude/channel` protocol — the receiving session sees them immediately.
- The broker **auto-cleans dead peers** (sessions that disconnected without notice).
- Everything is **localhost-only**. No external network calls.

---

### Core Capabilities

#### 1. Peer Discovery

Any session can call `list_peers` to see all currently active Claude Code sessions on the machine. The response includes:
- Peer ID
- Working directory of that session
- Auto-generated summary of what that session is working on (if configured)
- Connection status

#### 2. Real-Time Messaging

Any session can send a message to any other session by peer ID. The recipient sees it immediately via the channel protocol — it appears in the Claude Code context as if it were a new user message.

```bash
# Via CLI (outside Claude Code)
bun cli.ts send <peer-id> "your message here"
```

#### 3. Auto-Summary (Optional)

When `OPENAI_API_KEY` is set in the environment, each session generates a brief natural-language summary on startup using `gpt-5.4-nano`. The summary describes what the session is likely working on, based on:
- Working directory name
- Current git branch
- Recently modified files

Other sessions see this summary when they call `list_peers`.

#### 4. Scoped Channels

Sessions can be scoped — so a group of related sessions can form a sub-channel and only message within that group, rather than broadcasting to all active peers.

---

### CLI Commands (run from `~/claude-peers-mcp`)

| Command | What It Does |
|---|---|
| `bun cli.ts status` | Show broker status + all registered peers |
| `bun cli.ts peers` | List all active peers in a table |
| `bun cli.ts send <peer-id> "message"` | Send a message into a specific Claude session |
| `bun cli.ts kill-broker` | Stop the broker daemon |

---

### Requirements

| Requirement | Detail |
|---|---|
| **Bun runtime** | Must be installed (`bun.sh`) |
| **Claude Code version** | v2.1.80 or newer |
| **Authentication** | `claude.ai` login required — API key auth will NOT work for channels |
| **OS** | Any OS Claude Code runs on (localhost networking only) |

---

### Installation in This Project

**Step 1 — Install Bun (if not already installed)**

```bash
# Windows (PowerShell)
powershell -c "irm bun.sh/install.ps1 | iex"

# Or via npm
npm install -g bun
```

**Step 2 — Clone the repo**

```bash
git clone https://github.com/louislva/claude-peers-mcp.git ~/claude-peers-mcp
cd ~/claude-peers-mcp
bun install
```

**Step 3 — Register the MCP server globally with Claude Code**

```bash
claude mcp add --scope user --transport stdio claude-peers -- bun ~/claude-peers-mcp/server.ts
```

The `--scope user` flag means this MCP server will be available across ALL your Claude Code sessions, not just this project.

**Step 4 — Start Claude Code with development channels enabled**

```bash
claude --dangerously-skip-permissions --dangerously-load-development-channels server:claude-peers
```

The broker daemon starts automatically on first connection.

**Verification:**

Open a second terminal, run the same `claude` command. Then in either session, ask Claude to `list_peers` — you should see both sessions listed.

---

---

## Combined Summary

| | AutoResearch | Claude Peers |
|---|---|---|
| **Type** | Claude Code Skill | MCP Server |
| **Purpose** | Autonomous self-improvement loop | Multi-session communication bus |
| **Requires** | Claude Code | Bun + Claude Code v2.1.80+ + claude.ai login |
| **Runs** | Inside a single Claude Code session | Across all sessions on the machine |
| **Persistence** | Git commits + TSV log | SQLite on localhost |
| **Human input needed** | Only to define goal + metric | Only to set up; sessions self-discover after |
| **Stops when** | `Ctrl+C` or `Iterations: N` reached | When broker is killed |
| **Open source** | Yes (MIT) | Yes |

---

## Sources

- [uditgoenka/autoresearch (GitHub)](https://github.com/uditgoenka/autoresearch)
- [Udit Goenka project page](https://udit.co/projects/autoresearch)
- [louislva/claude-peers-mcp (GitHub)](https://github.com/louislva/claude-peers-mcp)
- [Claude Peers — MCP Market](https://mcpmarket.com/server/claude-peers)
- [Claude Peers — ScriptByAI explainer](https://www.scriptbyai.com/claude-peers-mcp/)
- [DeepWiki — claude-peers-mcp architecture](https://deepwiki.com/louislva/claude-peers-mcp)
- [MindStudio — AutoResearch pattern explainer](https://www.mindstudio.ai/blog/karpathy-autoresearch-pattern-claude-code-skills)
- [MindStudio — Eval loop + binary tests](https://www.mindstudio.ai/blog/autoresearch-eval-loop-binary-tests-claude-code-skills)
- [Medium — Reza Rezvani's AutoResearch skill writeup](https://alirezarezvani.medium.com/i-turned-karpathys-autoresearch-into-a-agent-skill-for-claude-code-that-optimizes-anything-here-97de83f2b7f0)
- [Botmonster — 5 repos for Claude Code](https://botmonster.com/posts/5-open-source-repos-claude-code-unstoppable-march-2026/)
- [alvinunreal/awesome-autoresearch](https://github.com/alvinunreal/awesome-autoresearch)
