from __future__ import annotations
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Literal
from .util import is_array, ome_zarr_version


REGISTRY: dict[str, type[Writer]] = dict()


class Writer(ABC):
    STATE: Literal["valid", "warn", "error"]

    def __init__(self, zip_dir: Path, zarr_root: Path) -> None:
        self.zip_dir = zip_dir
        self.zarr_root = zarr_root

    @classmethod
    def slug(cls) -> str:
        return cls.__name__.lower()

    def filename(self) -> str:
        return type(self).slug() + ".ozx"

    @property
    def zip_path(self) -> Path:
        return self.zip_dir.joinpath(self.filename())

    def ome_zarr_version(self) -> str:
        return ome_zarr_version(self.zarr_root)

    def is_array(self) -> bool:
        return is_array(self.zarr_root / "zarr.json")

    def prepare(self):
        assert not self.zip_path.exists(), "target zip already exists"
        self.zip_path.parent.mkdir(exist_ok=True, parents=True)

    def write(self):
        self.prepare()
        self._write()

    @abstractmethod
    def _write(self):
        pass

    @classmethod
    def register(cls):
        REGISTRY[cls.slug()] = cls
