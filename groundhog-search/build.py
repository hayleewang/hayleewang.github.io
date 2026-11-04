"""Builds index.html from template.html + the predictions CSV.
Usage: python3 build.py [path/to/predictions.csv]
(Downloads the CSV from the tutorial URL if no path is given.)"""
import csv, io, json, re, sys, urllib.request, pathlib, collections

URL = "https://the-art-of-data-journalism.github.io/tutorial-data/groundhogs/predictions.csv"
here = pathlib.Path(__file__).parent

if len(sys.argv) > 1:
    text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
else:
    text = urllib.request.urlopen(URL).read().decode("utf-8")

# order matters: first match wins
CREATURES = [
    ("Groundhog", r"groundhog"),
    ("Prairie dog", r"prairie dog"),
    ("Marmot", r"marmot"),
    ("Gopher", r"gopher"),
    ("Armadillo", r"armadillo"),
    ("Tortoise", r"tortoise"),
    ("Opossum", r"opossum"),
    ("Bullfrog", r"frog"),
    ("Fish", r"bass"),
    ("Duck", r"duck"),
    ("Alligator", r"alligator"),
    ("Cat", r"\bcat\b"),
    ("Owl", r"\bowl\b"),
    ("Beaver", r"beaver"),
    ("Squirrel", r"squirrel"),
    ("Hedgehog", r"hedgehog"),
    ("Lobster", r"lobster"),
    ("Chicken", r"chicken"),
    ("Flamingo", r"flamingo"),
]
def creature(t):
    for name, rx in CREATURES:
        if re.search(rx, t, re.I):
            return name
    return "Other"

preds = collections.OrderedDict()
for r in csv.DictReader(io.StringIO(text)):
    p = preds.setdefault(r["id"], {
        "id": int(r["id"]), "slug": r["slug"], "name": r["name"], "short": r["shortname"],
        "city": r["city"], "region": r["region"], "country": r["country"],
        "type": r["type"], "creature": creature(r["type"] + " " + r["name"]),
        "active": r["active"] == "1", "successor": r["successor"],
        "desc": r["description"], "img": r["image"], "source": r["source"], "y": {},
    })
    p["y"][r["year"]] = {"0": 0, "1": 1}.get(r["shadow"], -1)  # -1 = no usable record

data = list(preds.values())
print(len(data), "predictors")
print(collections.Counter((d["creature"]) for d in data))
for d in data:
    if d["creature"] == "Other": print("  other:", d["name"], "|", d["type"])

payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
tpl = (here / "template.html").read_text(encoding="utf-8")
(here / "index.html").write_text(tpl.replace("/*__DATA__*/[]", payload), encoding="utf-8")
print("wrote index.html")
