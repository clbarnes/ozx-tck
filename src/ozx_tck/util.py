from collections.abc import Iterable
from pathlib import Path
from dataclasses import dataclass
import json
from collections import deque
from typing import Any
from zipfile import ZipFile
import logging

logger = logging.getLogger(__name__)

SUBCOMMANDS = dict()

@dataclass
class FileEntry:
    path: Path
    """Path to the file on the file system."""

    name: str
    """Name of the entry in the zip archive (includes parent directories)."""

    @classmethod
    def from_root(cls, root: Path, fullpath: Path):
        return cls(fullpath, str(fullpath.relative_to(root)))

    def copy_entry(self, zf: ZipFile, force_zip64=True):
        b = self.path.read_bytes()
        with zf.open(self.name, "w", force_zip64=force_zip64) as f:
            f.write(b)


def is_array(path: Path) -> bool:
    """Takes path to zarr.json file"""
    return json.loads(path.read_text())["node_type"] == "array"


def walk_files_sorted(root: Path) -> Iterable[FileEntry]:
    yield from walk_files(root, True)
    yield from walk_files(root, False)


def walk_files(root: Path, metadata: bool | None = None) -> Iterable[FileEntry]:
    """Recursively iterate through all files below the root in breadth-first order.

    If metadata is None, return all files.
    If metadata is True, only return zarr.json files.
    If metadata is False, only return files other than zarr.json.
    """
    to_visit = deque([root])
    while to_visit:
        dirpath = to_visit.popleft()
        dirnames = []
        filenames = []
        for p in dirpath.iterdir():
            if p.is_symlink():
                continue
            elif p.is_dir():
                dirnames.append(p.name)
            elif p.is_file():
                if p.name == "zarr.json":
                    if metadata is False:
                        continue

                    if metadata is True and is_array(p):
                        dirnames.clear()
                        filenames.clear()
                        yield FileEntry.from_root(root, p)
                        break

                elif metadata is True:
                    continue

                filenames.append(p.name)

        dirnames.sort()
        filenames.sort()

        for fname in filenames:
            yield FileEntry.from_root(root, dirpath / fname)

        for dname in dirnames:
            to_visit.append(dirpath / dname)


def make_zip_comment(version: str, json_first: bool | None = True) -> bytes:
    d: dict[str, Any] = {
        "ome": {
            "version": version,
        }
    }
    if json_first is not None:
        d["ome"]["zipFile"] = {"centralDirectory": {"jsonFirst": json_first}}
    return json.dumps(d).encode()


class NoZarrJson(FileNotFoundError):
    pass


class NotOmeZarr(ValueError):
    pass


def ome_zarr_version(root_dir: Path) -> str:
    """May raise NoZarrJson or NotOmeZarr."""
    p = root_dir / "zarr.json"
    if not p.is_file(follow_symlinks=False):
        raise NoZarrJson()

    d = json.loads(p.read_text())
    if "ome" not in d.get("attributes", dict()):
        logger.error("Got zarr metadata object: %s", d)
        raise NotOmeZarr()
    return d["attributes"]["ome"]["version"]
