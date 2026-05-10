import os, requests, glob

API = os.environ["WIKI_API_URL"]
USER = os.environ["WIKI_USERNAME"]
PASS = os.environ["WIKI_PASSWORD"]

session = requests.Session()
session.headers.update({
    "User-Agent": "CreateAeronauticsAddonSync/1.0 (GitHub Actions bot)"
})

def login():
    r = session.post(API, data={"action":"query","meta":"tokens","type":"login","format":"json"})
    data = r.json()
    token = data["query"]["tokens"]["logintoken"]
    result = session.post(API, data={
        "action":"login","lgname":USER,"lgpassword":PASS,
        "lgtoken":token,"format":"json"
    }).json()
    print("Login result:", result.get("login", {}).get("result"))

def get_csrf():
    r = session.get(API, params={"action":"query","meta":"tokens","format":"json"}).json()
    return r["query"]["tokens"]["csrftoken"]

def edit_page(title, content, token):
    r = session.post(API, data={
        "action":"edit","title":title,"text":content,
        "token":token,"format":"json","bot":"true"
    }).json()
    print(f"Edit '{title}':", r.get("edit", {}).get("result", r))

def upload_image(filepath, filename, token):
    with open(filepath, "rb") as f:
        r = session.post(API, files={"file": (filename, f)}, data={
            "action":"upload","filename":filename,
            "token":token,"format":"json","ignorewarnings":"true"
        }).json()
    print(f"Upload '{filename}':", r.get("upload", {}).get("result", r))

def parse_txt(path):
    data = {"Name":"","Description":"","Adds":[]}
    current = None
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("Name:"):
                data["Name"] = line[5:].strip()
            elif line.startswith("Description:"):
                data["Description"] = line[12:].strip()
            elif line.startswith("Adds:"):
                current = "Adds"
            elif current == "Adds" and line.startswith("-"):
                data["Adds"].append(line[1:].strip())
    return data

login()
token = get_csrf()

addons = []

for txt_path in glob.glob("*/*.txt"):
    folder = os.path.dirname(txt_path)
    data = parse_txt(txt_path)
    if not data["Name"]:
        continue

    img_filename = None
    for ext in ["png","jpg","jpeg","gif","webp"]:
        img_path = f"{folder}/{folder}.{ext}"
        if os.path.exists(img_path):
            img_filename = f"{folder}.{ext}"
            upload_image(img_path, img_filename, token)
            break

    addons.append((data, img_filename))

addons.sort(key=lambda x: x[0]["Name"].lower())

lines = [
    "== Create: Aeronautics Addons ==",
    "",
    "----",
    "",
]

for data, img_filename in addons:
    name = data["Name"]
    desc = data["Description"]
    adds = data["Adds"]

    img_wikitext = f"[[File:{img_filename}|80px]]" if img_filename else ""

    adds_wikitext = ""
    if adds:
        adds_wikitext = "\n;What it adds:\n" + "\n".join(f"* {i}" for i in adds)

    block = f"""\
<div class="addon-block" data-name="{name.lower()}">
{{| class="wikitable mw-collapsible mw-collapsed" style="width:100%"
! style="text-align:left;" | {img_wikitext} {name}
|-
|
{desc}
{adds_wikitext}
|}}
</div>

"""
    lines.append(block)

index_text = "\n".join(lines)
edit_page("Create:Aeronautics Addons", index_text, token)
print("Done.")
