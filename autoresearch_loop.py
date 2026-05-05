"""Overnight self-improvement loop.

Each iteration: send the editable files plus instructions to Claude, ask
for one targeted diff, apply it, re-score, keep on improvement, roll back
otherwise. Every experiment is appended to ``experiments.json`` and
mirrored into the dashboard.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

EDITABLE_FILES = [
    "strategies/momentum.py",
    "strategies/mean_reversion.py",
    "allocator.py",
]
READONLY_CONTEXT = ["strategies/buy_hold.py"]
IMPROVEMENT_THRESHOLD = 0.02
MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 4096

REPO_ROOT = Path(__file__).resolve().parent
EXPERIMENTS_PATH = REPO_ROOT / "experiments.json"
DASHBOARD_EXPERIMENTS_PATH = REPO_ROOT / "dashboard" / "public" / "data" / "experiments.json"
LATEST_SCORE_PATH = REPO_ROOT / "latest_score.json"
RESEARCH_MD_PATH = REPO_ROOT / "RESEARCH.md"

DESCRIPTION_RE = re.compile(r"^DESCRIPTION:\s*(.+)$", re.MULTILINE)
DIFF_BLOCK_RE = re.compile(r"```diff\s*\n(.*?)```", re.DOTALL)


def run_cmd(cmd_list: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Wrapper for ``subprocess.run`` rooted at the repo with text capture."""
    return subprocess.run(
        cmd_list,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=check,
    )


def get_current_sharpe() -> float:
    """Run ``score.py`` and return the validation Sharpe; ``-inf`` on failure."""
    try:
        proc = run_cmd([sys.executable, "score.py"], check=False)
        if proc.returncode != 0:
            print(f"[score] non-zero exit: {proc.stderr.strip()}")
            return float("-inf")
        data = json.loads(LATEST_SCORE_PATH.read_text())
        return float(data["val_sharpe"])
    except Exception as exc:
        print(f"[score] failed: {exc}")
        return float("-inf")


def read_files_for_agent() -> str:
    """Concatenate editable + read-only files into one structured string."""
    sections = []
    for path in EDITABLE_FILES + READONLY_CONTEXT:
        full = REPO_ROOT / path
        body = full.read_text() if full.exists() else "(missing)"
        sections.append(f"### File: {path}\n```python\n{body}\n```")
    return "\n\n".join(sections)


def call_claude(client) -> Tuple[Optional[str], Optional[str]]:
    """Send RESEARCH.md plus current source to Claude and parse out (description, diff)."""
    research = RESEARCH_MD_PATH.read_text()
    files_block = read_files_for_agent()

    user_message = (
        f"{research}\n\n---\n\n"
        f"## Current source\n\n{files_block}\n\n---\n\n"
        "Propose exactly one targeted improvement now. Match the output format exactly."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": user_message}],
    )

    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")

    description_match = DESCRIPTION_RE.search(text)
    diff_match = DIFF_BLOCK_RE.search(text)

    description = description_match.group(1).strip() if description_match else None
    diff = diff_match.group(1) if diff_match else None
    return description, diff


def _clean_diff(diff: str) -> str:
    """Pre-clean a diff body: strip trailing whitespace, normalize blank lines.

    LLM output frequently contains trailing spaces on context lines and
    pure-whitespace blank lines that ``git apply`` rejects in strict mode.
    We rstrip every line and collapse pure-whitespace lines to a bare
    space (preserving the leading marker for blank context lines).
    """
    cleaned_lines = []
    for line in diff.splitlines():
        if not line:
            cleaned_lines.append("")
            continue
        first = line[0]
        if first in (" ", "+", "-") and line.strip() == "":
            cleaned_lines.append(first)
        else:
            cleaned_lines.append(line.rstrip())
    return "\n".join(cleaned_lines) + "\n"


def apply_diff(diff: str) -> bool:
    """Apply a unified diff with progressively more lenient flags.

    Tries strict, then ignore-whitespace, then ignore-whitespace plus
    recount (which tolerates a wrong line count in the ``@@`` hunk
    header). Returns True on first success.
    """
    cleaned = _clean_diff(diff)

    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as tmp:
        tmp.write(cleaned)
        patch_path = tmp.name

    flag_attempts = [
        ["--whitespace=fix"],
        ["--whitespace=fix", "--ignore-whitespace"],
        ["--whitespace=fix", "--ignore-whitespace", "--recount"],
    ]
    last_err = ""
    try:
        for flags in flag_attempts:
            proc = run_cmd(["git", "apply", *flags, patch_path], check=False)
            if proc.returncode == 0:
                return True
            last_err = proc.stderr.strip()
        print(f"[git apply] failed after fallbacks: {last_err}")
        return False
    finally:
        try:
            os.unlink(patch_path)
        except OSError:
            pass


