from __future__ import annotations
from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from typing import Any
import logging

logger = logging.getLogger(__name__)
EXECUTORS: dict[str, Executor] = dict()


class Executor(ABC):
    @abstractmethod
    def populate_parser(self, parser: ArgumentParser):
        logger.debug("populating parser from %s", type(self).__name__)

    def add_parser(
        self, add_subparser, add_subparser_kwargs: dict[str, Any] | None = None
    ):
        if add_subparser_kwargs is None:
            add_subparser_kwargs = dict()
        parser: ArgumentParser = add_subparser.add_parser(
            type(self).__name__.lower(), **add_subparser_kwargs
        )
        self.populate_parser(parser)
        parser.set_defaults(func=self.execute)

    @abstractmethod
    def execute(self, args: Namespace):
        logger.debug("executing %s with args %s", type(self).__name__, args)
