# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals

import argparse
import sys

from pybtex.database.input import bibtex

from .. import tools
from .. import __about__


def main(argv=None):
    parser = _get_parser()
    args = parser.parse_args(argv)

    data = bibtex.Parser().parse_file(args.infile)

    od = data.entries

    # deduplicate
    for key in data.entries:
        if "url" in od[key].fields and "doi" in od[key].fields:
            doi = tools.doi_from_url(od[key].fields["url"])
            if doi == od[key].fields["doi"]:
                # Would be nicer to remove it completely; see
                # <https://bitbucket.org/pybtex-devs/pybtex/issues/104/implement>.
                if args.keep_doi:
                    od[key].fields["url"] = None
                else:
                    od[key].fields["doi"] = None

    _write(od, args.outfile, "curly")
    return


def _write(od, out, delimeter_type):
    # Write header to the output file.
    out.write(
        "%comment{{This file was created with betterbib v{}.}}\n\n".format(
            __about__.__version__
        )
    )

    # Create the dictionary only once
    dictionary = tools.create_dict()

    # write the data out sequentially to respect ordering
    for bib_id, d in od.items():
        brace_delimeters = delimeter_type == "curly"
        a = tools.pybtex_to_bibtex_string(
            d, bib_id, brace_delimeters=brace_delimeters, dictionary=dictionary
        )
        out.write(a + "\n\n")
    return


def _get_parser():
    parser = argparse.ArgumentParser(
        description="Removes one of DOI and URL in a BibTeX file "
        "if both are identical."
    )
    parser.add_argument(
        "-v",
        "--version",
        help="display version information",
        action="version",
        version="betterbib {}, Python {}".format(__about__.__version__, sys.version),
    )
    parser.add_argument(
        "infile",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="input BibTeX file (default: stdin)",
    )
    parser.add_argument(
        "outfile",
        nargs="?",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="output BibTeX file (default: stdout)",
    )
    parser.add_argument(
        "-k",
        "--keep-doi",
        action="store_true",
        help="keep the DOI rather than the URL (default: false)",
    )
    return parser
