from pathlib import Path
from . import REGISTRY
import logging
from argparse import ArgumentParser

logger = logging.getLogger(__name__)


def main(raw_args=None):
    parser = ArgumentParser("ozx-tck")
    parser.add_argument("zarr_root", type=Path)
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args(raw_args)
    for slug, Cls in REGISTRY.items():
        logger.info("Processing %s", slug)
        d: Path = args.output_root / Cls.STATE
        d.mkdir(exist_ok=True, parents=True)
        inst = Cls(d, args.zarr_root)
        inst.write()


if __name__ == "__main__":
    main()
