# -*- coding: utf-8 -*-
#
from __future__ import print_function

from .__about__ import __version__, __author__, __author_email__, __website__

from . import cli
from .tools import (
    create_dict,
    decode,
    pybtex_to_dict,
    pybtex_to_bibtex_string,
    write,
    update,
    JournalNameUpdater,
    translate_month,
)
from .crossref import Crossref
from .dblp import Dblp

__all__ = [
    "__version__",
    "__author__",
    "__author_email__",
    "__website__",
    "cli",
    "create_dict",
    "decode",
    "pybtex_to_dict",
    "pybtex_to_bibtex_string",
    "write",
    "update",
    "JournalNameUpdater",
    "translate_month",
    "Crossref",
    "Dblp",
]

try:
    import pipdate
except ImportError:
    pass
else:
    if pipdate.needs_checking(__name__):
        print(pipdate.check(__name__, __version__), end="")
