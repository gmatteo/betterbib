# -*- coding: utf-8 -*-
#
"""
Parses a number of bibitems into a proper BibTeX bibliography.  Since bibitems
don't have semantic information, certain heuristics have to be applied.
"""
from __future__ import print_function

import argparse
import re
import sys

from .. import __about__


def main(argv=None):
    parser = _get_parser()
    args = parser.parse_args(argv)

    bibitem_strings = extract_bibitems(args.input)
    previous_author = None
    for bibitem_string in bibitem_strings:
        bibitem = parse_bibitem_string(bibitem_string)
        # If the author entry contains a vrule, assume that this is a
        # placeholder for the authors from the previous paper.
        if (
            "authors" in bibitem
            and (
                "\\vrule" in bibitem["authors"] or "\\sameauthor" in bibitem["authors"]
            )
            and previous_author
        ):
            bibitem["authors"] = previous_author
        entry = create_bibtex_string(bibitem)
        print(entry)
        if "authors" in bibitem:
            previous_author = bibitem["authors"]
        else:
            previous_author = None
    return


def clean(entry):
    """Removes newlines and font specs from entries.
    """
    new = entry
    new = (
        entry.replace("\n", " ")
        .replace("\\em ", "")
        .replace("\\sc ", "")
        .replace("~", " ")
        .strip()
    )
    # Remove surrounding brackets
    if new[0] == "{" and new[-1] == "}":
        new = new[1:-1].strip()

    # Replace multiple white space by a simple space.
    new = re.sub("\\s+", " ", new)
    return new


def clean_pages(entry):
    new = clean(entry)
    m = re.match("^[^0-9]*([0-9]+[-]+[0-9]+).*", entry)
    if m and m.groups():
        new = m.group(1).replace("--", "-")
    return new


def create_bibtex_string(bibitem):
    entries = []
    if "authors" in bibitem:
        entries.append("  author = {{{}}}".format(clean(bibitem["authors"])))
    if "title" in bibitem:
        entries.append("  title = {{{}}}".format(clean(bibitem["title"])))
    if "journal" in bibitem:
        entries.append("  journal = {{{}}}".format(clean(bibitem["journal"])))
    if "publisher" in bibitem:
        entries.append("  publisher = {{{}}}".format(clean(bibitem["publisher"])))
    if "pages" in bibitem:
        entries.append("  pages = {{{}}}".format(clean_pages(bibitem["pages"])))
    if "year" in bibitem:
        entries.append("  year = {{{}}}".format(clean(bibitem["year"])))

    entry = "@{}{{{},\n{}\n}}".format(
        bibitem["type"], bibitem["key"], ",\n".join(entries)
    )
    return entry


def my_split(s):
    """Explodes a string around commas except when in a {}-environment.
    See <http://stackoverflow.com/a/26809037/353337>.
    """
    parts = []
    bracket_level = 0
    current = []
    # trick to remove special-case of trailing chars
    for c in s + ",":
        if c == "," and bracket_level == 0:
            parts.append("".join(current))
            current = []
        else:
            if c == "{":
                bracket_level += 1
            elif c == "}":
                bracket_level -= 1
            current.append(c)
    return parts


def _get_entry_type(m2):
    if len(m2) > 2:
        a = clean_bibitem_string(m2[2])
        if a[:3] == "in:":
            return "inbook"

    if len(m2) > 4:
        a = clean_bibitem_string(m2[4])
        if a[-1] == ".":
            a = a[:-1]

        if len(a) == 4 and "-" not in a:
            return "book"
        return "article"

    # fallback
    return "article"


def parse_bibitem_string(bibitem_string):
    """Parses a bibitem given as (multiline) string and returns semantic
    information. Of course, heuristics are needed.
    """
    # Extract the reference key
    regex = re.compile("^\\\\bibitem{(\\w+)}\\s*(.*)", re.DOTALL)
    m = re.match(regex, bibitem_string)

    # Explode the rest of the string around commas, except the commas
    # are enclosed in curly brackets (e.g., in the authors list).
    m2 = my_split(m.group(2))

    # Now the heuristics.
    bibitem = {
        "key": m.group(1).strip(),
        "authors": clean_bibitem_string(m2[0]),
        "title": clean_bibitem_string(m2[1]),
        "type": _get_entry_type(m2),
    }

    if bibitem["type"] == "article":
        if len(m2) > 2:
            bibitem["journal"] = clean_bibitem_string(m2[2])
        if len(m2) > 3:
            a = clean_bibitem_string(m2[3])
            c = a.split(" ")
            # pylint: disable=len-as-condition
            if len(c) > 0:
                bibitem["number"] = c[0]
            if len(c) > 1 and c[1][0] == "(" and c[1][-1] == ")":
                bibitem["year"] = c[1][1:-1]
        if len(m2) > 4:
            a = clean_bibitem_string(m2[4])
            if a[-1] == ".":
                a = a[:-1]
            bibitem["pages"] = a
    elif bibitem["type"] == "book":
        if len(m2) > 2:
            bibitem["publisher"] = clean_bibitem_string(m2[2])
        if len(m2) > 4:
            a = clean_bibitem_string(m2[4])
            if a[-1] == ".":
                a = a[:-1]
            if len(a) == 4 and "-" not in a:
                bibitem["year"] = a
            else:
                bibitem["pages"] = a
    elif bibitem["type"] == "inbook":
        if len(m2) > 2:
            bibitem["booktitle"] = clean_bibitem_string(m2[2])

    return bibitem


def clean_bibitem_string(string):
    """Removes surrounding whitespace, surrounding \\emph brackets etc.
    """
    out = string
    out = out.strip()
    if out[:6] == "\\emph{" and out[-1] == "}":
        out = out[6:-1]
    if out[:8] == "\\textsc{" and out[-1] == "}":
        out = out[8:-1]

    return out


def extract_bibitems(filename):
    """Parses `filename` and returns all bibitems from inside all
    `thebibliography` environments.
    """
    recording = False
    bibitems = []
    with open(filename, "r") as f:
        for line in f:
            # Get first non-whitespace character
            m = re.match("^\\s*(\\S)", line)
            # Skip commented-out lines
            if m and m.group(1) == "%":
                continue
            if "\\begin{thebibliography}" in line:
                recording = True
            if "\\end{thebibliography}" in line:
                recording = False

            if recording:
                if "\\bibitem" in line:
                    # Create new bibitem entry
                    bibitems.append(line)
                elif bibitems:
                    # Append to last bibitem entry
                    bibitems[-1] += line
    return bibitems


def _get_parser():
    parser = argparse.ArgumentParser(description="Extract bibitems.")
    parser.add_argument(
        "-v",
        "--version",
        help="display version information",
        action="version",
        version="betterbib {}, Python {}".format(__about__.__version__, sys.version),
    )
    parser.add_argument("input", type=str, help="input LaTeX file")
    return parser
