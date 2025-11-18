"""Unit tests for GeneCLI business logic and caching."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import business


class TestGeneCache(unittest.TestCase):
    """Test the GeneCache class."""

    def setUp(self):
        """Create a temporary cache file for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = Path(self.temp_dir.name) / "test_cache.json"

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_cache_init_creates_directory(self):
        """Test that GeneCache creates parent directories if needed."""
        cache = business.GeneCache(self.cache_path)
        self.assertTrue(self.cache_path.parent.exists())

    def test_cache_set_and_get(self):
        """Test setting and retrieving values from cache."""
        cache = business.GeneCache(self.cache_path)
        test_data = {"symbol": "BRCA1", "summary": "Test summary"}
        cache.set("BRCA1", test_data)

        result = cache.get("BRCA1")
        self.assertIsNotNone(result)
        self.assertEqual(result.get("symbol"), "BRCA1")
        self.assertIn("fetched_at", result)

    def test_cache_case_insensitive(self):
        """Test that cache keys are case-insensitive."""
        cache = business.GeneCache(self.cache_path)
        test_data = {"symbol": "BRCA1", "summary": "Test"}
        cache.set("brca1", test_data)

        # Should retrieve with uppercase key
        result = cache.get("BRCA1")
        self.assertIsNotNone(result)

    def test_cache_persistence(self):
        """Test that cache persists across instances."""
        cache1 = business.GeneCache(self.cache_path)
        cache1.set("TP53", {"symbol": "TP53", "summary": "Test"})

        # Create new cache instance with same path
        cache2 = business.GeneCache(self.cache_path)
        result = cache2.get("TP53")
        self.assertIsNotNone(result)
        self.assertEqual(result.get("symbol"), "TP53")

    def test_legacy_cache_cleanup(self):
        """Test that legacy cache format is removed on get."""
        cache = business.GeneCache(self.cache_path)
        # Manually insert old-style cache entry
        cache._data["OLDGENE"] = {"fetched_at": 12345, "data": "old format"}
        cache._save()

        # Get should remove it
        result = cache.get("OLDGENE")
        self.assertIsNone(result)
        # Verify it was removed from persistent storage
        result2 = cache.get("OLDGENE")
        self.assertIsNone(result2)


class TestFetchDetailsViaNCBI(unittest.TestCase):
    """Test NCBI ClinicalTables fetch function."""

    @patch("business.requests.get")
    def test_fetch_details_success(self, mock_get):
        """Test successful fetch of gene details."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "uids": ["672"],
                "672": {
                    "Symbol": "BRCA1",
                    "description": "BRCA1 DNA repair associated",
                    "GeneID": "672",
                    "chromosome": "17",
                    "map_location": "17q21.31",
                }
            }
        }
        mock_get.return_value = mock_response

        # Mock the ClinicalTables API response (array format)
        mock_response.json.return_value = [
            3,  # total
            ["HGNC:1099"],  # codes
            None,  # ef_hash
            [["BRCA1", "BRCA1 DNA repair associated"]],  # displays
        ]

        result = business.fetch_details_via_ncbi("BRCA1")
        self.assertIsNotNone(result)
        self.assertEqual(result.get("symbol"), "BRCA1")

    @patch("business.requests.get")
    def test_fetch_details_not_found(self, mock_get):
        """Test when gene is not found raises GeneNotFoundError."""
        mock_response = MagicMock()
        mock_response.json.return_value = [0, [], None, []]  # empty result
        mock_get.return_value = mock_response

        with self.assertRaises(business.GeneNotFoundError):
            business.fetch_details_via_ncbi("NONEXISTENT")


class TestFetchSummaryFromEntrez(unittest.TestCase):
    """Test NCBI Entrez esummary fetch function."""

    @patch("business.requests.get")
    def test_fetch_summary_success(self, mock_get):
        """Test successful fetch of Entrez summary."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "uids": ["672"],
                "672": {
                    "summary": "This gene encodes a tumor suppressor protein...",
                    "name": "BRCA1",
                },
            }
        }
        mock_get.return_value = mock_response

        result = business.fetch_summary_from_entrez("672")
        self.assertIsNotNone(result)
        self.assertIn("tumor suppressor", result)

    @patch("business.requests.get")
    def test_fetch_summary_invalid_geneid(self, mock_get):
        """Test with invalid GeneID."""
        result = business.fetch_summary_from_entrez("not_a_number")
        self.assertIsNone(result)
        mock_get.assert_not_called()


