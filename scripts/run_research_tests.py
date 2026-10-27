"""Run the research suite and expose failed tracebacks in GitHub annotations."""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    arguments = sys.argv[1:] or ["discover", "-s", "tests", "-p", "test_research_*.py", "-v"]
    result = subprocess.run([sys.executable, "-m", "unittest", *arguments],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    sys.stdout.buffer.write(result.stdout)
    sys.stdout.buffer.flush()
    if result.returncode and os.environ.get("GITHUB_ACTIONS") == "true":
        # GitHub truncates long annotations; keep the traceback at the log tail.
        message = result.stdout[-3500:].decode("utf-8", errors="replace")
        escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        sys.stdout.buffer.write(f"::error title=Research test traceback::{escaped}\n".encode("utf-8"))
        sys.stdout.buffer.flush()
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
