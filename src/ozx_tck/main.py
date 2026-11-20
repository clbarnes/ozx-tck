import logging
from argparse import ArgumentParser

from .executor import Executor
from .generate import Generate
from .validate import Validate

logger = logging.getLogger(__name__)


def setup_logging(verbosity: int | None):
    level = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }.get(verbosity or 0, logging.DEBUG)
    logging.basicConfig(level=level)
    logger.info("log level set to %s", logging.getLevelName(level))


def main(raw_args=None):
    common = ArgumentParser(
        "ozx-tck",
        add_help=False,
        description=(
            "Technology Compatibility Toolkit for OZX files; "
            "single-file archives of OME-Zarr hierarchies. "
            "See subcommands for full functionality."
        ),
    )
    common.add_argument("-v", "--verbose", default=0, action="count")

    (initial_args, remaining) = common.parse_known_args(raw_args)

    setup_logging(initial_args.verbose)

    inner = ArgumentParser()
    subparsers = inner.add_subparsers()

    Cls: type[Executor]
    for Cls in [Generate, Validate]:
        logger.debug("adding executor %s", Cls.__name__)
        Cls().add_parser(subparsers)

    args = inner.parse_args(remaining)

    args.func(args)