def git_commit(description: str, val_sharpe: float, exp_num: int) -> None:
    """Stage and commit the accepted change with a structured message."""
    run_cmd(["git", "add", "-A"], check=True)
    msg = f"exp {exp_num}: {description} [val_sharpe={val_sharpe:.4f}]"
    run_cmd(["git", "commit", "-m", msg], check=True)


def git_reset_hard() -> None:
    """Discard any uncommitted changes."""
    run_cmd(["git", "reset", "--hard", "HEAD"], check=False)


def append_experiment(record: dict) -> None:
    """Append one experiment record to ``experiments.json`` and mirror into the dashboard."""
    history = []
    if EXPERIMENTS_PATH.exists():
        try:
            history = json.loads(EXPERIMENTS_PATH.read_text())
        except json.JSONDecodeError:
            history = []
    history.append(record)
    EXPERIMENTS_PATH.write_text(json.dumps(history, indent=2))

    DASHBOARD_EXPERIMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_EXPERIMENTS_PATH.write_text(json.dumps(history, indent=2))


def _next_experiment_number() -> int:
    if not EXPERIMENTS_PATH.exists():
        return 1
    try:
        data = json.loads(EXPERIMENTS_PATH.read_text())
        return len(data) + 1
    except json.JSONDecodeError:
        return 1


def _ensure_clean_tree() -> None:
    proc = run_cmd(["git", "status", "--porcelain"], check=False)
    if proc.stdout.strip():
        print("ERROR: working tree has uncommitted changes. Commit or stash before running the loop.")
        sys.exit(1)


def run_one_iteration(client, exp_num: int, current_best: float) -> float:
    """Run a single AutoResearch iteration and return the (possibly updated) best Sharpe."""
    timestamp = datetime.now(timezone.utc).isoformat()
    record: dict = {
        "experiment": exp_num,
        "timestamp": timestamp,
        "val_sharpe_before": current_best,
        "kept": False,
        "status": "unknown",
    }

    try:
        description, diff = call_claude(client)
    except Exception as exc:
        record.update(status="api_error", error=str(exc))
        append_experiment(record)
        print(f"[exp {exp_num}] API error: {exc}")
        return current_best

    if not description or not diff:
        record.update(status="parse_error", description=description, diff=diff)
        append_experiment(record)
        print(f"[exp {exp_num}] parse error -- skipping")
        return current_best

    record["description"] = description
    record["diff"] = diff

    if not apply_diff(diff):
        record.update(status="diff_apply_failed")
        append_experiment(record)
        git_reset_hard()
        print(f"[exp {exp_num}] diff failed to apply -- rolled back")
        return current_best

    new_sharpe = get_current_sharpe()
    record["val_sharpe_after"] = new_sharpe

    if new_sharpe == float("-inf"):
        record.update(status="score_error")
        append_experiment(record)
        git_reset_hard()
        print(f"[exp {exp_num}] scoring failed -- rolled back")
        return current_best

    delta = new_sharpe - current_best
    record["delta"] = round(delta, 4)

    if delta >= IMPROVEMENT_THRESHOLD:
        git_commit(description, new_sharpe, exp_num)
        record.update(status="ok", kept=True)
        append_experiment(record)
        print(f"[exp {exp_num}] KEPT  delta=+{delta:.4f}  -> {new_sharpe:.4f}  ::  {description}")
        return new_sharpe

    git_reset_hard()
    record.update(status="ok", kept=False)
    append_experiment(record)
    print(f"[exp {exp_num}] reject delta={delta:+.4f}  -> stay at {current_best:.4f}  ::  {description}")
    return current_best


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AutoResearch self-improvement loop.")
    parser.add_argument("--iterations", type=int, default=10, help="Number of iterations to attempt.")
    parser.add_argument(
        "--overnight",
        action="store_true",
        help="Increase per-iteration sleep from 2s to 5s for long unattended runs.",
    )
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY is not set in your environment.")
        sys.exit(1)

    try:
        from anthropic import Anthropic
    except ImportError:
        print("ERROR: install dependencies first: pip install -r requirements.txt")
        sys.exit(1)

    _ensure_clean_tree()

    client = Anthropic(api_key=api_key)
    sleep_seconds = 5 if args.overnight else 2

    current_best = get_current_sharpe()
    if current_best == float("-inf"):
        print("ERROR: baseline scoring failed. Run `python score.py` manually to debug.")
        sys.exit(1)
    print(f"baseline val_sharpe = {current_best:.4f}")

    start_num = _next_experiment_number()
    try:
        for i in range(args.iterations):
            exp_num = start_num + i
            try:
                current_best = run_one_iteration(client, exp_num, current_best)
            except KeyboardInterrupt:
                raise
            except Exception:
                print(f"[exp {exp_num}] unexpected error:")
                traceback.print_exc()
                git_reset_hard()
            time.sleep(sleep_seconds)
    except KeyboardInterrupt:
        print("\ninterrupted -- stopping cleanly")

    print(f"done. current best val_sharpe = {current_best:.4f}")


if __name__ == "__main__":
    main()