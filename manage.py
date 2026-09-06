#!/usr/bin/env python3
"""
manage.py — a small interactive helper for the portfolio repo.

Run it from inside your project folder (same place as package.json):

    python manage.py

It gives you a menu to:
  1. Add a new CFD project
  2. Add a new story (video / photo / writing)
  3. Attach images to an existing project or story
  4. Publish changes (git add + commit + push)
  5. Start the local dev server (npm run dev)

No extra installs needed — this only uses Python's built-in libraries.
"""

import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECTS_DIR = ROOT / "src" / "content" / "projects"
STORIES_DIR = ROOT / "src" / "content" / "stories"


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or default


def ask_list(prompt: str) -> list[str]:
    raw = input(f"{prompt} (comma-separated, e.g. OpenFOAM, Python, Bash): ").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def run(cmd: list[str], cwd: Path = ROOT) -> bool:
    """Run a shell command, streaming output. Returns True on success."""
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode == 0


def check_repo():
    if not (ROOT / ".git").exists():
        print(
            "\n⚠️  No .git folder found here. Run 'git init' and connect your "
            "GitHub remote first (see the README) before publishing.\n"
        )
        return False
    return True


# --------------------------------------------------------------------------
# 1. add a new CFD project
# --------------------------------------------------------------------------

def add_project():
    print("\n--- New CFD project ---")
    title = ask("Title (e.g. 'Vortex Shedding Behind a Cylinder')")
    if not title:
        print("Title is required, cancelling.")
        return

    slug = slugify(ask("File name / URL slug", slugify(title)))
    filepath = PROJECTS_DIR / f"{slug}.mdx"
    if filepath.exists():
        print(f"A project already exists at {filepath.relative_to(ROOT)} — pick a different slug.")
        return

    summary = ask("One-sentence summary")
    stack = ask_list("Tech stack")
    tags = ask_list("Tags")
    solver = ask("Solver (e.g. simpleFoam) — optional")
    status = ask("Status: ongoing / complete / archived", "ongoing")
    featured = ask("Feature on homepage? (y/n)", "n").lower().startswith("y")

    images_dir = PROJECTS_DIR / "images" / slug
    images_dir.mkdir(parents=True, exist_ok=True)

    def yaml_list(items):
        if not items:
            return "[]"
        return "[" + ", ".join(f'"{i}"' for i in items) + "]"

    frontmatter = f"""---
title: "{title}"
summary: "{summary}"
stack: {yaml_list(stack)}
tags: {yaml_list(tags)}
{f'solver: "{solver}"' if solver else '# solver: ""'}
status: "{status if status in ("ongoing", "complete", "archived") else "ongoing"}"
date: {date.today().isoformat()}
metrics: []
featured: {"true" if featured else "false"}
order: 99
# coverImage: "./images/{slug}/cover.png"
# gallery:
#   - "./images/{slug}/1.png"
#   - "./images/{slug}/2.png"
---

## Methodology

Write your methodology here. Use `$$ ... $$` for a display equation, e.g.

$$
y^+ = \\frac{{u_\\tau y}}{{\\nu}}
$$

or `$...$` for inline math like $Re = 4.2 \\times 10^5$.

## Results

...
"""
    filepath.write_text(frontmatter, encoding="utf-8")
    print(f"\n✅ Created {filepath.relative_to(ROOT)}")
    print(f"   Image folder ready at {images_dir.relative_to(ROOT)} — use option 3 to add photos.")
    print("   Uncomment coverImage/gallery lines in the file once images are added.")


# --------------------------------------------------------------------------
# 2. add a new story
# --------------------------------------------------------------------------

def add_story():
    print("\n--- New story (video / photo / writing) ---")
    title = ask("Title")
    if not title:
        print("Title is required, cancelling.")
        return

    slug = slugify(ask("File name / slug", slugify(title)))
    filepath = STORIES_DIR / f"{slug}.mdx"
    if filepath.exists():
        print(f"A story already exists at {filepath.relative_to(ROOT)} — pick a different slug.")
        return

    kind = ask("Kind: video / photo / writing", "video")
    summary = ask("One-sentence summary")
    tags = ask_list("Tags")

    youtube_line = ""
    if kind == "video":
        video_id = ask("YouTube video ID (the part after v= in the URL)")
        youtube_line = f'youtubeId: "{video_id}"\n'

    images_dir = STORIES_DIR / "images" / slug
    if kind == "photo":
        images_dir.mkdir(parents=True, exist_ok=True)

    def yaml_list(items):
        if not items:
            return "[]"
        return "[" + ", ".join(f'"{i}"' for i in items) + "]"

    frontmatter = f"""---
title: "{title}"
kind: "{kind if kind in ("video", "photo", "writing") else "writing"}"
summary: "{summary}"
date: {date.today().isoformat()}
{youtube_line}tags: {yaml_list(tags)}
{f'# gallery:\n#   - "./images/{slug}/1.png"' if kind == "photo" else ""}
---

Write the story text here.
"""
    filepath.write_text(frontmatter, encoding="utf-8")
    print(f"\n✅ Created {filepath.relative_to(ROOT)}")
    if kind == "photo":
        print(f"   Image folder ready at {images_dir.relative_to(ROOT)} — use option 3 to add photos.")


