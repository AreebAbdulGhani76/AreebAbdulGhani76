import os
import requests
from datetime import date, timedelta
from html import escape

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
result = response.json()

if "errors" in result:
    raise RuntimeError(result["errors"])

calendar = result["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]

days = {}
for week in calendar["weeks"]:
    for item in week["contributionDays"]:
        days[item["date"]] = item

# Calendar layout: 7 rows, one column per week.
start_date = start - timedelta(days=start.weekday())
columns = (today - start_date).days // 7 + 1
cell, gap, margin = 11, 3, 30
step = cell + gap
width = margin * 2 + columns * step
height = 150

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">',
    '<rect width="100%" height="100%" rx="8" fill="#0d1117"/>',
    '<text x="20" y="22" fill="#c9d1d9" '
    'font-size="14" font-family="Arial">GitHub Contributions — Last Year</text>',
]

for day_string, item in days.items():
    current = date.fromisoformat(day_string)
    col = (current - start_date).days // 7
    row = current.weekday()
    x = margin + col * step
    y = 36 + row * step

    count = item["contributionCount"]
    color = item["color"]

    tooltip = escape(
        f"{current.strftime('%B')} {current.day}, {current.year}: "
        f"{count} contribution{'s' if count != 1 else ''}"
    )

    parts.append(
        f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" '
        f'rx="2" fill="{color}">'
        f'<title>{tooltip}</title></rect>'
    )

parts.extend([
    f'<text x="20" y="{height - 12}" fill="#c9d1d9" '
    f'font-size="11" font-family="Arial">'
    f'{calendar["totalContributions"]} contributions in the displayed calendar'
    f'</text>',
    '</svg>',
])

os.makedirs("dist", exist_ok=True)
with open("dist/contribution-calendar.svg", "w", encoding="utf-8") as file:
    file.write("\n".join(parts))

print("Contribution calendar generated successfully.")
