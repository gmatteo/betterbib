# -*- coding: utf-8 -*-
#
from __future__ import print_function, unicode_literals

import argparse
import collections
import sys

from pybtex.database.input import bibtex

from .. import tools, __about__


def main(argv=None):
    parser = _get_parser()
    args = parser.parse_args(argv)

    data = bibtex.Parser().parse_file(args.infile)

    # Use an ordered dictionary to make sure that the entries are written out
    # sorted by their BibTeX key if demanded.
    od = tools.decode(
        collections.OrderedDict(
            sorted(data.entries.items())
            if args.sort_by_bibkey
            else data.entries.items()
        )
    )

    od = _adapt_doi_urls(od, args.doi_url_type)

    tools.write(od, args.outfile, args.delimeter_type, tab_indent=args.tabs_indent)
    return


def _adapt_doi_urls(od, doi_url_type):
    if doi_url_type == "new":
        od = _update_doi_url(od, lambda doi: "https://doi.org/" + doi)
    elif doi_url_type == "short":

        def update_to_short_doi(doi):
            short_doi = tools.get_short_doi(doi)
            if short_doi:
                return "https://doi.org/" + short_doi
            return None

        od = _update_doi_url(od, update_to_short_doi)
    else:
        assert doi_url_type == "unchanged"

    return od


def _update_doi_url(od, url_from_doi):
    for bib_id in od:
        if "url" in od[bib_id].fields:
            doi = tools.doi_from_url(od[bib_id].fields["url"])
            if doi:
                new_url = url_from_doi(doi)
                if new_url:
                    od[bib_id].fields["url"] = new_url
    return od


def _get_parser():
    parser = argparse.ArgumentParser(description="Reformat BibTeX files.")

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
        "-b",
        "--sort-by-bibkey",
        action="store_true",
        help="sort entries by BibTeX key (default: false)",
    )
    parser.add_argument(
        "-t",
        "--tabs-indent",
        action="store_true",
        help="use tabs for indentation (default: false)",
    )
    parser.add_argument(
        "-d",
        "--delimeter-type",
        choices=["braces", "quotes"],
        default="braces",
        help=("which delimeters to use in the output file " "(default: braces {...})"),
    )
    parser.add_argument(
        "-u",
        "--doi-url-type",
        choices=["unchanged", "new", "short"],
        default="new",
        help=(
            "DOI URL (new: https://doi.org/<DOI> (default), "
            "short: https://doi.org/abcde)"
        ),
    )
    return parser
