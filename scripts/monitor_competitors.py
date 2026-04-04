"""
OpenArena competitor monitor — daily scrape of top 10 project GitHub stats, diff analysis, TG push.
Usage: python scripts/monitor_competitors.py
"""

import subprocess
import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# === Config ===
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "scripts" / "monitor_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TG_BOT_TOKEN = "8608229739:AAHb_nKM8at8kFMYkxZOCZ4Jtk_8f6AGkU4"
TG_CHAT_ID = "6098536339"
PROXY_HOST = "127.0.0.1:10808"
API_BASE = f"https://api.telegram.org/bot{TG_BOT_TOKEN}"

# Top 10 repos — update if leaderboard changes
COMPETITORS = [
    {"rank": 1, "name": "Agent Reach", "repo": "Panniantong/Agent-Reach", "score": 90.2},
    {"rank": 2, "name": "OpenCLI", "repo": "jackwener/opencli", "score": 80},
    {"rank": 3, "name": "autoresearch", "repo": "karpathy/autoresearch", "score": 70.2},
    {"rank": 4, "name": "lark-cli", "repo": "larksuite/cli", "score": 67.84},
    {"rank": 5, "name": "InkOS", "repo": "Narcooo/inkos", "score": 66.67},
    {"rank": 6, "name": "Crucix", "repo": "calesthio/Crucix", "score": 65.49},
    {"rank": 7, "name": "Aura AI Trading", "repo": "Aura-AI-Trading-Agent/Aura-AI-Trading-Agent", "score": 64.31},
    {"rank": 8, "name": "DingTalk CLI", "repo": "DingTalk-Real-AI/dingtalk-workspace-cli", "score": 63.53},
    {"rank": 9, "name": "memory-lancedb-pro", "repo": "CortexReach/memory-lancedb-pro", "score": 58.43},
    {"rank": 10, "name": "OpenShell", "repo": "NVIDIA/OpenShell", "score": 56.08},
]

OUR_REPO = "0xSanei/darwinia"


def gh_api(endpoint):
    """Call GitHub API via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True, timeout=30,
            encoding="utf-8", errors="replace"
        )
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
        elif result.returncode != 0:
            print(f"  gh api {endpoint}: rc={result.returncode}")
    except Exception as e:
        print(f"  gh api error for {endpoint}: {e}")
    return None


def fetch_repo_info(repo):
    """Fetch key metrics for a repo."""
    data = gh_api(f"repos/{repo}")
    if not data:
        return None

    commits = gh_api(f"repos/{repo}/commits?per_page=3") or []

    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "pushed_at": data.get("pushed_at", ""),
        "description": data.get("description", ""),
        "language": data.get("language", ""),
        "topics": data.get("topics", []),
        "recent_commits": [
            {
                "sha": c.get("sha", "")[:7],
                "message": c.get("commit", {}).get("message", "").split("\n")[0][:80],
                "date": c.get("commit", {}).get("committer", {}).get("date", ""),
            }
            for c in commits[:3]
        ],
    }


def load_previous():
    """Load yesterday's data for comparison."""
    files = sorted(DATA_DIR.glob("*.json"))
    if files:
        return json.loads(files[-1].read_text(encoding="utf-8"))
    return {}


def calc_changes(current, previous):
    """Calculate changes from previous snapshot."""
    changes = []
    for comp in COMPETITORS:
        repo = comp["repo"]
        cur = current.get(repo)
        prev = previous.get(repo)
        if not cur:
            continue

        change = {"name": comp["name"], "rank": comp["rank"], "repo": repo}
        change["stars"] = cur["stars"]
        change["star_delta"] = cur["stars"] - (prev["stars"] if prev else cur["stars"])
        change["new_commits"] = []

        if prev:
            prev_shas = {c["sha"] for c in prev.get("recent_commits", [])}
            change["new_commits"] = [
                c for c in cur.get("recent_commits", [])
                if c["sha"] not in prev_shas
            ]

        change["active"] = bool(change["new_commits"])
        changes.append(change)

    return changes


