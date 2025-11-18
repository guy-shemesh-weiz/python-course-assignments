"""CLI for gene fetcher. Handles user interaction only and calls business logic.

Usage:
  - Run interactively: python cli.py
  - Pass genes as args: python cli.py BRCA1 TP53

The program loops: after printing results it prompts again, until user types 'exit' or Ctrl-C.
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path
from typing import Iterable


import business


def print_gene_result(gene: str, result: object) -> None:
    """Print a concise multi-field summary for the gene.

    Output includes: Symbol, Entrez GeneID, Chromosome, Map location, and Description/summary.
    """
    if not isinstance(result, dict):
        print(f"No data for {gene}")
        return

    sym = result.get("symbol") or gene
    geneid = result.get("geneid")
    chrom = result.get("chromosome")
    maploc = result.get("map_location")
    summary = result.get("summary")

    parts = [f"{sym}"]
    if geneid:
        parts.append(f"Entrez:{geneid}")
    if chrom:
        parts.append(f"Chr:{chrom}")
    if maploc:
        parts.append(f"Loc:{maploc}")

    header = " | ".join(parts)
    print(header)
    # print one-line condensed summary (single line). Prefer Entrez summary if available,
    # otherwise use the (whitespace-normalized) description.
    one_line = None
    entrez = result.get("entrez_summary") if isinstance(result, dict) else None
    if entrez:
        one_line = " ".join(entrez.split())
    elif summary:
        one_line = " ".join(summary.split())
    if summary:
        print(f"Description: {summary}")
    else:
        print(f"No description available for {sym}")
    if one_line:
        if len(one_line) > 300:
            one_line = one_line[:297] + "..."
        print(f"Summary: {one_line}")
    # print link(s)
    ncbi = result.get("ncbi_url")
    genecards = result.get("genecards_url")
    if ncbi:
        print(f"NCBI: {ncbi}")
    if genecards:
        print(f"GeneCards: {genecards}")


def process_genes(genes: Iterable[str], cache: business.GeneCache | None = None) -> None:
    if cache is None:
        cache = business.GeneCache()
    for gene in genes:
        gene = gene.strip()
        if not gene:
            continue
        try:
            res = business.get_gene_data(gene, cache=cache)
            print_gene_result(gene, res)
        except business.GeneNotFoundError as e:
            print(f"❌ Gene not found: {gene}")
        except Exception as e:
            print(f"⚠️  Error fetching {gene}: {e}")


def print_help() -> None:
    """Print usage and help information."""
    print(textwrap.dedent("""
    GeneCLI - Fetch gene information from NCBI and GeneCards
    
    Usage:
      python cli.py [GENE1 GENE2 ...]     Fetch genes and exit
      python cli.py                        Enter interactive mode
      python cli.py --help, -h             Show this help message
    
    Interactive Mode Commands:
      GENE1 GENE2 ...     Fetch one or more genes
      help                Show this help message
      exit, quit          Exit the program
      Ctrl-C              Exit the program
    
    Output includes:
      - Gene symbol and Entrez ID
      - Chromosome and map location
      - Summary (from NCBI Entrez, or description)
      - Links to NCBI Gene and GeneCards pages
    
    Examples:
      python cli.py BRCA1 TP53
      python cli.py
      > BRCA1 TP53
      > exit
    """))


def interactive_loop(cache: business.GeneCache | None = None) -> None:
    if cache is None:
        cache = business.GeneCache()
    print(textwrap.dedent("""
    Gene CLI interactive mode.
    Enter gene symbols separated by spaces (e.g. BRCA1 TP53).
    Type 'help' for usage, 'exit' or 'quit' to leave.
    """))
    while True:
        try:
            user = input("genes> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            return

        if not user:
            continue
        if user.lower() in ("help", "-h", "--help"):
            print_help()
            continue
        if user.lower() in ("exit", "quit"):
            print("Bye.")
            return

        genes = user.split()
        process_genes(genes, cache=cache)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="genecli",
        description="Fetch gene information from NCBI and GeneCards",
        add_help=False
    )
    parser.add_argument("genes", nargs="*", help="Gene symbols to fetch")
    parser.add_argument("-h", "--help", action="store_true", help="Show help message")
    
    args = parser.parse_args()
    
    if args.help:
        print_help()
        return 0
    
    if args.genes:
        # Non-interactive mode: fetch genes and exit
        process_genes(args.genes)
        return 0
    
    # Interactive mode
    interactive_loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
