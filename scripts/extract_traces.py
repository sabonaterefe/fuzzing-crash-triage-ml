#!/usr/bin/env python3
"""
Runs each AFL++ crash input through the ASan-instrumented harness,
captures the resulting stack trace, and saves a structured JSON record
per crash to results/crashes/.
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AFL_OUTPUT_DIR = PROJECT_ROOT / "results" / "afl_output" / "default"
HARNESS = PROJECT_ROOT / "src" / "harness"
OUT_DIR = PROJECT_ROOT / "results" / "crashes"
RAW_DIR = OUT_DIR / "raw"

FRAME_RE = re.compile(
    r"^\s*#(\d+)\s+0x[0-9a-fA-F]+\s+in\s+(\S+)\s+(.+?):(\d+)(?::\d+)?\s*$"
)


def find_crash_files():
    """AFL++ renames crashes/ to crashes.<timestamp>/ on each fresh
    start after a resume, so crash inputs end up spread across several
    crashes.* directories -- and the SAME crash bytes can appear under
    more than one directory name across resumes. Dedupe by content
    hash (md5) so a renamed directory never double-counts a crash."""
    import hashlib

    seen_hashes = set()
    crash_files = []
    for entry in sorted(AFL_OUTPUT_DIR.glob("crashes*")):
        if entry.is_dir():
            for f in sorted(entry.iterdir()):
                if f.is_file() and f.name.startswith("id:"):
                    digest = hashlib.md5(f.read_bytes()).hexdigest()
                    if digest in seen_hashes:
                        continue
                    seen_hashes.add(digest)
                    crash_files.append(f)
    return crash_files


def run_harness(crash_file: Path) -> str:
    env = os.environ.copy()
    env["ASAN_OPTIONS"] = "abort_on_error=1:symbolize=1"
    try:
        result = subprocess.run(
            [str(HARNESS), str(crash_file)],
            cwd=HARNESS.parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired as e:
        return (e.stdout or "") + (e.stderr or "") + "\n[TIMEOUT]"


def parse_frames(asan_output: str):
    """Only keep the FIRST contiguous block of stack frames: that's
    the crash-site stack. ASan prints a second 'allocated by' stack
    afterwards which we deliberately ignore here to avoid mixing the
    two into one noisy/duplicated frame list."""
    frames = []
    started = False
    for line in asan_output.splitlines():
        m = FRAME_RE.match(line)
        if m:
            started = True

            frames.append({
                "frame": int(m.group(1)),
                "function": m.group(2),
                "file": m.group(3),
                "line": int(m.group(4)),
            })
        elif started:
            break
    return frames


def extract_crash_summary(asan_output: str):
    for line in asan_output.splitlines():
        if "ERROR: AddressSanitizer:" in line:
            return line.strip()
    return None


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    crash_files = find_crash_files()
    print(f"Found {len(crash_files)} crash input(s).")

    for crash_file in crash_files:
        crash_id = f"{crash_file.parent.name}__{crash_file.name}".replace(":", "_")
        print(f"Processing {crash_id} ...")

        shutil.copy2(crash_file, RAW_DIR / crash_id)

        asan_output = run_harness(crash_file)

        frames = parse_frames(asan_output)
        summary = extract_crash_summary(asan_output)

        record = {
            "crash_id": crash_id,
            "source_file": str(crash_file.relative_to(PROJECT_ROOT)),
            "error_summary": summary,
            "frames": frames,
            "raw_asan_output": asan_output,
        }

        (OUT_DIR / f"{crash_id}.json").write_text(json.dumps(record, indent=2))
        print(f"  -> {summary or 'no ASan summary found'} ({len(frames)} crash-site frames)")

    print("Done.")


if __name__ == "__main__":
    main()
