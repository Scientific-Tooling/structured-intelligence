"""Compatibility entry point; implementation is shipped in scientific-tooling."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scientific_tooling import brief as implementation
if __name__ == "__main__":
    raise SystemExit(implementation.main())
sys.modules[__name__] = implementation
