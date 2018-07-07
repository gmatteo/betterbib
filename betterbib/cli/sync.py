# -*- coding: utf-8 -*-
#
from __future__ import print_function, unicode_literals

import argparse
import collections

import concurrent.futures
import sys

from pybtex.database.input import bibtex
from tqdm import tqdm

from .. import tools, crossref, dblp, errors, __about__


def main(argv=None):
    parser = _get_parser()
    args = parser.parse_args(argv)

    data = bibtex.Parser().parse_file(args.infile)

    # Use an ordered dictionary to make sure that the entries are written out
    # the way they came in.
    od = tools.decode(collections.OrderedDict(data.entries.items()))

    if args.source == "crossref":
        source = crossref.Crossref(args.long_journal_name)
    else:
        assert args.source == "dblp", "Illegal source."
        source = dblp.Dblp()

    print()
    od, num_success = _update_from_source(od, source, args.num_concurrent_requests)

    print("\n\nTotal number of entries: {}".format(len(data.entries)))
    print("Found: {}".format(num_success))

    tools.write(od, args.outfile, "braces", tab_indent=False)
    return


def _update_from_source(od, source, num_concurrent_requests):
    num_success = 0
    # pylint: disable=bad-continuation
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=num_concurrent_requests
    ) as executor:
        responses = {
            executor.submit(source.find_unique, entry): (bib_id, entry)
            for bib_id, entry in od.items()
        }
        for future in tqdm(
            concurrent.futures.as_completed(responses), total=len(responses)
        ):
            bib_id, entry = responses[future]
            data = None
            try:
                data = future.result()
            except (errors.NotFoundError, errors.UniqueError):
                pass
            except errors.HttpError as e:
                print(e.args[0])
            else:
                num_success += 1

            od[bib_id] = tools.update(entry, data)

    return od, num_success


def _get_parser():
    parser = argparse.ArgumentParser(
        description="Sync BibTeX files with information from online sources."
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
        "-s",
        "--source",
        choices=["crossref", "dblp"],
        default="crossref",
        help="data source (default: crossref)",
    )
    parser.add_argument(
        "-l",
        "--long-journal-name",
        action="store_true",
        help="prefer long journal names (default: false)",
    )
    parser.add_argument(
        "-c",
        "--num-concurrent-requests",
        type=int,
        default=10,
        metavar="N",
        help="number of concurrent HTTPS requests (default: 10)",
    )
    return parser
