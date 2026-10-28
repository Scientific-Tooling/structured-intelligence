"""Atomic record publication on modern Windows, including open shared readers.

Use FileRenameInfoEx with REPLACE_IF_EXISTS | POSIX_SEMANTICS. Unlike the
MoveFileEx operation behind os.replace, replacement does not leave the previous
record's name pending deletion while shared handles finish. Readers must allow
delete sharing; unrelated exclusive handles still produce an explicit error.
https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information
"""
from __future__ import annotations

import ctypes
import msvcrt
import os
from ctypes import wintypes as w

_api = ctypes.WinDLL("kernel32", use_last_error=True)
_api.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, ctypes.c_void_p, w.DWORD, w.DWORD, w.HANDLE]
_api.CreateFileW.restype = w.HANDLE
_api.SetFileInformationByHandle.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
_api.SetFileInformationByHandle.restype = w.BOOL
_api.CloseHandle.argtypes = [w.HANDLE]
_api.CloseHandle.restype = w.BOOL


def _open(path, access):
    # FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE; OPEN_EXISTING.
    handle = _api.CreateFileW(os.path.abspath(path), access, 7, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        error = ctypes.WinError(ctypes.get_last_error())
        error.filename = str(path)
        raise error
    return handle


def open_record(path):
    handle = _open(path, 0x80000000)  # GENERIC_READ
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        _api.CloseHandle(handle)
        raise
    # The CRT descriptor owns the handle from this point onward.
    try:
        return os.fdopen(fd, "r", encoding="utf-8")
    except BaseException:
        os.close(fd)
        raise


def replace(source, destination):
    encoded = os.path.abspath(destination).encode("utf-16-le")

    class Rename(ctypes.Structure):
        _fields_ = [("Flags", w.DWORD), ("RootDirectory", w.HANDLE), ("FileNameLength", w.DWORD),
                    ("FileName", w.WCHAR * (len(encoded) // 2 + 1))]

    info = Rename()
    info.Flags = 0x1 | 0x2  # REPLACE_IF_EXISTS | POSIX_SEMANTICS; preserve read-only/ACL checks.
    info.FileNameLength = len(encoded)
    ctypes.memmove(ctypes.addressof(info) + Rename.FileName.offset, encoded, len(encoded))
    handle = _open(source, 0x10000)  # DELETE permission to rename this owned temporary file.
    try:
        if not _api.SetFileInformationByHandle(handle, 22, ctypes.byref(info), ctypes.sizeof(info)):  # FileRenameInfoEx
            error = ctypes.WinError(ctypes.get_last_error())
            error.filename, error.filename2 = str(source), str(destination)
            raise error
    finally:
        _api.CloseHandle(handle)
