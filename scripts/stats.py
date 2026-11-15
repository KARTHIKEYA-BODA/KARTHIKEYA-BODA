"""Builds assets/stats.svg for the profile README.

Run locally:   GH_TOKEN=<token> GH_USER=KARTHIKEYA-BODA python scripts/stats.py
In Actions:    see .github/workflows/update-stats.yml (runs daily).
Only the standard library is used.
"""
import json, os, sys, urllib.request
from datetime import date, datetime, timedelta

BG, BONE, MUTE = "#0A0C11", "#E8ECF4", "#8693AB"
TOP, LEFT, RIGHT, EDGE = "#38466A", "#1B2332", "#121823", "#5B6BFF"
FONT = "'Segoe UI','Helvetica Neue',Arial,sans-serif"


def render(tiles, months=None):
    """tiles: [(value, label)], months: [(label, count)] or None."""
    W = 1200
    H = 150 if not months else 330
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub activity summary">',
         f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="#171C28"/>']
    n = len(tiles)
    step = (W - 80) / n
    for i, (val, label) in enumerate(tiles):
        x = 40 + i * step
        o.append(f'<text x="{x:.0f}" y="76" font-family="{FONT}" font-size="46" font-weight="800" fill="{BONE}">{val}</text>')
        o.append(f'<text x="{x:.0f}" y="106" font-family="{FONT}" font-size="14" fill="{MUTE}">{label}</text>')
        if i:
            o.append(f'<path d="M{x-24:.0f} 40V112" stroke="#1D2434"/>')
    if months:
        peak = max(c for _, c in months) or 1
        u = 14
        dx = u * .866
        dy = u * .5
        base = 290
        maxh = 110
        gap = (W - 120) / len(months)
        o.append(f'<path d="M40 {base+dy+8}H{W-40}" stroke="#1D2434"/>')

        def poly(pts, fill):
            return '<polygon points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f'" fill="{fill}" stroke="{EDGE}" stroke-opacity=".45"/>'

        for i, (lab, c) in enumerate(months):
            x = 60 + gap * i + gap / 2
            h = max(4, c / peak * maxh)
            L = (x - dx, base - h)
            R = (x + dx, base - h)
            T = (x, base - h - dy)
            B = (x, base - h + dy)
            o.append(poly([L, B, (x, base + dy), (x - dx, base)], LEFT))
            o.append(poly([R, B, (x, base + dy), (x + dx, base)], RIGHT))
            o.append(poly([T, R, B, L], TOP))
            o.append(f'<text x="{x:.1f}" y="{base-h-dy-8:.1f}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{BONE}">{c}</text>')
            o.append(f'<text x="{x:.1f}" y="{base+dy+26}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{MUTE}">{lab}</text>')
    o.append('</svg>')
    return "\n".join(o)


def gql(token, query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


Q = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){createdAt
followers{totalCount} repositories(ownerAffiliations:OWNER){totalCount}
contributionsCollection(from:$from,to:$to){contributionCalendar{totalContributions
weeks{contributionDays{date contributionCount}}}}}}"""


def main():
    token = os.environ.get("GH_TOKEN") or os.environ["GITHUB_TOKEN"]
    user = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER", "KARTHIKEYA-BODA")
    today = date.today()
    probe = gql(token, Q, {"login": user, "from": f"{today.year}-01-01T00:00:00Z", "to": f"{today}T23:59:59Z"})["user"]
    first = datetime.fromisoformat(probe["createdAt"].replace("Z", "+00:00")).year
    days, total, followers, repos = {}, 0, 0, 0
    for y in range(first, today.year + 1):
        end = min(date(y, 12, 31), today)
        u = gql(token, Q, {"login": user, "from": f"{y}-01-01T00:00:00Z", "to": f"{end}T23:59:59Z"})["user"]
        followers, repos = u["followers"]["totalCount"], u["repositories"]["totalCount"]
        cal = u["contributionsCollection"]["contributionCalendar"]
        total += cal["totalContributions"]
        for w in cal["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    longest = run = 0
    prev = None
    for d in sorted(days):
        cur = date.fromisoformat(d)
        if days[d] > 0:
            run = run + 1 if prev is not None and (cur - prev).days == 1 and run > 0 else 1
        else:
            run = 0
        longest = max(longest, run)
        prev = cur

    cutoff = (today - timedelta(days=365)).isoformat()
    last_year = sum(c for d, c in days.items() if d >= cutoff)
    months = []
    y, m = today.year, today.month
    for _ in range(12):
        key = f"{y}-{m:02d}"
        months.append((date(y, m, 1).strftime("%b"), sum(c for d, c in days.items() if d.startswith(key))))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    months.reverse()

    tiles = [(total, f"Contributions since {first}"), (last_year, "Contributions, last 12 months"),
             (repos, "Repositories"), (longest, "Day longest streak"), (followers, "Followers")]
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "stats.svg")
    with open(out, "w") as f:
        f.write(render(tiles, months))
    print("wrote", out)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("stats generation failed:", e, file=sys.stderr)
        sys.exit(1)
