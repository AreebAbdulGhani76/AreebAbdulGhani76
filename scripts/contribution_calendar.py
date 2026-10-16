
import os
import html
import requests
from datetime import date, timedelta
from pathlib import Path

USERNAME = "AreebAbdulGhani76"
TOKEN = os.environ["GH_TOKEN"]

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""

today = date.today()
start = today - timedelta(days=364)

response = requests.post(
    "https://api.github.com/graphql",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={
        "query": query,
        "variables": {
            "login": USERNAME,
            "from": f"{start.isoformat()}T00:00:00Z",
            "to": f"{today.isoformat()}T23:59:59Z",
        },
    },
    timeout=30,
)
response.raise_for_status()
data = response.json()

if "errors" in data:
    raise RuntimeError(data["errors"])

calendar = data["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]
days = {
    item["date"]: item
    for week in calendar["weeks"]
    for item in week["contributionDays"]
}

# Layout
cell = 11
gap = 3
step = cell + gap
left = 38
top = 62
bottom = 38
start_date = start - timedelta(days=start.weekday())
columns = ((today - start_date).days // 7) + 1
width = left + 18 + columns * step
height = top + 7 * step + bottom

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
    f'<rect width="{width}" height="{height}" rx="12" fill="#0d1117"/>',
    '<text x="20" y="28" fill="#f0f6fc" font-size="17" '
    'font-weight="600" font-family="Arial">A Year of Building</text>',
    f'<text x="20" y="47" fill="#8b949e" font-size="11" '
    f'font-family="Arial">{calendar["totalContributions"]:,} contributions in the last year</text>',
]

# Day labels
for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
    y = top + row * step + 9
    parts.append(
        f'<text x="8" y="{y}" fill="#8b949e" '
        f'font-size="9" font-family="Arial">{label}</text>'
    )

# Month labels
shown_months = set()
for d in sorted(days):
    current = date.fromisoformat(d)
    if current.day <= 7:
        col = (current - start_date).days // 7
        if current.strftime("%Y-%m") not in shown_months:
            x = left + col * step
            parts.append(
                f'<text x="{x}" y="{top - 10}" fill="#8b949e" '
                f'font-size="9" font-family="Arial">'
                f'{html.escape(current.strftime("%b"))}</text>'
            )
            shown_months.add(current.strftime("%Y-%m"))

# Contribution squares with native SVG tooltips
for d, item in days.items():
    current = date.fromisoformat(d)
    col = (current - start_date).days // 7
    row = current.weekday()
    x = left + col * step
    y = top + row * step
    count = item["contributionCount"]
    color = item["color"]
    plural = "" if count == 1 else "s"
    tooltip = html.escape(
        f"{count} contribution{plural} on "
        f"{current.strftime('%b %d, %Y')}"
    )

    parts.append(
        f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" '
        f'rx="2" fill="{color}" stroke="#0d1117" stroke-width="0.5">'
        f'<title>{tooltip}</title></rect>'
    )

# Legend
legend_y = height - 16
parts.append(
    f'<text x="{left}" y="{legend_y}" fill="#8b949e" '
    f'font-size="9" font-family="Arial">Less</text>'
)
legend_x = left + 29
for color in ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]:
    parts.append(
        f'<rect x="{legend_x}" y="{legend_y - 9}" width="10" height="10" '
        f'rx="2" fill="{color}"/>'
    )
    legend_x += 14

parts.append(
    f'<text x="{legend_x + 2}" y="{legend_y}" fill="#8b949e" '
    f'font-size="9" font-family="Arial">More</text>'
)
parts.append("</svg>")

Path("dist").mkdir(exist_ok=True)
Path("dist/contribution-calendar.svg").write_text(
    "\n".join(parts), encoding="utf-8"
)
print("Contribution dashboard generated.")