# --------------------------------------------------------------------------
# 3. attach images to an existing project or story
# --------------------------------------------------------------------------

def list_entries(directory: Path) -> list[Path]:
    return sorted(p for p in directory.glob("*.mdx"))


def attach_images():
    print("\n--- Attach images ---")
    print("1. Project")
    print("2. Story")
    choice = ask("Which one?", "1")
    directory = PROJECTS_DIR if choice == "1" else STORIES_DIR

    entries = list_entries(directory)
    if not entries:
        print("No entries found yet — create one first (option 1 or 2 in the main menu).")
        return

    print("\nExisting entries:")
    for i, e in enumerate(entries, 1):
        print(f"  {i}. {e.stem}")
    idx = ask("Pick a number", "1")
    try:
        entry = entries[int(idx) - 1]
    except (ValueError, IndexError):
        print("Not a valid choice.")
        return

    slug = entry.stem
    images_dir = directory / "images" / slug
    images_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"\nDrag and drop image files into: {images_dir}\n"
        "or paste full file paths below one at a time (blank line to finish)."
    )

    copied = []
    while True:
        src = input("Image path (or Enter to stop): ").strip('" ').strip()
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
            f"\nNow open {entry.relative_to(ROOT)} and set (or uncomment):\n"
            f'  coverImage: "./images/{slug}/{copied[0]}"\n'
            "  gallery:\n"
            + "\n".join(f'    - "./images/{slug}/{name}"' for name in copied)
        )
    else:
        print("No images were copied.")


# --------------------------------------------------------------------------
# 4. publish (git add / commit / push)
# --------------------------------------------------------------------------

def publish():
    print("\n--- Publish changes ---")
    if not check_repo():
        return

    # show what changed, so it's not a total black box
    run(["git", "status", "--short"])

    proceed = ask("\nAdd and commit all changes above? (y/n)", "y")
    if not proceed.lower().startswith("y"):
        print("Cancelled.")
        return

    message = ask("Commit message", "Update portfolio content")

    if not run(["git", "add", "."]):
        print("git add failed — see the error above.")
        return
    if not run(["git", "commit", "-m", message]):
        print(
            "Nothing to commit, or commit failed — if it says 'nothing to commit', "
            "there were no changes to publish."
        )
        return
    if not run(["git", "push"]):
        print(
            "\n⚠️  git push failed. Common causes: no internet, not logged into "
            "GitHub, or remote not set up yet (see the README's Step 4)."
        )
        return

    print("\n✅ Pushed. Vercel will redeploy automatically in ~1 minute.")


# --------------------------------------------------------------------------
# 5. run dev server
# --------------------------------------------------------------------------

def run_dev():
    print("\nStarting local dev server — press Ctrl+C to stop it.\n")
    npm_cmd = "npm.cmd" if sys.platform.startswith("win") else "npm"
    try:
        subprocess.run([npm_cmd, "run", "dev"], cwd=ROOT)
    except FileNotFoundError:
        print("Could not find npm — make sure Node.js is installed and restart your terminal.")
    except KeyboardInterrupt:
        pass


# --------------------------------------------------------------------------
# main menu
# --------------------------------------------------------------------------

def main():
    if not PROJECTS_DIR.exists() or not STORIES_DIR.exists():
        print(
            "⚠️  Couldn't find src/content/projects or src/content/stories.\n"
            "   Make sure manage.py sits in the same folder as package.json."
        )
        return

    while True:
        print(
            "\n========== Portfolio Manager ==========\n"
            "1. Add a new CFD project\n"
            "2. Add a new story (video / photo / writing)\n"
            "3. Attach images to an existing project or story\n"
            "4. Publish changes (git add + commit + push)\n"
            "5. Start local dev server (npm run dev)\n"
            "6. Exit\n"
        )
        choice = ask("Choose an option", "6")

        if choice == "1":
            add_project()
        elif choice == "2":
            add_story()
        elif choice == "3":
            attach_images()
        elif choice == "4":
            publish()
        elif choice == "5":
            run_dev()
        elif choice == "6":
            print("Bye!")
            break
        else:
            print("Not a valid option, try again.")


if __name__ == "__main__":
    main()