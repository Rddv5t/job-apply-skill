"""Install bundled skills; optionally run the huashu-chrome installer."""
import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BROWSER_PACKAGE = "huashu-chrome@1.3.0"
OFFERLINK_URL = "https://offerlink.tech/"


def same_tree(source, target):
    if not target.is_dir():
        return False
    def files(root):
        return {p.relative_to(root): p.read_bytes() for p in root.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    source_files = files(source)
    target_files = files(target)
    return source_files == target_files


def main():
    p = argparse.ArgumentParser(description=__doc__)
    default_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    p.add_argument("--target", type=Path, default=default_home / "skills")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--with-browser", action="store_true")
    p.add_argument("--with-tracker", action="store_true",
                   help="Prepare the pinned local autumn tracker extension instead of requiring OfferLink")
    args = p.parse_args()
    root = Path(__file__).resolve().parent
    skills = sorted((root / "skills").iterdir())
    targets = [(s, args.target.expanduser().absolute() / s.name) for s in skills
               if s.is_dir() and (s / "SKILL.md").exists()]
    if not targets:
        p.error("No bundled skills found")
    for source, target in targets:
        if source.resolve() == target.resolve() or source.resolve() in target.resolve().parents:
            p.error("Install target cannot be inside the source directory")
        if target.is_symlink():
            p.error(f"Refusing to overwrite a symlink: {target}")
        if target.exists() and not same_tree(source, target) and not args.overwrite:
            p.error(f"{target} exists with different files; use --overwrite to back up and replace it")
    if args.with_browser and not shutil.which("npx"):
        p.error("--with-browser needs Node.js/npm (npx); install it or omit that flag")
    print("First-time onboarding:")
    print("1. Load the prepared local autumn tracker extension." if args.with_tracker else
          "1. Choose local autumn tracker (--with-tracker) or OfferLink: " + OFFERLINK_URL)
    print("2. Enter and verify your own information/resume in the chosen extension.")
    print("3. In $job-apply, rank target roles, cities and industries as 1 / 2 / 3.")
    print("Browser extension installation/login must be completed in your browser.")
    for source, target in targets:
        if same_tree(source, target):
            print(f"Already installed: {source.name}")
            continue
        print(f"Install {source.name} -> {target}")
        if args.dry_run:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            backup = target.with_name(target.name + ".backup-" + stamp)
            target.rename(backup)
            print(f"Backed up: {backup}")
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if args.with_tracker:
        tracker_dest = args.target.expanduser().absolute().parent / "job-apply-runtime" / (
            "autumn-tracker-" + "a24b328" + "-compat-v3")
        command = [sys.executable, str(root / "skills/job-apply/scripts/prepare_autumn_tracker.py"),
                   "--dest", str(tracker_dest)]
        if args.dry_run:
            print("Prepare local tracker: " + " ".join(command))
        elif (tracker_dest / "JOB_APPLY_LOCAL_PATCH.json").exists():
            print("Local tracker is already prepared: " + str(tracker_dest))
        else:
            subprocess.run(command, check=True)
    if args.with_browser:
        command = [shutil.which("npx"), "-y", BROWSER_PACKAGE, "install"]
        print("Browser dependency: " + " ".join(command))
        if not args.dry_run:
            subprocess.run(command + ["--dry-run"], check=True)
            print("The third-party installer may configure detected AI clients.")
            if input("Run its installer and open extension setup? [y/N] ").strip().lower() == "y":
                subprocess.run(command, check=True)
                print("Finish enabling the extension in your browser, then reload your AI client.")
            else:
                print("Browser setup skipped. Bundled skills are installed.")
    print("Dry run complete." if args.dry_run else
          "Skills installed. Complete your profile tool setup, then open a new chat and invoke $job-apply.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as exc:
        sys.exit(f"Installation failed: {exc}")
