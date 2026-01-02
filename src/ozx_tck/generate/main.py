from argparse import ArgumentParser, Namespace
from pathlib import Path
import logging

from ..executor import Executor
from .base import CASE_WRITERS

logger = logging.getLogger(__name__)


class Generate(Executor):
    def populate_parser(self, parser: ArgumentParser):
        super().populate_parser(parser)
        parser.description = "Generate examples of OZX files which are valid, should throw warnings, and should error."
        parser.add_argument(
            "zarr_root",
            type=Path,
            help="local path to existing valid OME-Zarr hierarchy root",
        )
        parser.add_argument(
            "output_root",
            type=Path,
            help=(
                "path to an empty target directory; "
                "will populate with `valid`, `warn`, and `error` directories, "
                "each of which contains the relevant examples"
            ),
        )

    def execute(self, args: Namespace):
        super().execute(args)
        for slug, Cls in CASE_WRITERS.items():
            logger.info("generating case %s", slug)
            d: Path = args.output_root / Cls.STATE
            d.mkdir(exist_ok=True, parents=True)
            inst = Cls(d, args.zarr_root)
            inst.write()
