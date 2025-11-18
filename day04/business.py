"""Business logic for gene CLI: fetching and caching summaries.

This module tries GeneCards GeneALaCart first. Because that service typically requires a
logged-in session to return JSON, we detect when it returns HTML (login page) and fall back
to the public NCBI ClinicalTables API to obtain gene information. The cache stores only the
extracted fields and the source used.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests


class GeneNotFoundError(Exception):
    """Raised when a gene symbol is not found in any data source."""
    pass


DEFAULT_CACHE_PATH = Path("cache.json")



class GeneCache:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else DEFAULT_CACHE_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._data = {}
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception:
            # corrupted cache -> start fresh
            self._data = {}

    def get(self, gene: str) -> Optional[Any]:
        val = self._data.get(gene.upper())
        if not val:
            return None
        # Handle legacy cache entries which stored raw responses under a `data` key.
        # New normalized cache stores 'summary' and 'source'. If we detect the old
        # format we drop it (so a fresh fetch is attempted) and persist the removal.
        if isinstance(val, dict) and "summary" not in val and "data" in val:
            try:
                del self._data[gene.upper()]
                self._save()
            except Exception:
                pass
            return None
        return val

    def set(self, gene: str, value: Any) -> None:
        # store minimal normalized structure
        self._data[gene.upper()] = {"fetched_at": int(time.time()), **value}
        self._save()

    def _save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception:
            # best effort; avoid crashing the program on save failures
            pass


def fetch_gene_from_genecards(gene: str, timeout: int = 10) -> Any:
    """Attempt to fetch gene data from GeneCards GeneALaCart Query endpoint.

    Note: GeneALaCart's web endpoint requires authentication for JSON responses. When called
    anonymously the site normally returns HTML (login page). This function requests JSON
    and raises a RuntimeError with a clear message if authentication appears required.
    """
    url = "https://genealacart.genecards.org/Query"
    session = requests.Session()
    params = {"geneList": gene, "format": "json"}
    headers = {"Accept": "application/json"}

    try:
        resp = session.get(url, params=params, headers=headers, timeout=timeout)
    except Exception as exc:
        raise RuntimeError(f"Network error while contacting GeneALaCart: {exc}")

    content_type = resp.headers.get("Content-Type", "")
    if "application/json" not in content_type.lower():
        # try to decode in case server returned JSON but wrong content-type
        try:
            return resp.json()
        except Exception:
            raise RuntimeError("GeneALaCart did not return JSON (likely requires authentication).")

    try:
        return resp.json()
    except Exception as exc:
        raise RuntimeError(f"Failed to decode JSON from GeneALaCart: {exc}")


def fetch_summary_via_ncbi(gene: str, timeout: int = 10) -> Optional[str]:
    """Fallback to NCBI Genes via ClinicalTables to obtain a gene description.

    Uses the ClinicalTables API: https://clinicaltables.nlm.nih.gov/api/ncbi_genes/v3/search
    The API returns an array where element 3 contains display fields requested via the `df`
    parameter. We'll request `df=Symbol,description` and look for an exact symbol match, or
    return the first description available.
    """
    url = "https://clinicaltables.nlm.nih.gov/api/ncbi_genes/v3/search"
    params = {
        "terms": gene,
        "df": "Symbol,description",
        "count": 20,
    }
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        j = resp.json()
        # j format: [total, codes[], ef_hash|null, df_display_array, ...]
        displays = j[3] if len(j) > 3 and j[3] is not None else []
        if not displays:
            return None
        # each display is an array matching df order: [Symbol, description]
        for disp in displays:
            sym = disp[0] if len(disp) >= 1 else None
            desc = disp[1] if len(disp) >= 2 else None
            if sym and sym.upper() == gene.upper():
                return desc
        # No exact match -> not found (don't return fuzzy/partial matches)
        return None
    except Exception:
        return None


def fetch_details_via_ncbi(gene: str, timeout: int = 10) -> Optional[Dict[str, Optional[str]]]:
    """Fetch detailed fields from ClinicalTables NCBI Genes API.

    Returns a dict with keys: symbol, description, geneid, chromosome, map_location (values may be None).
    Raises GeneNotFoundError if no results are returned.
    """
    url = "https://clinicaltables.nlm.nih.gov/api/ncbi_genes/v3/search"
    # request display fields (df) and extra fields (ef) to retrieve structured data
    params = {
        "terms": gene,
        "df": "Symbol,description",
        "ef": "GeneID,chromosome,map_location",
        "count": 20,
    }
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        j = resp.json()
        # j format: [total, codes[], ef_hash|null, df_display_array, ...]
        codes = j[1] if len(j) > 1 and j[1] is not None else []
        ef_hash = j[2] if len(j) > 2 else None
        displays = j[3] if len(j) > 3 and j[3] is not None else []
        if not displays or not codes:
            # No results found -> gene does not exist
            raise GeneNotFoundError(f"Gene '{gene}' not found in NCBI database")

        # look for exact symbol match first
        for idx, disp in enumerate(displays):
            sym = disp[0] if len(disp) >= 1 else None
            desc = disp[1] if len(disp) >= 2 else None
            if sym and sym.upper() == gene.upper():
                # extract ef fields for this index if available
                geneid = ef_hash.get("GeneID")[idx] if ef_hash and "GeneID" in ef_hash and idx < len(ef_hash.get("GeneID")) else None
                chrom = ef_hash.get("chromosome")[idx] if ef_hash and "chromosome" in ef_hash and idx < len(ef_hash.get("chromosome")) else None
                maploc = ef_hash.get("map_location")[idx] if ef_hash and "map_location" in ef_hash and idx < len(ef_hash.get("map_location")) else None
                return {
                    "symbol": sym,
                    "description": desc,
                    "geneid": geneid,
                    "chromosome": chrom,
                    "map_location": maploc,
                }

        # No exact match found -> gene symbol not found
        # (Don't return partial matches; ClinicalTables fuzzy search can return unrelated genes)
        raise GeneNotFoundError(f"Gene '{gene}' not found in NCBI database")
    except GeneNotFoundError:
        raise
    except Exception:
        # network error or other issue -> raise not found to be safe
        raise GeneNotFoundError(f"Could not fetch gene '{gene}' from NCBI (network error)")


def fetch_summary_from_entrez(geneid: str, timeout: int = 10) -> Optional[str]:
    """Fetch the official gene summary from NCBI Entrez esummary (returns 'Summary').

    Uses the public E-utilities esummary endpoint. Returns the Summary string if present.
    """
    try:
        # ensure geneid is string/int
        gid = str(int(geneid))
    except Exception:
        return None

    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {"db": "gene", "id": gid, "retmode": "json"}
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        j = resp.json()
        result = j.get("result", {})
        # 'uids' contains list of ids returned
        uids = result.get("uids") or []
        if not uids:
            return None
        uid = uids[0]
        info = result.get(uid) or {}
        summary = info.get("summary") or info.get("Summary")
        if summary:
            return summary
        return None
    except Exception:
        return None


def fetch_gene_info_via_entrez(gene: str, timeout: int = 10) -> Optional[Dict[str, Optional[str]]]:
    """Fetch gene info using NCBI Entrez esearch + esummary (more reliable for exact matches).
    
    This is used as a fallback when ClinicalTables doesn't return exact matches.
    Returns dict with symbol, geneid, chromosome, map_location if found.
    """
    # First: use esearch to find the gene ID by symbol
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "gene",
        "term": f'"{gene}"[Gene Symbol] AND human[orgn]',
        "retmode": "json",
        "retmax": 5,
    }
    
    try:
        resp = requests.get(search_url, params=search_params, timeout=timeout)
        resp.raise_for_status()
        j = resp.json()
        result = j.get("esearchresult", {})
        ids = result.get("idlist") or []
        
        if not ids:
            return None
        
        # Found at least one match; fetch details for the first one
        geneid = ids[0]
        
        # Second: use esummary to get detailed info
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {
            "db": "gene",
            "id": geneid,
            "retmode": "json",
        }
        resp2 = requests.get(summary_url, params=summary_params, timeout=timeout)
        resp2.raise_for_status()
        j2 = resp2.json()
        result2 = j2.get("result", {})
        info = result2.get(geneid) or {}
        
        # Extract fields
        symbol = info.get("name") or gene  # fallback to input
        chromosome = info.get("chromosome")
        maplocation = info.get("maplocation")
        description = info.get("description")
        
        return {
            "symbol": symbol,
            "geneid": geneid,
            "chromosome": chromosome,
            "map_location": maplocation,
            "description": description,
        }
    except Exception:
        return None


def get_gene_data(gene: str, cache: Optional[GeneCache] = None) -> Dict[str, Any]:
    """Return a dict with at least 'summary' and 'source'.

    Workflow:
    - If cached, return cached dict
    - Try GeneALaCart (may require auth) -> if successful and contains a summary field use it
    - Otherwise fall back to MyGene.info to fetch summary
    - Cache and return a dict like: {"summary": str or None, "source": "genecards"|"mygene"}
    """
    if cache is None:
        cache = GeneCache()

    gene_key = gene.strip().upper()
    if not gene_key:
        raise ValueError("Empty gene symbol")

    cached = cache.get(gene_key)
    if cached is not None:
        # If cached but entrez summary missing and we have a geneid, enrich cache with entrez summary
        try:
            if isinstance(cached, dict) and cached.get("geneid") and cached.get("entrez_summary") is None:
                entrez = fetch_summary_from_entrez(cached.get("geneid"))
                if entrez:
                    cached["entrez_summary"] = entrez
                    cache.set(gene_key, cached)
        except Exception:
            pass
        return cached

    # Try GeneALaCart first (may raise if auth required). If not usable, fall back to NCBI ClinicalTables
    try:
        gc = fetch_gene_from_genecards(gene_key)
        # try to extract a summary/description
        summary = None
        details = None
        if isinstance(gc, dict):
            if "summary" in gc and isinstance(gc["summary"], str):
                summary = gc["summary"]
            else:
                # attempt to locate nested candidate
                candidate = None
                if gene_key in gc:
                    candidate = gc.get(gene_key)
                else:
                    for v in gc.values():
                        candidate = v
                        break

                if isinstance(candidate, dict):
                    for k in ("summary", "GeneCards Summary", "description", "function"):
                        if k in candidate and isinstance(candidate[k], str):
                            summary = candidate[k]
                            break

        if summary is None:
            try:
                details = fetch_details_via_ncbi(gene_key)
                source = "ncbi"
            except GeneNotFoundError:
                # ClinicalTables didn't find exact match; try Entrez directly
                details = fetch_gene_info_via_entrez(gene_key)
                if details:
                    source = "entrez"
                else:
                    raise GeneNotFoundError(f"Gene '{gene_key}' not found")
        else:
            # prefer to also try to enrich with NCBI fields when available
            try:
                details = fetch_details_via_ncbi(gene_key)
                source = "genecards"
            except GeneNotFoundError:
                # fallback to Entrez if ClinicalTables fails
                details = fetch_gene_info_via_entrez(gene_key)
                source = "entrez" if details else "genecards"

    except RuntimeError:
        try:
            details = fetch_details_via_ncbi(gene_key)
            source = "ncbi"
        except GeneNotFoundError:
            # try Entrez as fallback
            details = fetch_gene_info_via_entrez(gene_key)
            if details:
                source = "entrez"
            else:
                raise GeneNotFoundError(f"Gene '{gene_key}' not found")

    # normalize output: symbol, summary/description, geneid, chromosome, map_location, source
    out = {
        "symbol": gene_key,
        "summary": None,
        "geneid": None,
        "chromosome": None,
        "map_location": None,
        "ncbi_url": None,
        "genecards_url": None,
        "source": source,
        "fetched_at": int(time.time()),
    }

    if details:
        out.update({
            "symbol": details.get("symbol") or gene_key,
            "summary": details.get("description"),
            "geneid": details.get("geneid"),
            "chromosome": details.get("chromosome"),
            "map_location": details.get("map_location"),
        })

    # Add URLs: NCBI gene page (if geneid available) and GeneCards page by symbol
    if out.get("geneid"):
        try:
            out["ncbi_url"] = f"https://www.ncbi.nlm.nih.gov/gene/{out.get('geneid')}"
        except Exception:
            out["ncbi_url"] = None
    # GeneCards URL by symbol (works even if GeneALaCart requires auth for API)
    try:
        out["genecards_url"] = f"https://www.genecards.org/cgi-bin/carddisp.pl?gene={out.get('symbol')}"
    except Exception:
        out["genecards_url"] = None
    # If we have a GeneID, try to fetch the NCBI Entrez 'Summary' (usually a short paragraph)
    # and prefer it for the one-line condensed summary if available.
    if out.get("geneid"):
        entrez_summary = fetch_summary_from_entrez(out.get("geneid"))
        if entrez_summary:
            # prefer Entrez summary for one-line display but keep the description in 'summary'
            out["entrez_summary"] = entrez_summary
        else:
            out["entrez_summary"] = None
    else:
        out["entrez_summary"] = None

    # if we previously had a summary from GeneALaCart, prefer it
    if 'summary' in locals() and summary:
        out["summary"] = summary

    cache.set(gene_key, out)
    return cache.get(gene_key)