def format_report(changes, our_info):
    """Format TG message in HTML."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"<b>🏟 OpenArena Daily Report | {today}</b>", ""]

    # Our project status
    if our_info:
        lines.append(f"<b>📊 Darwinia</b>: ⭐{our_info['stars']} | 🍴{our_info['forks']}")
        lines.append("")

    # Active projects (had commits today)
    active = [c for c in changes if c["active"]]
    inactive = [c for c in changes if not c["active"]]

    if active:
        lines.append("<b>🔥 Active Today</b>")
        for c in active:
            delta = f"+{c['star_delta']}" if c['star_delta'] > 0 else str(c['star_delta'])
            lines.append(f"  #{c['rank']} <b>{c['name']}</b> ⭐{c['stars']}({delta})")
            for commit in c["new_commits"][:2]:
                lines.append(f"    └ <code>{commit['sha']}</code> {commit['message'][:50]}")

    if inactive:
        lines.append("")
        lines.append("<b>😴 No Updates Today</b>")
        names = [f"#{c['rank']}{c['name']}" for c in inactive]
        lines.append("  " + " | ".join(names))

    # Star ranking
    lines.append("")
    lines.append("<b>⭐ Star Ranking</b>")
    sorted_by_stars = sorted(changes, key=lambda x: x["stars"], reverse=True)
    for i, c in enumerate(sorted_by_stars[:5]):
        lines.append(f"  {i+1}. {c['name']}: {c['stars']:,}")

    # Insights
    big_movers = [c for c in changes if abs(c.get("star_delta", 0)) > 50]
    if big_movers:
        lines.append("")
        lines.append("<b>📈 Big Movers</b>")
        for c in big_movers:
            lines.append(f"  {c['name']}: star {'+' if c['star_delta']>0 else ''}{c['star_delta']}")

    lines.append("")
    lines.append(f"<i>As of {today} 23:00 | {max(0, (datetime(2026,4,15) - datetime.now()).days)} days until submission deadline</i>")

    return "\n".join(lines)


def send_tg(text):
    """Send message to TG via curl + SOCKS5."""
    payload = json.dumps({
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }, ensure_ascii=False).encode("utf-8")

    try:
        proc = subprocess.run(
            ["curl", "-s", "--socks5-hostname", PROXY_HOST,
             "-X", "POST", f"{API_BASE}/sendMessage",
             "-H", "Content-Type: application/json",
             "--data-binary", "@-"],
            input=payload, capture_output=True, timeout=30,
        )
        resp = json.loads(proc.stdout) if proc.stdout else {}
        if resp.get("ok"):
            print("TG push OK")
        else:
            print(f"TG push failed: {resp}")
    except Exception as e:
        print(f"TG push error: {e}")


def main():
    print(f"=== OpenArena Competitor Monitor | {datetime.now().isoformat()} ===")

    # Fetch all repos
    current = {}
    for comp in COMPETITORS:
        print(f"  Fetching #{comp['rank']} {comp['name']} ({comp['repo']})...")
        info = fetch_repo_info(comp["repo"])
        if info:
            current[comp["repo"]] = info
        time.sleep(0.5)  # Rate limit

    # Fetch our repo
    print(f"  Fetching our repo ({OUR_REPO})...")
    our_info = fetch_repo_info(OUR_REPO)

    # Load previous & compare
    previous = load_previous()
    changes = calc_changes(current, previous)

    # Save today's snapshot
    today = datetime.now().strftime("%Y-%m-%d")
    snapshot_path = DATA_DIR / f"{today}.json"
    snapshot_path.write_text(
        json.dumps(current, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"  Saved snapshot: {snapshot_path}")

    # Format & send report
    report = format_report(changes, our_info)
    print("\n" + report.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "").replace("<code>", "").replace("</code>", ""))

    send_tg(report)
    print("\nDone.")


if __name__ == "__main__":
    main()
