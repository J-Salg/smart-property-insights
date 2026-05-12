import urllib.request
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "app", "static", "js")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# GLTFLoader: try versions in order until one succeeds
GLTF_CANDIDATES = [
    "https://raw.githubusercontent.com/mrdoob/three.js/r148/examples/js/loaders/GLTFLoader.js",
    "https://raw.githubusercontent.com/mrdoob/three.js/r147/examples/js/loaders/GLTFLoader.js",
    "https://raw.githubusercontent.com/mrdoob/three.js/r140/examples/js/loaders/GLTFLoader.js",
    "https://raw.githubusercontent.com/mrdoob/three.js/r132/examples/js/loaders/GLTFLoader.js",
]

FILES = {
    "three.min.js": (
        "https://raw.githubusercontent.com/mrdoob/three.js/r155/build/three.min.js"
    ),
}

def fetch(url, dest):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as r, open(dest, "wb") as f:  
        f.write(r.read())

for filename, url in FILES.items():
    dest = os.path.join(BASE, filename)
    print(f"  Downloading {filename} ...", end=" ", flush=True)
    fetch(url, dest)
    print(f"{os.path.getsize(dest) // 1024} KB")

dest = os.path.join(BASE, "GLTFLoader.js")
print(f"  Downloading GLTFLoader.js ...", end=" ", flush=True)
downloaded = False
for url in GLTF_CANDIDATES:
    try:
        fetch(url, dest)
        downloaded = True
        print(f"{os.path.getsize(dest) // 1024} KB  (from {url.split('/r')[1].split('/')[0]})")
        break
    except Exception:  
        continue
if not downloaded:
    print("FAILED — no candidate URL succeeded.")

print("\nDone.")
