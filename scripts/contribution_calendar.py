
import os
import json
import html
import requests
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

USERNAME = "AreebAbdulGhani76"
TOKEN = os.environ["GH_TOKEN"]

today = datetime.now(timezone.utc).date()
start = today - timedelta(days=364)

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

if result.get("errors"):
    raise RuntimeError(result["errors"])

calendar = result["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]

days = [
    day
    for week in calendar["weeks"]
    for day in week["contributionDays"]
]
days = [
    day for day in days
    if start.isoformat() <= day["date"] <= today.isoformat()
]

active_days = sum(d["contributionCount"] > 0 for d in days)

longest_streak = 0
current_streak = 0

for day in days:
    if day["contributionCount"] > 0:
        current_streak += 1
        longest_streak = max(longest_streak, current_streak)
    else:
        current_streak = 0

# Current streak: count backwards from today.
current_streak = 0
for day in reversed(days):
    if day["contributionCount"] > 0:
        current_streak += 1
    elif day["date"] != today.isoformat():
        break

data = json.dumps(
    {
        "days": days,
        "total": calendar["totalContributions"],
        "activeDays": active_days,
        "longestStreak": longest_streak,
        "currentStreak": current_streak,
        "start": start.isoformat(),
        "end": today.isoformat(),
    }
)

page = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A Year of Building | Areeb Abdul Ghani</title>
<style>
:root {
  color-scheme: dark;
  --bg: #0d1117;
  --panel: #161b22;
  --border: #30363d;
  --text: #e6edf3;
  --muted: #8b949e;
  --accent: #58a6ff;
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 28px 16px;
  background: var(--bg); color: var(--text);
  font: 14px/1.5 system-ui, sans-serif;
}
main { max-width: 1050px; margin: auto; }
h1 { margin-bottom: 4px; font-size: 27px; }
p { color: var(--muted); }
a { color: var(--accent); }
.panel {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 12px; padding: 20px; margin-top: 18px;
}
.stats {
  display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px; margin-top: 18px;
}
.stat {
  padding: 16px; border: 1px solid var(--border);
  border-radius: 10px; background: var(--panel);
}
.number { font-size: 25px; font-weight: 700; }
.label { color: var(--muted); font-size: 12px; }
.scroll { overflow-x: auto; padding-bottom: 12px; }
.calendar { min-width: 790px; }
.months {
  display: grid; grid-template-columns: repeat(53, 1fr);
  margin-left: 35px; height: 25px; color: var(--muted);
  font-size: 11px;
}
.month { white-space: nowrap; }
.graph { display: flex; gap: 8px; }
.weekdays {
  display: grid; grid-template-rows: repeat(7, 12px);
  gap: 4px; color: var(--muted); font-size: 10px;
}
.weeks {
  display: grid; grid-auto-flow: column;
  grid-auto-columns: 12px; grid-template-rows: repeat(7, 12px);
  gap: 4px;
}
.day {
  width: 12px; height: 12px; border-radius: 3px;
  border: 1px solid #ffffff0c;
}
.day:hover, .day:focus {
  outline: 2px solid var(--text); outline-offset: 1px;
}
.legend {
  display: flex; align-items: center; gap: 5px;
  justify-content: flex-end; color: var(--muted);
  font-size: 11px; margin-top: 16px;
}
.legend .day { display: inline-block; }
@media (max-width: 500px) {
  body { padding: 18px 10px; }
  .panel { padding: 14px; }
  .stats { gap: 7px; }
  .stat { padding: 10px; }
  .number { font-size: 20px; }
}
</style>
</head>
<body>
<main>
  <h1>A Year of Building <span style="color:#58a6ff">.</span></h1>
  <p>GitHub contribution activity for
    <a href="https://github.com/USERNAME">USERNAME</a>
  </p>
  <section class="stats">
    <div class="stat"><div class="number" id="total">—</div>
      <div class="label">Contributions in the last year</div></div>
    <div class="stat"><div class="number" id="active">—</div>
      <div class="label">Active days</div></div>
    <div class="stat"><div class="number" id="streak">—</div>
      <div class="label">Longest streak (days)</div></div>
  </section>
  <section class="panel">
    <h2 style="font-size:17px;margin-top:0">Contribution calendar</h2>
    <p id="period"></p>
    <div class="scroll">
      <div class="calendar">
        <div class="months" id="months"></div>
        <div class="graph">
          <div class="weekdays">
            <span></span><span>Mon</span><span></span>
            <span>Wed</span><span></span><span>Fri</span><span></span>
          </div>
          <div class="weeks" id="weeks"></div>
        </div>
      </div>
    </div>
    <div class="legend">
      Less
      <span class="day" style="background:#161b22"></span>
      <span class="day" style="background:#0e4429"></span>
      <span class="day" style="background:#006d32"></span>
      <span class="day" style="background:#26a641"></span>
      <span class="day" style="background:#39d353"></span>
      More
    </div>
  </section>
  <p><a href="https://github.com/USERNAME">View GitHub profile →</a></p>
</main>
<script>
const DATA = __DATA__;
document.getElementById("total").textContent =
  DATA.total.toLocaleString();
document.getElementById("active").textContent = DATA.activeDays;
document.getElementById("streak").textContent = DATA.longestStreak;
document.getElementById("period").textContent =
  DATA.start + " — " + DATA.end;

const map = new Map(DATA.days.map(d => [d.date, d]));
const first = new Date(DATA.start + "T12:00:00Z");
const last = new Date(DATA.end + "T12:00:00Z");
const mondayOffset = (first.getUTCDay() + 6) % 7;
first.setUTCDate(first.getUTCDate() - mondayOffset);

const weeks = document.getElementById("weeks");
const months = document.getElementById("months");
let previousMonth = "";

for (let d = new Date(first); d <= last; d.setUTCDate(d.getUTCDate() + 1)) {
  const key = d.toISOString().slice(0, 10);
  const item = map.get(key);
  const col = Math.floor((d - first) / (7 * 86400000));

  if (d.getUTCDate() <= 7) {
    const label = document.createElement("span");
    label.className = "month";
    label.style.gridColumn = String(col + 1);
    label.textContent = d.toLocaleString("en", {
      month: "short", timeZone: "UTC"
    });
    if (key.slice(0, 7) !== previousMonth) months.appendChild(label);
    previousMonth = key.slice(0, 7);
  }

  const cell = document.createElement("span");
  cell.className = "day";
  cell.style.gridColumn = String(col + 1);
  cell.style.gridRow = String(((d.getUTCDay() + 6) % 7) + 1);

  if (item) {
    cell.style.background = item.color || "#161b22";
    const count = item.contributionCount;
    cell.title = `${count} contribution${count === 1 ? "" : "s"} on ${key}`;
    cell.setAttribute("aria-label", cell.title);
    cell.tabIndex = 0;
  } else {
    cell.style.visibility = "hidden";
  }
  weeks.appendChild(cell);
}
</script>
</body>
</html>
"""

page = page.replace("USERNAME", USERNAME)
page = page.replace("__DATA__", data)

Path("dist").mkdir(exist_ok=True)
Path("dist/index.html").write_text(page, encoding="utf-8")
print("Interactive HTML contribution calendar generated.")


# Generate SVG for the GitHub profile README
from xml.sax.saxutils import escape

svg_width = 900
cell_size = 11
gap = 4
step = cell_size + gap
left = 40
top = 30
svg_height = 150

first_day = date.fromisoformat(days[0]["date"])
monday_offset = first_day.weekday()

# Position each contribution day in a Monday-first calendar
calendar_start = first_day - timedelta(days=monday_offset)

svg_parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'viewBox="0 0 {svg_width} {svg_height}" '
    f'width="100%" role="img" '
    f'aria-label="GitHub contribution calendar">',
    '<rect width="100%" height="100%" rx="8" fill="#0d1117"/>',
    '<text x="10" y="18" fill="#e6edf3" '
    'font-size="12" font-family="Arial, sans-serif">'
    f'{calendar["totalContributions"]:,} contributions in the last year'
    '</text>',
]

day_map = {item["date"]: item for item in days}

# Month labels
seen_months = set()

for item in days:
    day_date = date.fromisoformat(item["date"])
    col = (day_date - calendar_start).days // 7

    month_key = day_date.strftime("%Y-%m")
    if day_date.day <= 7 and month_key not in seen_months:
        x = left + col * step
        svg_parts.append(
            f'<text x="{x}" y="45" fill="#8b949e" '
            f'font-size="10" font-family="Arial, sans-serif">'
            f'{escape(day_date.strftime("%b"))}</text>'
        )
        seen_months.add(month_key)

# Contribution squares with hover tooltips
for item in days:
    day_date = date.fromisoformat(item["date"])
    offset = (day_date - calendar_start).days
    col = offset // 7
    row = offset % 7

    x = left + col * step
    y = top + row * step
    count = item["contributionCount"]
    color = item.get("color") or "#161b22"

    tooltip = escape(
        f'{count} contribution{"s" if count != 1 else ""} on {item["date"]}',
        {'"': "&quot;"}
    )

    svg_parts.append(
        f'<rect x="{x}" y="{y}" width="{cell_size}" '
        f'height="{cell_size}" rx="2" fill="{color}">'
        f'<title>{tooltip}</title>'
        '</rect>'
    )

svg_parts.append("</svg>")

Path("dist/contribution-calendar.svg").write_text(
    "\n".join(svg_parts),
    encoding="utf-8"
)

print("Interactive HTML and README SVG calendars generated.")

