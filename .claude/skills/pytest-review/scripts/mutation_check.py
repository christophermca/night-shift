#!/usr/bin/env python3
"""Break the code on purpose and check that the tests notice.

Usage:
    mutation_check.py FILE OLD NEW [-- PYTEST_ARGS...]

Replaces the first occurrence of OLD with NEW in FILE, runs pytest (with
PYTEST_ARGS, e.g. a test path and -k filter), then always restores FILE.

Exit status: 0 if the mutant was caught (pytest failed), 1 if it survived
(tests stayed green: they don't protect this code), 2 on usage errors.
"""
import os
import subprocess
import sys
from pathlib import Path


def main(argv):
    if "--" in argv:
        split = argv.index("--")
        args, pytest_args = argv[:split], argv[split + 1 :]
    else:
        args, pytest_args = argv, []

    if len(args) != 3:
        print(__doc__, file=sys.stderr)
        return 2

    path, old, new = Path(args[0]), args[1], args[2]
    original = path.read_text()
    if old not in original:
        print(f"'{old}' not found in {path}", file=sys.stderr)
        return 2

    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    # `-o addopts=` drops ini addopts (e.g. --cov) so plugins the project
    # configures can't turn a run into a usage error.
    cmd = [sys.executable, "-m", "pytest", "-q", "--no-header",
           "-p", "no:cacheprovider", "-o", "addopts=", *pytest_args]
    try:
        path.write_text(original.replace(old, new, 1))
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    finally:
        path.write_text(original)

    lines = [l for l in result.stdout.splitlines() if l.strip()]
    print(f"mutant: {path}: {old!r} -> {new!r}")
    print(f"pytest: {lines[-1] if lines else '(no output)'}")
    # pytest exit codes: 0 all passed, 1 tests failed, >=2 error/usage/no tests.
    if result.returncode == 0:
        print("SURVIVED - tests stayed green; they don't protect this code")
        return 1
    if result.returncode == 1:
        print("CAUGHT - tests failed as they should")
        return 0
    print(f"ERROR - pytest exited {result.returncode}; mutant not evaluated")
    print(result.stdout[-2000:] + result.stderr[-2000:], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
