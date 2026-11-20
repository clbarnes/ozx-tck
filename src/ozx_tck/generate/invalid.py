import json
import shlex
import subprocess as sp
from math import ceil
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from ..util import make_zip_comment, walk_files_sorted
from .base import CaseWriter


class ErrorWriter(CaseWriter):
    STATE = "error"


class RootNotZarr(ErrorWriter):
    def _write(self):
        v = self.ome_zarr_version()
        with ZipFile(self.zip_path, "x") as z:
            for entry in walk_files_sorted(self.zarr_root):
                entry.name = "somedirectory/" + entry.name
                entry.copy_entry(z)

            z.comment = make_zip_comment(v)


RootNotZarr.register()


class OzxInOzx(ErrorWriter):
    def _write(self):
        v = self.ome_zarr_version()
        with TemporaryDirectory(prefix="ozx-tck_ozx-in-ozx") as dname:
            tmpz = Path(dname) / "inner.ozx"
            with ZipFile(tmpz, "w") as z:
                with z.open("zarr.json", "w", force_zip64=True) as f:
                    f.write(
                        json.dumps(
                            {
                                "node_type": "group",
                                "zarr_version": 3,
                                "attributes": {"ome": {"version": v}},
                            }
                        ).encode()
                    )
                z.comment = make_zip_comment(v)

            with ZipFile(self.zip_path, "x") as z:
                for entry in walk_files_sorted(self.zarr_root):
                    entry.copy_entry(z)
                with z.open("inner.ozx", "w", force_zip64=True) as f:
                    f.write(tmpz.read_bytes())

                z.comment = make_zip_comment(v)


OzxInOzx.register()


class Multipart(ErrorWriter):
    def _write(self):
        v = self.ome_zarr_version()
        with ZipFile(self.zip_path, "x") as z:
            for entry in walk_files_sorted(self.zarr_root):
                entry.copy_entry(z)

            z.comment = make_zip_comment(v)

        size = self.zip_path.stat().st_size
        # some `zip` impls have an 8-character limit
        # on the split size???
        max_maxsize = int("9" * 8)
        maxsize = min(ceil(size / 3), max_maxsize)
        container = self.zip_path.with_suffix("")
        container.mkdir()
        root = container / (self.zip_path.stem + ".zip")
        sp.run(
            shlex.split(f"zip {self.zip_path} --out {root} -s {maxsize}"),
            check=True,
            capture_output=True,
        )
        try:
            self.zip_path.unlink()
        except FileNotFoundError:
            pass


Multipart.register()


class MisleadingSort(ErrorWriter):
    def _write(self):
        v = self.ome_zarr_version()
        rng = Random(1991)

        entries = list(walk_files_sorted(self.zarr_root))
        rng.shuffle(entries)
        with ZipFile(self.zip_path, "x") as z:
            for entry in entries:
                entry.copy_entry(z)

            # metadata is incorrect
            z.comment = make_zip_comment(v, True)


MisleadingSort.register()
