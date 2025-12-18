from zipfile import ZipFile, ZIP_DEFLATED
from random import Random

from ..util import walk_files_sorted, make_zip_comment
from .base import CaseWriter


class WarnWriter(CaseWriter):
    STATE = "warn"


class MissingComment(WarnWriter):
    def _write(self):
        with ZipFile(self.zip_path, "x") as z:
            for entry in walk_files_sorted(self.zarr_root):
                entry.copy_entry(z)


MissingComment.register()


class NotZip64(WarnWriter):
    def _write(self):
        v = self.ome_zarr_version()
        all_over_2gig = True
        with ZipFile(self.zip_path, "x") as z:
            for entry in walk_files_sorted(self.zarr_root):
                if all_over_2gig and entry.path.stat().st_size <= 2 * 1024**3:
                    all_over_2gig = False
                entry.copy_entry(z, False)

            z.comment = make_zip_comment(v)
        assert not all_over_2gig, "all files are over 2GiB; cannot test non-zip64"


NotZip64.register()


class Unsorted(WarnWriter):
    def _write(self):
        v = self.ome_zarr_version()
        rng = Random(1991)

        entries = list(walk_files_sorted(self.zarr_root))
        rng.shuffle(entries)
        with ZipFile(self.zip_path, "x") as z:
            for entry in entries:
                entry.copy_entry(z)

            # metadata is correct, we just don't like unsorted
            z.comment = make_zip_comment(v, False)


Unsorted.register()


class NotOzx(WarnWriter):
    def _write(self):
        v = self.ome_zarr_version()

        self.zip_path.parent.mkdir(exist_ok=True, parents=True)
        with ZipFile(self.zip_path.with_suffix(".zip"), "x") as z:
            for entry in walk_files_sorted(self.zarr_root):
                entry.copy_entry(z)

            z.comment = make_zip_comment(v)


NotOzx.register()


class Compressed(WarnWriter):
    def _write(self):
        v = self.ome_zarr_version()

        self.zip_path.parent.mkdir(exist_ok=True, parents=True)
        with ZipFile(self.zip_path, "x", compression=ZIP_DEFLATED) as z:
            for entry in walk_files_sorted(self.zarr_root):
                entry.copy_entry(z)

            z.comment = make_zip_comment(v)


Compressed.register()
