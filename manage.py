#!/usr/bin/env python3
"""
manage.py — Advanced interactive CLI & Git Manager for the CFD portfolio.
"""

import os
import re
import shutil
import subprocess
import sys
import platform
from datetime import datetime, date
from pathlib import Path

# --------------------------------------------------------------------------
# Setup & Visuals
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
PROJECTS_DIR = ROOT / "src" / "content" / "projects"
STORIES_DIR = ROOT / "src" / "content" / "stories"

class Colors:
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_color(text: str, color: str, bold=False):
    style = f"{color}{Colors.BOLD}" if bold else color
    print(f"{style}{text}{Colors.RESET}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --------------------------------------------------------------------------
# Helpers & Validation
# --------------------------------------------------------------------------
def slugify(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")

def ask(prompt: str, default: str = "", required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        val = input(f"{Colors.CYAN}{prompt}{suffix}:{Colors.RESET} ").strip()
        if val: return val
        if default: return default
        if not required: return ""
        print_color(" ⚠️ This field is required.", Colors.RED)

def ask_list(prompt: str) -> list[str]:
    raw = input(f"{Colors.CYAN}{prompt} (comma-separated):{Colors.RESET} ").strip()
    return [item.strip() for item in raw.split(",") if item.strip()] if raw else []

def run(cmd: list[str], cwd: Path = ROOT, quiet: bool = False) -> bool:
    if not quiet:
        print_color(f"\n> {' '.join(cmd)}", Colors.MAGENTA)
    result = subprocess.run(cmd, cwd=cwd, capture_output=quiet, text=True)
    if quiet:
        return result.returncode == 0, result.stdout
    return result.returncode == 0

def check_dirs():
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    STORIES_DIR.mkdir(parents=True, exist_ok=True)

def select_entry(action_name: str) -> Path:
    print(f"\n{Colors.BOLD}--- {action_name} ---{Colors.RESET}")
    choice = ask("1. CFD Project \n2. Story/Blog\nChoose category", "1")
    
    directory = PROJECTS_DIR if choice == "1" else STORIES_DIR
    entries = sorted(p for p in directory.glob("*.mdx"))
    
    if not entries:
        print_color(" ⚠️ No entries found in this category.", Colors.YELLOW)
        return None

    print(f"\n{Colors.BOLD}Available entries:{Colors.RESET}")
    for i, e in enumerate(entries, 1):
        print(f"  {Colors.BLUE}{i}.{Colors.RESET} {e.stem}")
        
    idx = ask("Pick a number", "1")
    try:
        return entries[int(idx) - 1]
    except (ValueError, IndexError):
        print_color(" ⚠️ Invalid selection.", Colors.RED)
        return None

# --------------------------------------------------------------------------
# Advanced Features: Dashboard & Git Sync
# --------------------------------------------------------------------------
def show_dashboard():
    clear_screen()
    print_color(f"\n=== PORTFOLIO SYSTEM DASHBOARD ===", Colors.CYAN, bold=True)
    
    p_count = len(list(PROJECTS_DIR.glob("*.mdx")))
    s_count = len(list(STORIES_DIR.glob("*.mdx")))
    i_count = len(list(PROJECTS_DIR.rglob("*.png"))) + len(list(PROJECTS_DIR.rglob("*.jpg")))
    
    print(f" 📂 {Colors.BOLD}CFD Projects:{Colors.RESET} {p_count}")
    print(f" 📝 {Colors.BOLD}Stories/Blogs:{Colors.RESET} {s_count}")
    print(f" 🖼️  {Colors.BOLD}Total Images:{Colors.RESET}  {i_count}")
    
    # Check Git Status
    if (ROOT / ".git").exists():
        success, out = run(["git", "status", "--short"], quiet=True)
        changes = len(out.strip().split('\n')) if out.strip() else 0
        if changes > 0:
            print_color(f" 🔄 Pending Git Changes: {changes} uncommitted files", Colors.YELLOW)
        else:
            print_color(f" 🔄 Pending Git Changes: Up to date", Colors.GREEN)
    print("\n" + "="*34 + "\n")

def advanced_git_sync():
    print(f"\n{Colors.BOLD}--- Advanced Git Sync ---{Colors.RESET}")
    if not (ROOT / ".git").exists():
        print_color(" ⚠️ No .git repository found in this directory.", Colors.RED)
        return

    # 1. Check Status
    success, out = run(["git", "status", "--short"], quiet=True)
    if not out.strip():
        print_color(" ✅ Repository is completely up to date. Nothing to push.", Colors.GREEN)
        return
        
    print_color("Modified/Untracked files:", Colors.YELLOW)
    print(out)
    
    if ask("Stage ALL changes for commit? (y/n)", "y").lower() != 'y':
        print_color(" ❌ Sync aborted.", Colors.YELLOW)
        return
        
    if not run(["git", "add", "."]):
        print_color(" ⚠️ Failed to stage files.", Colors.RED)
        return

    # 2. Smart Commit Message
    default_msg = f"Content update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    msg = ask("Commit message", default_msg)
    
    if not run(["git", "commit", "-m", msg]):
        print_color(" ⚠️ Commit failed.", Colors.RED)
        return

    # 3. Safe Push (handles conflicts gracefully)
    print_color("Pushing to remote...", Colors.CYAN)
    if run(["git", "push"]):
        print_color("\n ✅ Success! Changes pushed. Live site will rebuild shortly.", Colors.GREEN, bold=True)
    else:
        print_color("\n ⚠️ Push failed! The remote repository might have changes you don't have.", Colors.RED, bold=True)
        if ask("Attempt to pull changes automatically? (y/n)", "y").lower() == 'y':
            run(["git", "pull", "--rebase"])
            run(["git", "push"])
            print_color(" ✅ Sync resolved successfully.", Colors.GREEN)

def start_dev_server():
    print(f"\n{Colors.BOLD}--- Live Preview ---{Colors.RESET}")
    print_color("Starting local server. Press Ctrl+C to stop and return to menu.", Colors.CYAN)
    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
    try:
        subprocess.run([npm_cmd, "run", "dev"], cwd=ROOT)
    except FileNotFoundError:
        print_color(" ⚠️ Node.js/npm not found. Please install Node.js.", Colors.RED)
    except KeyboardInterrupt:
        print_color("\n 🛑 Server stopped.", Colors.YELLOW)

# --------------------------------------------------------------------------
# Content Management
# --------------------------------------------------------------------------
def add_project():
    print(f"\n{Colors.BOLD}--- New CFD Project ---{Colors.RESET}")
    title = ask("Title", required=True)
    slug = slugify(ask("URL slug", slugify(title)))
    
    filepath = PROJECTS_DIR / f"{slug}.mdx"
    if filepath.exists():
        print_color(f" ⚠️ Project '{slug}' already exists.", Colors.RED)
        return

    summary = ask("Short summary", required=True)
    stack = ask_list("Tech stack (e.g., OpenFOAM, LIGGGHTS, Python)")
    status = ask("Status (ongoing/complete)", "ongoing")
    
    (PROJECTS_DIR / "images" / slug).mkdir(parents=True, exist_ok=True)
    
    content = f"""---
title: "{title}"
summary: "{summary}"
stack: [{", ".join(f'"{i}"' for i in stack)}]
status: "{status}"
date: {date.today().isoformat()}
---

## Overview
Brief introduction to the simulation.

## Methodology
$$
y^+ = \\frac{{u_\\tau y}}{{\\nu}}
$$

## Results
"""
    filepath.write_text(content, encoding="utf-8")
    print_color(f" ✅ Created {filepath.name}.", Colors.GREEN)

def attach_images():
    entry = select_entry("Attach Images")
    if not entry: return
    
    slug = entry.stem
    images_dir = entry.parent / "images" / slug
    images_dir.mkdir(parents=True, exist_ok=True)
    
    print_color(f"\nDrag and drop image files into: {images_dir}", Colors.CYAN)
    print("Or paste full file paths below (blank line to finish).")
    
    copied = []
    while True:
        src = input(f"{Colors.YELLOW}Image path (Enter to stop):{Colors.RESET} ").strip('" ').strip()
        if not src: break
        
        src_path = Path(src)
        if not src_path.exists():
            print_color(f" ⚠️ File not found.", Colors.RED)
            continue
            
        dest = images_dir / src_path.name
        shutil.copy2(src_path, dest)
        copied.append(dest.name)
        print_color(f" ✅ Copied {dest.name}", Colors.GREEN)

def edit_entry():
    entry = select_entry("Edit Entry")
    if not entry: return
    print_color(f"Opening {entry.name} in default editor...", Colors.GREEN)
    if platform.system() == 'Darwin': subprocess.call(('open', entry))
    elif platform.system() == 'Windows': os.startfile(entry)
    else: subprocess.call(('xdg-open', entry))

def remove_entry():
    entry = select_entry("Remove Entry")
    if not entry: return
    
    slug = entry.stem
    images_dir = entry.parent / "images" / slug

    print_color(f"\n ⚠️ DANGER: Permanently delete '{slug}'?", Colors.RED, bold=True)
    if ask("Type 'YES' to confirm") == "YES":
        entry.unlink(missing_ok=True)
        if images_dir.exists(): shutil.rmtree(images_dir, ignore_errors=True)
        print_color(f" 🗑️ Deleted '{slug}'.", Colors.GREEN)
    else:
        print_color(" ❌ Deletion cancelled.", Colors.YELLOW)

# --------------------------------------------------------------------------
# Main Application Loop
# --------------------------------------------------------------------------
def main():
    check_dirs()
    while True:
        show_dashboard()
        print("1. ➕ Add CFD Project")
        print("2. 📸 Attach Images to Entry")
        print("3. ✏️  Edit an Entry")
        print("4. 🗑️  Delete an Entry")
        print("5. 🌐 Start Live Server (npm run dev)")
        print(f"6. 🚀 {Colors.MAGENTA}Sync & Publish to GitHub{Colors.RESET}")
        print("7. 🚪 Exit")
        
        choice = ask("\nSelect Action", "7")
        if choice == "1": add_project()
        elif choice == "2": attach_images()
        elif choice == "3": edit_entry()
        elif choice == "4": remove_entry()
        elif choice == "5": start_dev_server()
        elif choice == "6": advanced_git_sync()
        elif choice == "7": 
            print_color("Session closed.", Colors.GREEN)
            break
        else: 
            print_color("Invalid choice.", Colors.RED)
            
        if choice != "7" and choice != "5":
            input(f"\n{Colors.CYAN}Press Enter to return to Dashboard...{Colors.RESET}")

if __name__ == "__main__":
    main()