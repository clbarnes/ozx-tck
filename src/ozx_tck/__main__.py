import logging
from argparse import ArgumentParser

from . import generate as _  # noqa: F401
from .executor import EXECUTORS

logger = logging.getLogger(__name__)


def main(raw_args=None):
    parser = ArgumentParser("ozx-tck")
    subparsers = parser.add_subparsers()

    for executor in EXECUTORS.values():
        executor.add_parser(subparsers)

    args = parser.parse_args(raw_args)
    args.func(args)


if __name__ == "__main__":
    main()
