"""Refresh the dynamic blocks in README.md.

- RECENT: the most recently pushed original (non-fork) repositories.
- OSS:    merged pull requests to repositories owned by someone else.

Run by .github/workflows/refresh-readme.yml. Uses only the standard library.
If the GitHub API fails, the README is left untouched.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

USER = os.environ.get("GH_USER", "omkarjoshi9")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
README = Path(__file__).resolve().parent.parent / "README.md"

RECENT_LIMIT = 4
OSS_LIMIT = 6
SKIP_REPOS = {USER.lower(), "test", "dummyapp", "floaters_chatbot"}

# Curated one-liners. Repos not listed here fall back to their GitHub description,
# and are skipped if they have none (so half-finished experiments don't surface).
BLURBS = {
    "agentic_pentester": "Autonomous multi-agent web pentesting loop with guardrails and a Docker sandbox",
    "job_hunt": "Scheduled job-digest pipeline delivering a ranked Telegram digest",
    "DeploX": "Vercel-style deploy platform with a Redis build queue",
    "PSL_AI_Foundry": "Research internship work on on-device RAG with Windows AI Foundry",
    "SQLi-prevention-pipeline": "SQL injection detection pipeline on AWS (WAF + Lambda + SNS)",
    "Agentic_Search": "Multi-agent research search with a reviewer loop",
    "GitHub-Repo-Intelligence-Bot": "LLM summaries of commits and PRs, posted to Slack",
    "age_of_umpires": "Daily browser game: guess the cricket umpire's age",
    "mcportfolio": "Portfolio site built as a blocky sandbox world",
    "agentguard": "Design stage: least-privilege permissions for AI coding agents, derived from project files",
}


def api(path: str):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": f"{USER}-readme-refresh",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def month(iso: str) -> str:
    return datetime.strptime(iso[:10], "%Y-%m-%d").strftime("%b %Y")


def recent_block() -> str:
    repos = api(f"/users/{USER}/repos?type=owner&sort=pushed&per_page=50")
    lines = []
    for r in repos:
        if r["fork"] or r["archived"] or r["private"] or r["name"].lower() in SKIP_REPOS:
            continue
        blurb = BLURBS.get(r["name"]) or (r.get("description") or "").strip()
        if not blurb:
            continue
        lines.append(
            f"- **[{r['name']}]({r['html_url']})**: {blurb} · <sub>{month(r['pushed_at'])}</sub>"
        )
        if len(lines) == RECENT_LIMIT:
            break
    return "\n".join(lines)


def oss_block() -> str:
    q = urllib.parse.quote(f"author:{USER} type:pr is:merged -user:{USER}")
    items = api(f"/search/issues?q={q}&sort=created&order=desc&per_page=50")["items"]
    lines = []
    for it in items:
        repo = it["repository_url"].split("/repos/", 1)[1]
        title = it["title"].replace("[", "(").replace("]", ")").strip()
        lines.append(f"- **[{repo}]({it['html_url']})**: {title}")
        if len(lines) == OSS_LIMIT:
            break
    return "\n".join(lines)


def replace(text: str, tag: str, body: str) -> str:
    if not body:
        return text  # never blank a section because of an empty / failed response
    pattern = re.compile(rf"(<!-- {tag}:START -->\n).*?(\n<!-- {tag}:END -->)", re.S)
    return pattern.sub(lambda m: m.group(1) + body + m.group(2), text)


def main() -> int:
    original = README.read_text(encoding="utf-8")
    try:
        updated = replace(original, "RECENT", recent_block())
        updated = replace(updated, "OSS", oss_block())
    except Exception as exc:  # network / API problems: keep the current README
        print(f"skip: {exc}", file=sys.stderr)
        return 0
    if updated != original:
        README.write_text(updated, encoding="utf-8")
        print("README updated")
    else:
        print("README unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
