from zipfile import ZipFile
import logging
from .util import walk_files_sorted, make_zip_comment
from .base import Writer

logger = logging.getLogger(__name__)


class Valid(Writer):
    STATE = "valid"

    def _write(self):
        v = self.ome_zarr_version()

        with ZipFile(self.zip_path, "x") as z:
            for entry in walk_files_sorted(self.zarr_root):
                entry.copy_entry(z)

            z.comment = make_zip_comment(v)


Valid.register()


# class ValidArray(Valid):
#     def __init__(self, zip_path: Path, zarr_root: Path) -> None:
#         for entry in walk_files(zarr_root, metadata=True):
#             if is_array(entry.path):
#                 super().__init__(zip_path, entry.path.parent)
#                 return
#         raise AssertionError("No array in this zarr hierarchy")

#     def prepare(self):
#         super().prepare()
#         assert self.is_array()


# ValidArray.register()
