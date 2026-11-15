#!/usr/bin/env python3
"""Build a repository-hosted SVG from public GitHub API data."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

user = "KARTHIKEYA-BODA"
headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-stats"}
if os.environ.get("GITHUB_TOKEN"):
    headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
request = Request("https://api.github.com/users/" + user, headers=headers)
with urlopen(request, timeout=20) as response:
    data = json.load(response)
repos, followers = int(data["public_repos"]), int(data["followers"])
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="145" viewBox="0 0 1200 145"><rect width="1200" height="145" rx="10" fill="#0a0c10"/><rect x="1" y="1" width="1198" height="143" rx="9" fill="none" stroke="#303842" stroke-width="2"/><text x="42" y="43" fill="#ff9f1c" font-family="monospace" font-size="17" letter-spacing="2">PUBLIC GITHUB SIGNAL</text><text x="42" y="94" fill="#e6edf3" font-family="monospace" font-size="27">{repos}</text><text x="98" y="94" fill="#c9d1d9" font-family="monospace" font-size="17">PUBLIC REPOSITORIES</text><text x="515" y="94" fill="#e6edf3" font-family="monospace" font-size="27">{followers}</text><text x="570" y="94" fill="#c9d1d9" font-family="monospace" font-size="17">FOLLOWERS</text></svg>'''
Path("assets/stats.svg").write_text(svg + "\n", encoding="utf-8")
