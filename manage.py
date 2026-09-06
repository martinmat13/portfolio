#!/usr/bin/env python3
"""
manage.py — advanced interactive helper for the portfolio repo.

Run it from inside your project folder (same place as package.json):

    python manage.py

Everything destructive (edit / delete / style changes) makes a timestamped
backup in .manage_backups/ first, and content is validated before every
publish, so a bad edit is always recoverable and shouldn't break your
live site.

Only uses Python's built-in libraries — nothing extra to install.
"""

import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECTS_DIR = ROOT / "src" / "content" / "projects"
STORIES_DIR = ROOT / "src" / "content" / "stories"
COLLABS_DIR = ROOT / "src" / "content" / "collaborations"
BACKUPS_DIR = ROOT / ".manage_backups"
TAILWIND_CONFIG = ROOT / "tailwind.config.mjs"
GLOBAL_CSS = ROOT / "src" / "styles" / "global.css"
HERO_FILE = ROOT / "src" / "components" / "Hero.astro"

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ==========================================================================
# generic helpers
# ==========================================================================

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or default


def ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    default = "y" if default_yes else "n"
    val = ask(f"{prompt} (y/n)", default).lower()
    return val.startswith("y")


def ask_list(prompt: str, current: list = None) -> list:
    hint = f" (currently: {', '.join(current)})" if current else ""
    raw = input(f"{prompt}{hint} — comma-separated, blank to keep: ").strip()
    if not raw:
        return current or []
    return [item.strip() for item in raw.split(",") if item.strip()]


def run(cmd: list, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, capture_output=False)


def backup_file(path: Path):
    """Copy a file into .manage_backups/ with a timestamp before we touch it."""
    if not path.exists():
        return
    BACKUPS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUPS_DIR / f"{stamp}__{path.name}"
    shutil.copy2(path, dest)
    print(f"   (backup saved: {dest.relative_to(ROOT)})")


def check_repo() -> bool:
    if not (ROOT / ".git").exists():
        print("\n⚠️  No .git folder found here — set up GitHub first (see README) before publishing.\n")
        return False
    return True


# ==========================================================================
# frontmatter parsing / serialising
# Deliberately hand-rolled (not a YAML library) so nothing extra needs
# installing, and tuned specifically to the format this project's own
# schema (src/content/config.ts) and this script produce.
# ==========================================================================

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.S)


