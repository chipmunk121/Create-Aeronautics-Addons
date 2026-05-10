import os, requests, glob

API = os.environ["WIKI_API_URL"]
USER = os.environ["WIKI_USERNAME"]
PASS = os.environ["WIKI_PASSWORD"]

session = requests.Session()

# --- Login ---
def login():
    r = session.post(API, data={"action":"query","meta":"tokens","type":"login","format":"json"}).json()
    token = r["query"]["tokens"]["logintoken"]
    session.post(API, data={
        "action":"login","lgname":USER,"lgpassword":PASS,
        "lgtoken":token,"format":"json"
    })

def get_csrf():
    r = session.get(API, params={"action":"query","meta":"tokens","format":"json"}).json()
    return r["query"]["tokens"]["csrftoken"]

def edit_page(title, content, token):
    session.post(API, data={
        "action":"edit","title":title,"text":content,
        "token":token,"format":"json","bot":"true"
    })

def upload_image(filepath, filename, token):
    with open(filepath, "rb") as f:
        session.post(API, files={"file": (filename, f)}, data={
            "action":"upload","filename":filename,
            "token":token,"format":"json","ignorewarnings":"true"
        })

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

def make_wikitext(d, folder):
    # Find image
    img_line = ""
    for ext in ["png","jpg","jpeg","gif","webp"]:
        img = f"{folder}/{folder}.{ext}"
        if os.path.exists(img):
            img_line = f"[[File:{folder}.{ext}|200px|right|{d['Name']} logo]]"
            break

    adds_section = ""
    if d["Adds"]:
        items = "\n".join(f"* {i}" for i in d["Adds"])
        adds_section = f"\n== Adds ==\n{items}\n"

    return f"""{img_line}
== {d['Name']} ==
{d['Description']}
{adds_section}
[[Category:Create Aeronautics Addons]]
"""

login()
token = get_csrf()

# Build the addon index list for the search/index page
addon_names = []

for txt_path in glob.glob("*/*.txt"):
    folder = os.path.dirname(txt_path)
    data = parse_txt(txt_path)
    if not data["Name"]:
        continue

    addon_names.append((data["Name"], folder))

    # Upload image if present
    for ext in ["png","jpg","jpeg","gif","webp"]:
        img_path = f"{folder}/{folder}.{ext}"
        if os.path.exists(img_path):
            upload_image(img_path, f"{folder}.{ext}", token)
            break

    wikitext = make_wikitext(data, folder)
    page_title = f"Addon:{data['Name'].replace(' ', '_')}"
    edit_page(page_title, wikitext, token)
    print(f"Updated: {page_title}")

# Update the index page (used for search)
index_lines = ["== Create: Aeronautics Addons ==",
               "Use the search box below to filter by addon name.",
               "",
               '<div id="addon-search-box">',
               '<inputbox>',
               'type=search',
               'namespaces=Addon',
               'placeholder=Search addons...',
               '</inputbox>',
               '</div>',
               "",
               "=== All Addons ==="]

for name, folder in sorted(addon_names):
    index_lines.append(f"* [[Addon:{name.replace(' ','_')}|{name}]]")

index_text = "\n".join(index_lines)
edit_page("Create:Aeronautics Addons", index_text, token)
print("Updated index page.")
