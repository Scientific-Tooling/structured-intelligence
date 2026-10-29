"""Atomic workflow records and process-owned locks, including on Windows."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .reading import WorkflowError

if os.name == "nt":
    from .windows_files import open_record, replace
else:
    replace = os.replace

    def open_record(path):
        return path.open("r", encoding="utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def hex_id(value, message: str) -> str:
    """Saved request and record IDs are UUID hex, so they are always safe path segments."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{32}", value):
        raise WorkflowError(message)
    return value


def seal(value: dict) -> dict:
    return {**value, "revision": digest(value)}


def read_sealed(path: Path, schema: str, workspace_id: str, message: str) -> dict:
    """Read a sealed record of this project; any change to it fails with message."""
    value = read_json(path)
    if (value.get("schema") != schema or value.get("workspace_id") != workspace_id
            or value.get("revision") != digest({k: v for k, v in value.items() if k != "revision"})):
        raise WorkflowError(message)
    return value


def read_json(path: Path) -> dict:
    with open_record(path) as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise WorkflowError(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: dict) -> None:
    """A reader sees either the previous complete record or the next one."""
    fd, pending = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        replace(pending, path)
    finally:
        Path(pending).unlink(missing_ok=True)


@contextmanager
def lock(path: Path):
    """Kernel locks release after crashes; never guess ownership from a PID."""
    stream = path.open("a+b")
    acquired = False
    try:
        if os.name == "nt":
            import msvcrt
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise WorkflowError("This workspace is busy. Retry when its active operation finishes.") from exc
        else:
            import fcntl
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise WorkflowError("This workspace is busy. Retry when its active operation finishes.") from exc
        acquired = True
        yield
    finally:
        if acquired:
            if os.name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)
        stream.close()
