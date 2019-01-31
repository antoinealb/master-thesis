#!/usr/bin/env python3
"""
Sorts a tex bibliography according to the order they are cited.
"""

import argparse
import re
import logging


def parse_cite(line):
    """
    Parses a line, returning a list of citation keys.


    >>> parse_cite("Paxos\cite{kernelpaxos} is an \cite{attempt} to.")
    ['kernelpaxos', 'attempt']

    >>> parse_cite("Paxos\cite{kernel, paxos} is an \cite{attempt} to.")
    ['kernel', 'paxos', 'attempt']

    >>> parse_cite("Paxos\cite[p 10.]{kernelpaxos} is an \cite{attempt} to.")
    ['kernelpaxos', 'attempt']

    >>> parse_cite("Foobar is hello")
    []
    """
    pattern = r'\\cite(\[.*?\])?\{(.+?)\}'
    matches = re.findall(pattern, line)
    result = []
    for cite_all in [m[1] for m in matches]:
        result += [s.strip() for s in cite_all.split(",")]

    return result

def parse_include(line):
    """
    Returns the name of the file to include, if there is something to include.
    If the line is not an incude line, return None.

    >>> parse_include('\include{introduction}')
    'introduction.tex'

    >>> parse_include('\section{Foobar}')
    """
    pattern = r'\\include\{(.+?)\}'
    match = re.match(pattern, line)
    if match:
        return match.groups(1)[0] + ".tex"

def extract_citations(input_file):
    """
    Reads all citations from the given file, yielding keys.

    Recursively go into includes.
    """
    logging.debug('Parsing %s', input_file.name)

    total_keys = 0
    for l in input_file:
        total_keys += len(list(parse_cite(l)))

        # Recursively go down in the include
        if parse_include(l):
            with open(parse_include(l)) as f:
                yield from extract_citations(f)

        # Yields all citation keys
        yield from iter(parse_cite(l))

    logging.debug('Found %d keys in %s', total_keys, input_file.name)

def keep_only_first_occurence(seq):
    """
    Keeps only the first occurence of any item in the first given sequence.

    >>> keep_only_first_occurence([1,2,3,1,4])
    [1, 2, 3, 4]
    """
    result = []
    seen_so_far = set()
    for x in seq:
        if x not in seen_so_far:
            result.append(x)
            seen_so_far.add(x)
    return result

def parse_bib_entry(line):
    """
    Parses a bibentry and returns the key if its a starting line.

    Returns none if it is not the start of a bibtex entry.
    >>> parse_bib_entry('@inproceedings{chubby')
    'chubby'
    >>> parse_bib_entry('title={The Chubby lock },')
    """
    pattern = r"@[a-z]*{([^,]*)"
    match = re.match(pattern, line)
    if match:
        return match.group(1)

def parse_bibliography(bibfile):
    """
    Parses a bibfile and returns a dict with the citation key as key and the
    entry lines as values
    """
    result = {}
    for l in bibfile:
        if parse_bib_entry(l):
            key = parse_bib_entry(l)
            result[key] = []
        result[key].append(l)

    return result

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", type=argparse.FileType(), required=True)
    parser.add_argument("--tex", "-t", type=argparse.FileType(), required=True)
    parser.add_argument("--output", "-o", type=argparse.FileType('w'), required=True)
    parser.add_argument("--verbose", "-v", action='store_true')


    return parser.parse_args()

def main():
    args = parse_args()

    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)

    citation_keys = list(extract_citations(args.tex))
    citation_keys = keep_only_first_occurence(citation_keys)
    print(citation_keys)

    bibliography = parse_bibliography(args.input)

    # We keep uncited keys sorted so that this program is a stable sort
    uncited_keys = sorted(set(bibliography.keys()) - set(citation_keys))

    logging.info("%d unused keys: %s", len(uncited_keys), ", ".join(uncited_keys))

    for k in citation_keys + uncited_keys:
        args.output.write("".join(bibliography[k]))


if __name__ == '__main__':
    main()
