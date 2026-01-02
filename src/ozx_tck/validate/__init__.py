from __future__ import annotations
from argparse import ArgumentParser, Namespace
from contextlib import AbstractContextManager
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Self, Sequence
from zipfile import ZipFile, ZipInfo
import logging

from ..executor import Executor
from ..util import State

logger = logging.getLogger(__name__)


class Validate(Executor):
    def populate_parser(self, parser: ArgumentParser):
        super().populate_parser(parser)
        parser.add_argument("path", nargs="+", type=Path)
        parser.add_argument(
            "-s", "--strict", action="store_true", help="fail on a warning case"
        )
        parser.add_argument("-f", "--fail-fast", action="store_true")

    def execute(self, args: Namespace):
        super().execute(args)
        events = []
        for p in args.path:
            with Validator(p, args.fail_fast, args.strict) as v:
                events.extend(v.process())

        highest = 0
        msgs = []
        for e in events:
            highest = max(highest, e.level())
            msgs.append(e.fmt())

        if highest == 1 and not args.strict:
            highest = 0

        bail(highest, msgs)


def bail(code=0, msg: None | str | Sequence[str] = None):
    if msg is None:
        msg = []
    elif isinstance(msg, str):
        msg = [msg]
    for m in msg:
        print(m)
    sys.exit(code)


def maybe_bail(info: tuple[int, str] | None):
    if info is not None:
        bail(info[0], info[1])


class BfsChecker:
    def __init__(self) -> None:
        self.layers: list[list[str]] = []
        self.max_depth = 0
        self.bfs = True

    def is_bfs_order(self, name: str) -> bool:
        if not self.bfs:
            return self.bfs

        elems = name.split("/")
        if not elems:
            return self.bfs
        last = elems.pop()

        if not last == "zarr.json":
            return self.bfs

        is_bfs = self.bfs
        # if this element belongs to a layer we've already finished
        if len(elems) < len(self.layers):
            self.bfs = False
            return False
        for idx, elem in enumerate(elems):
            if idx >= len(self.layers):
                self.layers.append([])
            layer = self.layers[idx]

            if elem in layer:
                if elem != layer[-1]:
                    is_bfs = False
                    return False
            else:
                layer.append(elem)

        return is_bfs


@dataclass
class Event:
    path: Path
    arcname: str | None
    state: State
    msg: str

    def fmt(self) -> str:
        return f"{self.path}::{self.arcname}::{self.state.upper()}::{self.msg}"

    def level(self) -> int:
        match self.state:
            case "valid":
                return 0
            case "warn":
                return 1
            case "error":
                return 2

    def normalised_level(self, strict=False) -> int:
        lvl = self.level()
        if lvl == 1 and not strict:
            return 0
        return lvl


class Validator(AbstractContextManager):
    def __init__(self, path: Path, fail_fast=False, strict=False):
        self.path = path
        self.zf = ZipFile(self.path)
        self.fail_fast = fail_fast
        self.strict = strict

        self.events: list[Event] = []

    def finish(self):
        highest = 0
        msgs = []
        for e in self.events:
            highest = max(highest, e.level())
            msgs.append(e.fmt())

        if highest == 1 and not self.strict:
            highest = 0

        self.exit(highest, msgs)

    def format_msg(self, arcname: str | None, msg: str):
        if arcname is None:
            return msg
        return f"{arcname}: {msg}"

    def exit(self, lvl: int = 0, msg: str | Sequence[str] | None = None):
        self.close()
        bail(lvl, msg)

    def add_event(self, state: State, msg: str, arcname: str | None = None):
        if state == "valid":
            return

        event = Event(self.path, arcname, state, msg)
        logger.debug("got event %s", event)
        lvl = event.normalised_level(self.strict)
        if self.fail_fast and lvl:
            self.exit(lvl, event.fmt())
        self.events.append(event)

    def process_comment(self):
        comment = self.zf.comment
        try:
            d: dict = json.loads(comment)
        except json.JSONDecodeError:
            self.add_event("warn", "no JSON comment")
            return

        if not isinstance(d, dict):
            self.add_event("warn", "JSON comment is not an object")

        ome = d.get("ome")
        if not isinstance(ome, dict):
            self.add_event("warn", "JSON comment missing `ome` object")
            return

        if not isinstance(ome.get("version"), str):
            self.add_event("warn", "JSON comment missing `ome.version`")

        try:
            json_first = ome["zipFile"]["centralDirectory"]["jsonFirst"]
            return json_first
        except KeyError:
            self.add_event(
                "warn", "JSON comment does not show metadata files as sorted"
            )
        except Exception as e:
            self.add_event("warn", f"JSON comment malformed: {e}")
        return False

    def process(self):
        logger.info("validating %s", self.path)
        if self.path.suffix != ".ozx":
            self.add_event("warn", "does not end in .ozx")

        expect_sorted = self.process_comment()
        bfs = None
        if expect_sorted:
            bfs = BfsChecker()
        has_root_zarr_json = False

        non_zarr_json = False

        for info in self.zf.infolist():
            logger.debug("processing file %s", info.filename)
            if info.filename == "zarr.json":
                has_root_zarr_json = True
                if non_zarr_json and bfs is not None:
                    self.add_event("error", "should be JSON first but isn't")
            else:
                non_zarr_json = True
            self.process_info(info)
            if bfs is not None:
                bfs.is_bfs_order(info.filename)

        if bfs is not None and not bfs.bfs:
            self.add_event("error", "should be BFS but isn't")

        if not has_root_zarr_json:
            self.add_event("error", "missing root metadata", "zarr.json")

        return self.events

    def process_info(self, info: ZipInfo):
        if info.compress_type != 0:
            self.add_event("warn", "zip compressed", info.filename)

        elems = info.filename.lower().rsplit(".", 1)
        if len(elems) > 1 and elems[-1] in ("zip", "ozx"):
            self.add_event("error", "probably contains archive", info.filename)

        # TODO: test for ZIP64?

    def close(self):
        self.zf.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.close()