def parse_entry(path: Path):
    """Returns (frontmatter_dict, body_text) for an .mdx file."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"{path.name}: couldn't find a --- frontmatter block")
    yaml_block, body = m.group(1), m.group(2)
    data = {}
    lines = yaml_block.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        km = re.match(r"^(\w+):\s*(.*)$", line)
        if not km:
            i += 1
            continue
        key, rest = km.group(1), km.group(2).strip()

        if rest == "":
            items = []
            j = i + 1
            while j < len(lines) and re.match(r"^\s*-\s", lines[j]):
                item = lines[j].strip()[1:].strip()
                if item.startswith("{"):
                    d = {}
                    for k, v in re.findall(r'(\w+):\s*"([^"]*)"', item):
                        d[k] = v
                    items.append(d)
                else:
                    items.append(item.strip('"'))
                j += 1
            data[key] = items
            i = j
            continue

        if rest.startswith("["):
            items = re.findall(r'"([^"]*)"', rest)
            data[key] = items
            i += 1
            continue

        if rest.startswith('"'):
            data[key] = rest.strip('"')
            i += 1
            continue

        if rest in ("true", "false"):
            data[key] = rest == "true"
            i += 1
            continue

        try:
            data[key] = int(rest)
        except ValueError:
            try:
                data[key] = float(rest)
            except ValueError:
                data[key] = rest  # e.g. bare date 2026-01-01
        i += 1

    return data, body


def yaml_str(v) -> str:
    return f'"{v}"'


def yaml_inline_list(items) -> str:
    return "[" + ", ".join(yaml_str(i) for i in items) + "]"


PROJECT_FIELDS = [
    ("title", "str"), ("summary", "str"), ("stack", "list"), ("tags", "list"),
    ("solver", "str_opt"), ("status", "str"), ("date", "date"),
    ("metrics", "dictlist"), ("coverImage", "str_opt"), ("gallery", "list_opt"),
    ("repoUrl", "str_opt"), ("paperUrl", "str_opt"), ("featured", "bool"), ("order", "int"),
]
STORY_FIELDS = [
    ("title", "str"), ("kind", "str"), ("summary", "str"), ("date", "date"),
    ("youtubeId", "str_opt"), ("coverImage", "str_opt"), ("gallery", "list_opt"), ("tags", "list"),
]
COLLAB_FIELDS = [
    ("title", "str"), ("partner", "str"), ("role", "str"), ("summary", "str"),
    ("period", "str"), ("tags", "list"), ("coverImage", "str_opt"), ("link", "str_opt"), ("order", "int"),
]

SPECS = {"projects": PROJECT_FIELDS, "stories": STORY_FIELDS, "collaborations": COLLAB_FIELDS}
DIRS = {"projects": PROJECTS_DIR, "stories": STORIES_DIR, "collaborations": COLLABS_DIR}


def serialize_entry(collection: str, data: dict, body: str) -> str:
    lines = ["---"]
    for key, kind in SPECS[collection]:
        val = data.get(key)
        if kind == "str":
            lines.append(f"{key}: {yaml_str(val or '')}")
        elif kind == "str_opt":
            if val:
                lines.append(f"{key}: {yaml_str(val)}")
            else:
                lines.append(f'# {key}: ""')
        elif kind == "list":
            lines.append(f"{key}: {yaml_inline_list(val or [])}")
        elif kind == "list_opt":
            if val:
                lines.append(f"{key}:")
                for item in val:
                    lines.append(f'  - "{item}"')
            else:
                lines.append(f"# {key}:")
                lines.append(f'#   - "./images/example/1.png"')
        elif kind == "bool":
            lines.append(f"{key}: {'true' if val else 'false'}")
        elif kind == "int":
            lines.append(f"{key}: {int(val) if val is not None else 99}")
        elif kind == "date":
            lines.append(f"{key}: {val}")
        elif kind == "dictlist":
            if val:
                lines.append(f"{key}:")
                for d in val:
                    inner = ", ".join(f'{k}: "{v}"' for k, v in d.items())
                    lines.append(f"  - {{ {inner} }}")
            else:
                lines.append(f"{key}: []")
    lines.append("---")
    return "\n".join(lines) + "\n" + body


# ==========================================================================
# validation
# ==========================================================================

def validate_data(collection: str, slug: str, path: Path, data: dict) -> list:
    errors = []

    def require(key):
        if not data.get(key):
            errors.append(f"missing required field '{key}'")

    if collection == "projects":
        for k in ("title", "summary", "stack", "status", "date"):
            require(k)
        if len(data.get("summary", "")) > 220:
            errors.append("summary is longer than 220 characters")
        if data.get("status") not in ("ongoing", "complete", "archived", None):
            errors.append(f"status '{data.get('status')}' must be ongoing / complete / archived")
        if not isinstance(data.get("stack", []), list) or not data.get("stack"):
            errors.append("stack should be a non-empty list, e.g. [\"OpenFOAM\", \"Python\"]")

    elif collection == "stories":
        for k in ("title", "kind", "summary", "date"):
            require(k)
        if data.get("kind") not in ("video", "photo", "writing", None):
            errors.append(f"kind '{data.get('kind')}' must be video / photo / writing")
        if data.get("kind") == "video" and not data.get("youtubeId"):
            errors.append("kind is 'video' but youtubeId is missing")
        if len(data.get("summary", "")) > 220:
            errors.append("summary is longer than 220 characters")

    elif collection == "collaborations":
        for k in ("title", "partner", "role", "summary", "period"):
            require(k)
        if len(data.get("summary", "")) > 240:
            errors.append("summary is longer than 240 characters")

    d = data.get("date")
    if d and not DATE_RE.match(str(d)):
        errors.append(f"date '{d}' should look like YYYY-MM-DD")

    for img_key in ("coverImage", "gallery"):
        val = data.get(img_key)
        if not val:
            continue
        paths = [val] if img_key == "coverImage" else val
        for rel in paths:
            resolved = (path.parent / rel).resolve()
            if not resolved.exists():
                errors.append(f"{img_key} points to '{rel}' but that file doesn't exist")

    link_keys = ["repoUrl", "paperUrl"] if collection == "projects" else (["link"] if collection == "collaborations" else [])
    for lk in link_keys:
        val = data.get(lk)
        if val and not (val.startswith("http://") or val.startswith("https://")):
            errors.append(f"{lk} should be a full URL starting with http(s)://")

    return errors


def validate_all(verbose: bool = True) -> bool:
    print("\n--- Validating all content ---")
    total_errors = 0
    for collection, directory in DIRS.items():
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.mdx")):
            slug = path.stem
            try:
                data, _ = parse_entry(path)
            except ValueError as e:
                print(f"❌ {path.relative_to(ROOT)}: {e}")
                total_errors += 1
                continue
            errors = validate_data(collection, slug, path, data)
            if errors:
                total_errors += len(errors)
                print(f"❌ {path.relative_to(ROOT)}")
                for e in errors:
                    print(f"     - {e}")
            elif verbose:
                print(f"✅ {path.relative_to(ROOT)}")

    if total_errors == 0:
        print("\nAll content passed validation. ✅")
        return True
    print(f"\n{total_errors} issue(s) found. Fix these before publishing to avoid a broken build.")
    return False


# ==========================================================================
# add new entries
# ==========================================================================

def add_project():
    print("\n--- New CFD project ---")
    title = ask("Title")
    if not title:
        print("Title is required, cancelling.")
        return
    slug = slugify(ask("File name / URL slug", slugify(title)))
    filepath = PROJECTS_DIR / f"{slug}.mdx"
    if filepath.exists():
        print("A project already exists with that slug — pick a different one.")
        return

    data = {
        "title": title,
        "summary": ask("One-sentence summary"),
        "stack": ask_list("Tech stack"),
        "tags": ask_list("Tags"),
        "solver": ask("Solver (optional)"),
        "status": ask("Status: ongoing / complete / archived", "ongoing"),
        "date": date.today().isoformat(),
        "metrics": [],
        "coverImage": "",
        "gallery": [],
        "repoUrl": "",
        "paperUrl": "",
        "featured": ask_yes_no("Feature on homepage?", False),
        "order": 99,
    }
    body = "\n## Methodology\n\nWrite your methodology here. Use `$$ ... $$` for a display equation, e.g.\n\n$$\ny^+ = \\frac{u_\\tau y}{\\nu}\n$$\n\n## Results\n\n...\n"
    errors = validate_data("projects", slug, filepath, data)
    if errors:
        print("\n⚠️  This entry has issues:")
        for e in errors:
            print(f"   - {e}")
        if not ask_yes_no("Save anyway?", False):
            print("Cancelled.")
            return
    filepath.write_text(serialize_entry("projects", data, body), encoding="utf-8")
    (PROJECTS_DIR / "images" / slug).mkdir(parents=True, exist_ok=True)
    print(f"\n✅ Created {filepath.relative_to(ROOT)}")


def add_story():
    print("\n--- New story ---")
    title = ask("Title")
    if not title:
        print("Title is required, cancelling.")
        return
    slug = slugify(ask("File name / slug", slugify(title)))
    filepath = STORIES_DIR / f"{slug}.mdx"
    if filepath.exists():
        print("A story already exists with that slug — pick a different one.")
        return

    kind = ask("Kind: video / photo / writing", "video")
    data = {
        "title": title,
        "kind": kind,
        "summary": ask("One-sentence summary"),
        "date": date.today().isoformat(),
        "youtubeId": ask("YouTube video ID") if kind == "video" else "",
        "coverImage": "",
        "gallery": [],
        "tags": ask_list("Tags"),
    }
    body = "\nWrite the story text here.\n"
    errors = validate_data("stories", slug, filepath, data)
    if errors:
        print("\n⚠️  This entry has issues:")
        for e in errors:
            print(f"   - {e}")
        if not ask_yes_no("Save anyway?", False):
            print("Cancelled.")
            return
    filepath.write_text(serialize_entry("stories", data, body), encoding="utf-8")
    if kind == "photo":
        (STORIES_DIR / "images" / slug).mkdir(parents=True, exist_ok=True)
    print(f"\n✅ Created {filepath.relative_to(ROOT)}")


def add_collaboration():
    print("\n--- New collaboration ---")
    title = ask("Title")
    if not title:
        print("Title is required, cancelling.")
        return
    slug = slugify(ask("File name / slug", slugify(title)))
    filepath = COLLABS_DIR / f"{slug}.mdx"
    if filepath.exists():
        print("A collaboration already exists with that slug — pick a different one.")
        return

    data = {
        "title": title,
        "partner": ask("Partner / institution name"),
        "role": ask("Your role"),
        "summary": ask("One-sentence summary"),
        "period": ask("Period (e.g. '2025 - present')"),
        "tags": ask_list("Tags"),
        "coverImage": "",
        "link": ask("Link (optional, full https:// URL)"),
        "order": 99,
    }
    body = "\nWrite more detail about this collaboration here.\n"
    errors = validate_data("collaborations", slug, filepath, data)
    if errors:
        print("\n⚠️  This entry has issues:")
        for e in errors:
            print(f"   - {e}")
        if not ask_yes_no("Save anyway?", False):
            print("Cancelled.")
            return
    filepath.write_text(serialize_entry("collaborations", data, body), encoding="utf-8")
    print(f"\n✅ Created {filepath.relative_to(ROOT)}")


# ==========================================================================
# list / choose an entry
# ==========================================================================

def choose_collection() -> str:
    print("\n1. Project\n2. Story\n3. Collaboration")
    choice = ask("Which kind?", "1")
    return {"1": "projects", "2": "stories", "3": "collaborations"}.get(choice, "projects")


def choose_entry(collection: str):
    directory = DIRS[collection]
    entries = sorted(directory.glob("*.mdx"))
    if not entries:
        print(f"No {collection} found yet.")
        return None
    print(f"\nExisting {collection}:")
    for i, e in enumerate(entries, 1):
        print(f"  {i}. {e.stem}")
    idx = ask("Pick a number", "")
    try:
        return entries[int(idx) - 1]
    except (ValueError, IndexError, TypeError):
        print("Not a valid choice.")
        return None


# ==========================================================================
# edit an existing entry
# ==========================================================================

def edit_entry():
    print("\n--- Edit an existing entry ---")
    collection = choose_collection()
    path = choose_entry(collection)
    if not path:
        return
    data, body = parse_entry(path)

    while True:
        fields = SPECS[collection]
        print(f"\nEditing {path.relative_to(ROOT)}:")
        for i, (key, kind) in enumerate(fields, 1):
            print(f"  {i}. {key} = {data.get(key)!r}")
        print(f"  {len(fields) + 1}. Done editing")

        choice = ask("Field number to edit", str(len(fields) + 1))
        try:
            choice_i = int(choice)
        except ValueError:
            print("Not a number.")
            continue
        if choice_i == len(fields) + 1:
            break
        if not (1 <= choice_i <= len(fields)):
            print("Out of range.")
            continue

        key, kind = fields[choice_i - 1]
        current = data.get(key)

        if kind in ("str", "str_opt"):
            data[key] = ask(f"New value for {key}", current or "")
        elif kind == "bool":
            data[key] = ask_yes_no(f"{key}?", bool(current))
        elif kind == "int":
            raw = ask(f"New value for {key}", str(current if current is not None else 99))
            try:
                data[key] = int(raw)
            except ValueError:
                print("Not a whole number, keeping old value.")
        elif kind == "date":
            raw = ask(f"New date (YYYY-MM-DD) for {key}", str(current or date.today().isoformat()))
            data[key] = raw
        elif kind == "list":
            data[key] = ask_list(f"New {key}", current or [])
        elif kind == "list_opt":
            raw = ask(
                f"New {key} as comma-separated relative paths (blank to clear)",
                ", ".join(current) if current else "",
            )
            data[key] = [x.strip() for x in raw.split(",") if x.strip()] if raw else []
        elif kind == "dictlist":
            print("Enter metrics as label:value pairs separated by commas, e.g. Re:4.2e5, Cells:2.1M")
            raw = ask("Metrics", "")
            if raw:
                items = []
                for pair in raw.split(","):
                    if ":" in pair:
                        label, value = pair.split(":", 1)
                        items.append({"label": label.strip(), "value": value.strip()})
                data[key] = items

    errors = validate_data(collection, path.stem, path, data)
    if errors:
        print("\n⚠️  This entry now has issues:")
        for e in errors:
            print(f"   - {e}")
        if not ask_yes_no("Save anyway?", False):
            print("Not saved.")
            return

    backup_file(path)
    path.write_text(serialize_entry(collection, data, body), encoding="utf-8")
    print(f"\n✅ Saved {path.relative_to(ROOT)}")
    print("   (Note: this only edits the frontmatter fields above — edit the")
    print("   prose body directly in VS Code if you need to change the text.)")


# ==========================================================================
# delete an existing entry
# ==========================================================================

def delete_entry():
    print("\n--- Delete an entry ---")
    collection = choose_collection()
    path = choose_entry(collection)
    if not path:
        return

    slug = path.stem
    print(f"\nYou're about to delete: {path.relative_to(ROOT)}")
    images_dir = DIRS[collection] / "images" / slug
    if images_dir.exists():
        print(f"This will also remove its image folder: {images_dir.relative_to(ROOT)} (backed up first)")

    confirm = ask(f"Type the slug '{slug}' to confirm deletion", "")
    if confirm != slug:
        print("Slug didn't match — cancelled, nothing deleted.")
        return

    backup_file(path)
    if images_dir.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        BACKUPS_DIR.mkdir(exist_ok=True)
        shutil.copytree(images_dir, BACKUPS_DIR / f"{stamp}__{slug}_images", dirs_exist_ok=True)
        shutil.rmtree(images_dir)

    path.unlink()
    print(f"\n🗑️  Deleted {path.relative_to(ROOT)} (backup kept in .manage_backups/)")


# ==========================================================================
# attach images
# ==========================================================================

def attach_images():
    print("\n--- Attach images ---")
    collection = choose_collection()
    if collection == "collaborations":
        print("(Collaborations only support a single coverImage — edit that field via option 4 instead.)")
    path = choose_entry(collection)
    if not path:
        return
    slug = path.stem
    images_dir = DIRS[collection] / "images" / slug
    images_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nDrag files into {images_dir} or paste full paths below (blank line to stop).")
    copied = []
    while True:
        src = input("Image path: ").strip('" ').strip()
        if not src:
            break
        src_path = Path(src)
        if not src_path.exists():
            print(f"  ⚠️  Not found: {src_path}")
            continue
        dest = images_dir / src_path.name
        shutil.copy2(src_path, dest)
        copied.append(dest.name)
        print(f"  ✅ Copied to {dest.relative_to(ROOT)}")

    if copied:
        print(
            f"\nNow use option 4 (Edit an existing entry) to set:\n"
            f"  coverImage → ./images/{slug}/{copied[0]}\n"
            f"  gallery    → " + ", ".join(f"./images/{slug}/{n}" for n in copied)
        )


# ==========================================================================
# visual style editor
# ==========================================================================

FONT_PRESETS = {
    "1": ("Space Grotesk", "Inter", "JetBrains Mono", "current default"),
    "2": ("Sora", "Manrope", "IBM Plex Mono", "softer geometric pairing"),
    "3": ("Archivo", "Source Sans 3", "Space Mono", "bolder, more brutalist display"),
}


def edit_colors():
    if not TAILWIND_CONFIG.exists():
        print("Couldn't find tailwind.config.mjs.")
        return
    text = TAILWIND_CONFIG.read_text(encoding="utf-8")

    # .*? with DOTALL so this also matches across the "// ... accent" comment
    # line that sits between the opening brace and DEFAULT in this file.
    flow_re = re.compile(r'flow:\s*\{.*?DEFAULT:\s*"(#[0-9A-Fa-f]{6})"', re.S)
    vortex_re = re.compile(r'vortex:\s*\{.*?DEFAULT:\s*"(#[0-9A-Fa-f]{6})"', re.S)

    flow_match = flow_re.search(text)
    current_flow = flow_match.group(1) if flow_match else "#00E5FF"

    print(f"\nCurrent primary accent (cyan): {current_flow}")
    new_flow = ask("New primary accent hex (blank to keep)", current_flow)

    vortex_match = vortex_re.search(text)
    current_vortex = vortex_match.group(1) if vortex_match else "#FF7A1A"
    print(f"Current secondary accent (orange): {current_vortex}")
    new_vortex = ask("New secondary accent hex (blank to keep)", current_vortex)

    for label, val in (("primary", new_flow), ("secondary", new_vortex)):
        if not HEX_RE.match(val):
            print(f"'{val}' isn't a valid hex color (expected format #RRGGBB) — aborting, nothing changed.")
            return

    if not flow_match or not vortex_match:
        print("Couldn't locate the color definitions in tailwind.config.mjs — aborting, nothing changed.")
        return

    backup_file(TAILWIND_CONFIG)
    new_text = text
    new_text = new_text[: flow_match.start(1)] + new_flow + new_text[flow_match.end(1):]
    vortex_match2 = vortex_re.search(new_text)
    new_text = new_text[: vortex_match2.start(1)] + new_vortex + new_text[vortex_match2.end(1):]

    TAILWIND_CONFIG.write_text(new_text, encoding="utf-8")
    print("\n✅ Updated colors. Run 'npm run dev' to preview before publishing.")


def edit_fonts():
    if not GLOBAL_CSS.exists() or not TAILWIND_CONFIG.exists():
        print("Couldn't find global.css or tailwind.config.mjs.")
        return

    print("\nFont pairings:")
    for key, (disp, body, mono, desc) in FONT_PRESETS.items():
        print(f"  {key}. {disp} / {body} / {mono} — {desc}")
    print("  4. Enter custom Google Font names")

    choice = ask("Pick one", "1")
    if choice in FONT_PRESETS:
        display_f, body_f, mono_f = FONT_PRESETS[choice][:3]
    else:
        display_f = ask("Display font (Google Fonts name)", "Space Grotesk")
        body_f = ask("Body font (Google Fonts name)", "Inter")
        mono_f = ask("Monospace font (Google Fonts name)", "JetBrains Mono")

    def family_param(name):
        return name.replace(" ", "+") + ":wght@400;500;600;700"

    import_url = (
        "https://fonts.googleapis.com/css2?family="
        + family_param(display_f) + "&family=" + family_param(body_f)
        + "&family=" + family_param(mono_f) + "&display=swap"
    )

    css_text = GLOBAL_CSS.read_text(encoding="utf-8")
    new_css, n = re.subn(
        r'@import url\("https://fonts\.googleapis\.com[^"]*"\);',
        f'@import url("{import_url}");',
        css_text,
        count=1,
    )
    if n == 0:
        print("Couldn't find the existing @import line in global.css — aborting, nothing changed.")
        return

    tw_text = TAILWIND_CONFIG.read_text(encoding="utf-8")
    new_tw, n2 = re.subn(
        r'fontFamily:\s*\{[^}]*\}',
        (
            "fontFamily: {\n"
            f'        display: ["{display_f}", "sans-serif"],\n'
            f'        body: ["{body_f}", "sans-serif"],\n'
            f'        mono: ["{mono_f}", "ui-monospace", "monospace"],\n'
            "      }"
        ),
        tw_text,
        count=1,
    )
    if n2 == 0:
        print("Couldn't find fontFamily block in tailwind.config.mjs — aborting, nothing changed.")
        return

    backup_file(GLOBAL_CSS)
    backup_file(TAILWIND_CONFIG)
    GLOBAL_CSS.write_text(new_css, encoding="utf-8")
    TAILWIND_CONFIG.write_text(new_tw, encoding="utf-8")
    print(f"\n✅ Fonts updated to {display_f} / {body_f} / {mono_f}. Run 'npm run dev' to preview.")


def edit_hero_animation():
    if not HERO_FILE.exists():
        print("Couldn't find src/components/Hero.astro.")
        return
    text = HERO_FILE.read_text(encoding="utf-8")

    count_match = re.search(r"const COUNT = (\d+);", text)
    speed_match = re.search(r"const speed = ([\d.]+);", text)
    current_count = count_match.group(1) if count_match else "260"
    current_speed = speed_match.group(1) if speed_match else "1.15"

    print(f"\nCurrent particle count: {current_count} (higher = denser, more CPU use)")
    print(f"Current particle speed: {current_speed}")

    new_count = ask("New particle count (50-800 recommended)", current_count)
    new_speed = ask("New particle speed (0.3-3 recommended)", current_speed)

    try:
        int(new_count)
        float(new_speed)
    except ValueError:
        print("Those need to be numbers — aborting, nothing changed.")
        return

    backup_file(HERO_FILE)
    new_text = text
    if count_match:
        new_text = re.sub(r"const COUNT = \d+;", f"const COUNT = {new_count};", new_text, count=1)
    if speed_match:
        new_text = re.sub(r"const speed = [\d.]+;", f"const speed = {new_speed};", new_text, count=1)
    HERO_FILE.write_text(new_text, encoding="utf-8")
    print("\n✅ Hero animation updated. Run 'npm run dev' to preview.")


def style_menu():
    while True:
        print(
            "\n--- Visual style editor ---\n"
            "1. Change accent colors (cyan / orange)\n"
            "2. Change fonts\n"
            "3. Adjust hero background animation (particle count / speed)\n"
            "4. Back to main menu"
        )
        choice = ask("Choose", "4")
        if choice == "1":
            edit_colors()
        elif choice == "2":
            edit_fonts()
        elif choice == "3":
            edit_hero_animation()
        elif choice == "4":
            break
        else:
            print("Not a valid option.")


# ==========================================================================
# publish
# ==========================================================================

def publish():
    print("\n--- Publish changes ---")
    if not check_repo():
        return

    if not validate_all(verbose=False):
        if not ask_yes_no("\nValidation found issues — publish anyway? (not recommended)", False):
            print("Cancelled — fix the issues above and try again.")
            return

    if ask_yes_no("\nRun a full production build check first? (recommended, takes ~30-60s)", True):
        npm_cmd = "npm.cmd" if sys.platform.startswith("win") else "npm"
        print("\nRunning build check...")
        result = subprocess.run([npm_cmd, "run", "build"], cwd=ROOT)
        if result.returncode != 0:
            print(
                "\n❌ Build failed — see the error above. This means Vercel would "
                "fail too. Fix the issue before publishing (a backup of anything "
                "you edited is in .manage_backups/ if you need to revert)."
            )
            return
        print("\n✅ Build check passed.")

    run(["git", "status", "--short"])
    if not ask_yes_no("\nAdd and commit all changes above?", True):
        print("Cancelled.")
        return

    message = ask("Commit message", "Update portfolio content")
    if run(["git", "add", "."]).returncode != 0:
        print("git add failed.")
        return
    commit_result = run(["git", "commit", "-m", message])
    if commit_result.returncode != 0:
        print("Nothing to commit, or commit failed — check the message above.")
        return
    if run(["git", "push"]).returncode != 0:
        print("\n⚠️  git push failed — check you're connected to the internet and logged into GitHub.")
        return

    print("\n✅ Pushed. Vercel will redeploy automatically in ~1 minute.")


def run_dev():
    print("\nStarting local dev server — press Ctrl+C to stop it.\n")
    npm_cmd = "npm.cmd" if sys.platform.startswith("win") else "npm"
    try:
        subprocess.run([npm_cmd, "run", "dev"], cwd=ROOT)
    except FileNotFoundError:
        print("Could not find npm — make sure Node.js is installed and restart your terminal.")
    except KeyboardInterrupt:
        pass


# ==========================================================================
# main menu
# ==========================================================================

def main():
    if not PROJECTS_DIR.exists():
        print(
            "⚠️  Couldn't find src/content/projects — make sure manage.py sits "
            "in the same folder as package.json."
        )
        return
    COLLABS_DIR.mkdir(parents=True, exist_ok=True)
    STORIES_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        print(
            "\n========== Portfolio Manager ==========\n"
            "1. Add a new CFD project\n"
            "2. Add a new story\n"
            "3. Add a new collaboration\n"
            "4. Edit an existing entry\n"
            "5. Delete an existing entry\n"
            "6. Attach images to an entry\n"
            "7. Edit site visuals (colors / fonts / hero animation)\n"
            "8. Validate all content\n"
            "9. Publish (validate + build check + git push)\n"
            "10. Start local dev server\n"
            "11. Exit\n"
        )
        choice = ask("Choose an option", "11")

        actions = {
            "1": add_project, "2": add_story, "3": add_collaboration,
            "4": edit_entry, "5": delete_entry, "6": attach_images,
            "7": style_menu, "8": validate_all, "9": publish, "10": run_dev,
        }
        if choice == "11":
            print("Bye!")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("Not a valid option, try again.")


if __name__ == "__main__":
    main()