#!/usr/bin/env python3
"""Update README public project list from GitHub public repos."""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import urllib.request

OWNER = "sedgar03"
README_PATH = "README.md"
START = "<!-- public-projects:start -->"
END = "<!-- public-projects:end -->"


def fetch_public_repos(owner: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{owner}/repos"
            f"?type=public&sort=updated&per_page=100&page={page}"
        )
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "profile-readme-updater",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if not data:
            break

        repos.extend(data)
        page += 1

    filtered = []
    for repo in repos:
        if repo.get("private"):
            continue
        if repo.get("fork"):
            continue
        name = str(repo.get("name", ""))
        if name.lower() == owner.lower():
            continue
        filtered.append(repo)

    filtered.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
    return filtered


def build_section(repos: list[dict]) -> str:
    if not repos:
        return "_Auto-generated from public repositories. No public projects yet._"

    lines: list[str] = []
    for repo in repos:
        name = repo.get("name", "")
        url = repo.get("html_url", "")
        desc = (repo.get("description") or "").strip()
        stars = int(repo.get("stargazers_count") or 0)
        updated = str(repo.get("updated_at") or "")

        updated_short = ""
        if updated:
            try:
                d = dt.datetime.fromisoformat(updated.replace("Z", "+00:00"))
                updated_short = d.strftime("%Y-%m-%d")
            except ValueError:
                updated_short = ""

        parts = [f"- [{name}]({url})"]
        if desc:
            parts.append(f"- {desc}")
        meta = []
        meta.append(f"stars: {stars}")
        if updated_short:
            meta.append(f"updated: {updated_short}")
        if meta:
            parts.append(f"({', '.join(meta)})")

        lines.append(" ".join(parts))

    return "\n".join(lines)


def replace_block(readme: str, section: str) -> str:
    pattern = re.compile(
        rf"{re.escape(START)}.*?{re.escape(END)}",
        flags=re.DOTALL,
    )
    replacement = f"{START}\n{section}\n{END}"
    if not pattern.search(readme):
        raise RuntimeError("README markers not found")
    return pattern.sub(replacement, readme)


def main() -> int:
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    repos = fetch_public_repos(OWNER)
    section = build_section(repos)
    updated = replace_block(readme, section)

    if updated != readme:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated)
        print("Updated README public projects section")
    else:
        print("README already up to date")

    return 0


if __name__ == "__main__":
    sys.exit(main())