class TestGetGeneData(unittest.TestCase):
    """Test the main get_gene_data function."""

    def setUp(self):
        """Create a temporary cache for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = Path(self.temp_dir.name) / "test_cache.json"
        self.cache = business.GeneCache(self.cache_path)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_get_gene_data_empty_gene(self):
        """Test that empty gene symbol raises ValueError."""
        with self.assertRaises(ValueError):
            business.get_gene_data("", cache=self.cache)

    def test_get_gene_data_whitespace_gene(self):
        """Test that whitespace-only gene symbol raises ValueError."""
        with self.assertRaises(ValueError):
            business.get_gene_data("   ", cache=self.cache)

    @patch("business.fetch_details_via_ncbi")
    @patch("business.fetch_gene_from_genecards")
    def test_get_gene_data_not_found(self, mock_genecards, mock_details):
        """Test GeneNotFoundError when gene is not found."""
        mock_genecards.side_effect = RuntimeError("Not found")
        mock_details.side_effect = business.GeneNotFoundError("Gene not found")

        with self.assertRaises(business.GeneNotFoundError):
            business.get_gene_data("FAKEGENE", cache=self.cache)

    @patch("business.fetch_details_via_ncbi")
    @patch("business.fetch_summary_from_entrez")
    @patch("business.fetch_gene_from_genecards")
    def test_get_gene_data_success(self, mock_genecards, mock_entrez, mock_details):
        """Test successful gene data retrieval."""
        mock_genecards.side_effect = RuntimeError("Auth required")
        mock_details.return_value = {
            "symbol": "BRCA1",
            "description": "BRCA1 DNA repair associated",
            "geneid": "672",
            "chromosome": "17",
            "map_location": "17q21.31",
        }
        mock_entrez.return_value = "This is a longer Entrez summary..."

        result = business.get_gene_data("BRCA1", cache=self.cache)
        self.assertIsNotNone(result)
        self.assertEqual(result.get("symbol"), "BRCA1")
        self.assertEqual(result.get("geneid"), "672")
        self.assertIn("ncbi_url", result)
        self.assertIn("genecards_url", result)

    @patch("business.fetch_details_via_ncbi")
    @patch("business.fetch_summary_from_entrez")
    @patch("business.fetch_gene_from_genecards")
    def test_get_gene_data_caching(self, mock_genecards, mock_entrez, mock_details):
        """Test that successful results are cached."""
        mock_genecards.side_effect = RuntimeError("Auth required")
        mock_details.return_value = {
            "symbol": "TEST",
            "description": "Test gene",
            "geneid": "999",
            "chromosome": "1",
            "map_location": "1p1.1",
        }
        mock_entrez.return_value = "Test summary"

        # First call should fetch
        result1 = business.get_gene_data("TEST", cache=self.cache)
        call_count_1 = mock_details.call_count

        # Second call should use cache (no additional calls)
        result2 = business.get_gene_data("TEST", cache=self.cache)
        call_count_2 = mock_details.call_count

        self.assertEqual(result1, result2)
        self.assertEqual(call_count_1, call_count_2)  # Should not fetch again


class TestURLGeneration(unittest.TestCase):
    """Test URL generation in get_gene_data."""

    def setUp(self):
        """Create a temporary cache for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = Path(self.temp_dir.name) / "test_cache.json"
        self.cache = business.GeneCache(self.cache_path)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    @patch("business.fetch_details_via_ncbi")
    @patch("business.fetch_gene_from_genecards")
    def test_ncbi_url_generation(self, mock_genecards, mock_details):
        """Test NCBI URL is generated when GeneID is present."""
        mock_genecards.side_effect = RuntimeError("Auth required")
        mock_details.return_value = {
            "symbol": "BRCA1",
            "description": "Test",
            "geneid": "672",
            "chromosome": "17",
            "map_location": "17q21.31",
        }

        result = business.get_gene_data("BRCA1", cache=self.cache)
        self.assertEqual(result.get("ncbi_url"), "https://www.ncbi.nlm.nih.gov/gene/672")

    @patch("business.fetch_details_via_ncbi")
    @patch("business.fetch_gene_from_genecards")
    def test_genecards_url_generation(self, mock_genecards, mock_details):
        """Test GeneCards URL is always generated."""
        mock_genecards.side_effect = RuntimeError("Auth required")
        mock_details.return_value = {
            "symbol": "BRCA1",
            "description": "Test",
            "geneid": "672",
            "chromosome": "17",
            "map_location": "17q21.31",
        }

        result = business.get_gene_data("BRCA1", cache=self.cache)
        self.assertIn("genecards_url", result)
        self.assertIn("BRCA1", result.get("genecards_url", ""))


if __name__ == "__main__":
    unittest.main()
