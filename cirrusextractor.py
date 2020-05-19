#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# =============================================================================
#  Version: 1.00 (December 15, 2015)
#  Author: Giuseppe Attardi (attardi@di.unipi.it), University of Pisa
#
# =============================================================================
#  Copyright (c) 2015. Giuseppe Attardi (attardi@di.unipi.it).
# =============================================================================
#  This file is part of Tanl.
#
#  Tanl is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License, version 3,
#  as published by the Free Software Foundation.
#
#  Tanl is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
# =============================================================================

# Modifications by Jérémie C. Wenger 2020.

"""
Wikipedia Cirrus Extractor:
Extracts and cleans text from a Wikipedia Cirrus dump and stores output in
files (one per wiki document).
This outputs only raw text, without any html.
"""

import argparse
import gzip
import json
import sys
import re
import os

# ----------------------------------------------------------------------


def process_dump(input_file, out_path, args):
    """
    :param input_file: name of the wikipedia dump file; '-' to read from stdin
    :param out_path: directory where to store extracted data, or '-' for stdout
    :param file_compress: whether to compress files with bzip.
    """

    if input_file == "-":
        inp = sys.stdin
    else:
        inp = gzip.open(input_file)

    count = 0

    # process dump
    # format
    # {"index":{"_type":"page","_id":"3825914"}}
    # {"namespace":0,"title":TITLE,"timestamp":"2014-06-29T15:51:09Z","text":TEXT,...}
    while True:

        count += 1

        line = inp.readline()
        if not line:
            break

        # reads the index line, e.g.: '{"index":{"_type":"page","_id":"56720"}}
        index = json.loads(line)

        # readline reads the next one, containing the actual document
        content = json.loads(inp.readline())
        doc_type = index["index"]["_type"]
        doc_id = index["index"]["_id"]
        language = content["language"]

        if doc_type == "page" and content["namespace"] == 0:

            if out_path == "-":
                sys.stdout.write("\n")
                sys.stdout.write(content["title"] + "\n")
                sys.stdout.write(content["text"] + "\n")

            else:

                title = title_to_filename(content["title"])
                if os.path.basename(out_path).startswith("fr"):
                    text = clean_text(content["text"])
                else:
                    text = content["text"]

                out_fname = os.path.join(out_path, title)
                with open(out_fname, "wb") as o:
                    o.write(text.encode("utf-8"))
                if not args.quiet:
                    print(out_fname)
                if args.count:
                    # https://stackoverflow.com/a/943921
                    columns = int(os.popen("stty size", "r").read().split()[0])
                    print(" " * columns, end="\r")
                    msg = f"{count} | {out_fname}"
                    print(f"{msg[: columns - 5]}...", end="\r")

                # print(title)
                # print()
                # print(text)
                # print('*')
                # print(content["source_text"])
                # print("-"*40)
                # print()


REGICES_FR = {
    "navigation": re.compile(
        r"Début de la boite de navigation du chapitre fin de la boite de navigation du chapitre "
    ),
    "limitations": re.compile(
        r"En raison de limitations techniques, la typographie souhaitable du .*?, n\'a pu être restituée correctement ci-dessus. "
    ),
    "précédent": re.compile(r"\s*<\s+Précédent\s*(\||$)"),
    "suivant": re.compile(r"\s*\|*\s+Suivant\s+>\s*$"),
}


def clean_text(text):
    # drop references:
    # ^ The Penguin Dictionary
    # text = re.sub(r'  \^ .*', '', text)
    text = re.sub(REGICES_FR["suivant"], "", text)
    text = re.sub(REGICES_FR["précédent"], "", text)
    text = re.sub(REGICES_FR["navigation"], "", text)
    text = re.sub(REGICES_FR["limitations"], "", text)
    return text


def title_to_filename(title):
    title = re.sub(r"[  \/,?!();:'\[\]]+", "-", title)
    title = re.sub(r"-+", "-", title)
    title = re.sub(r"-$", "", title)
    title = title.lower()
    title = title + ".txt"
    return title


def dir_name_from_input(inp):
    """
    Take a file path as an input, returns the language code & the wiki name.
    dir/frwikivoyage-.... ---> 'fr', 'wikivoyage'
    """
    fname = os.path.basename(inp)
    m = re.match("^(\w+?wik\w+)-", fname)
    wikiname = m.group(1)
    return wikiname


# ----------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        prog=os.path.basename(sys.argv[0]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    parser.add_argument("input", help="Cirrus Json wiki dump file (.gz)")

    groupO = parser.add_argument_group("output")

    groupO.add_argument(
        "-o",
        "--output_dir",
        default="cirrus",
        help="directory for extracted files (or '-' for dumping to stdin), defaults to 'cirrus'",
    )

    groupO.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppresses all informational printing.",
    )

    groupO.add_argument(
        "-c",
        "--count",
        action="store_true",
        help="prints an ongoing count of the processed files. Will automatically triger 'quiet'",
    )

    args = parser.parse_args()

    input_file = args.input

    if args.count:
        args.quiet = True

    if input_file != "-" and args.output_dir != "-":
        wikiname = dir_name_from_input(input_file)
        out_path = os.path.join(args.output_dir, wikiname)
    else:
        out_path = args.output_dir

    if out_path != "-" and not os.path.isdir(out_path):
        try:
            os.makedirs(out_path)
            print("created dir:", out_path)
        except:
            print("could not create:", out_path)
            return

    process_dump(input_file, out_path, args)

    if args.count:
        print("\n")


if __name__ == "__main__":
    main()
