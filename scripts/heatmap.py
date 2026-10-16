import json, os, urllib.request

USER = os.environ.get("GH_USER", "AreebAbdulGhani76")
TOKEN = os.environ["GITHUB_TOKEN"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
data = json.load(urllib.request.urlopen(req))
weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

CELL, GAP, PAD = 11, 3, 4
palette = ["#1E293B", "#4C1D95", "#6D28D9", "#A855F7", "#E9D5FF"]
max_count = max((d["contributionCount"] for w in weeks for d in w["contributionDays"]), default=0)

def level(c):
    if c == 0: return 0
    if max_count <= 4: return min(4, c)
    return min(4, 1 + int(c / max_count * 3.99))

cols = len(weeks)
width = PAD * 2 + cols * (CELL + GAP)
height = PAD * 2 + 7 * (CELL + GAP)
rects = []
for x, w in enumerate(weeks):
    for y, d in enumerate(w["contributionDays"]):
        color = palette[level(d["contributionCount"])]
        rects.append(
            f'<rect x="{PAD + x*(CELL+GAP)}" y="{PAD + y*(CELL+GAP)}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"><title>{d["date"]}: {d["contributionCount"]} contributions</title></rect>'
        )

os.makedirs("assets", exist_ok=True)
with open("assets/heatmap.svg", "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n' + "\n".join(rects) + "\n</svg>\n")
print("heatmap written")
