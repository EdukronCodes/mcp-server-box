"""Test invoice processing tools integration."""

import pytest
import json
from pathlib import Path


@pytest.fixture
def invoice_tools():
    """Create invoice tools instance for testing."""
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from tools.box_tools_invoices import InvoiceTools

    return InvoiceTools(invoice_directory="invoices")


def test_list_invoices(invoice_tools):
    """Test listing available invoices."""
    result = invoice_tools.list_invoices()
    assert "error" not in result or result["error"] is None
    assert "files" in result
    assert len(result["files"]) > 0
    assert any(f.endswith(".pdf") for f in result["files"])


def test_process_single_invoice(invoice_tools):
    """Test processing a single invoice."""
    files = invoice_tools.list_invoices()
    if "files" in files and files["files"]:
        file_name = files["files"][0]
        result = invoice_tools.process_single_invoice(file_name)
        
        assert "error" not in result or not result["error"]
        assert "invoice_number" in result
        assert "total_amount" in result
        assert result["total_amount"] >= 0


def test_process_all_invoices(invoice_tools):
    """Test processing all invoices."""
    result = invoice_tools.process_all_invoices()
    
    assert "error" not in result or not result["error"]
    assert "total_processed" in result
    assert result["total_processed"] > 0
    assert "invoices" in result
    assert "summary" in result
    assert len(result["invoices"]) == result["total_processed"]


def test_invoice_summary(invoice_tools):
    """Test getting invoice summary."""
    result = invoice_tools.get_invoice_summary()
    
    assert "error" not in result or not result["error"]
    assert "total_invoices" in result
    assert result["total_invoices"] > 0
    assert "total_amount" in result
    assert "total_tax" in result
    assert "average_confidence" in result


def test_search_invoices(invoice_tools):
    """Test searching invoices."""
    # First get summary to find a valid invoice number
    summary = invoice_tools.get_invoice_summary()
    if summary.get("invoices"):
        inv_number = summary["invoices"][0]["invoice_number"]
        
        result = invoice_tools.search_invoices(inv_number)
        assert "error" not in result or not result["error"]
        assert "query" in result
        assert "matches" in result
        assert result["matches"] > 0


def test_export_invoices(invoice_tools, tmp_path):
    """Test exporting invoices."""
    output_file = tmp_path / "invoices_export.json"
    result = invoice_tools.export_invoices_as_json(str(output_file))
    
    assert "error" not in result or not result["error"]
    assert output_file.exists()
    
    # Verify exported file contains valid JSON
    with open(output_file) as f:
        data = json.load(f)
        assert "invoices" in data
        assert "summary" in data


def test_invoice_details(invoice_tools):
    """Test getting invoice details."""
    files = invoice_tools.list_invoices()
    if "files" in files and files["files"]:
        file_name = files["files"][0]
        result = invoice_tools.get_invoice_details(file_name)
        
        assert "error" not in result or not result["error"]
        assert result["file_name"] == file_name
        assert "invoice_number" in result
        assert "confidence_score" in result


def test_extracted_fields():
    """Test that key fields are extracted correctly."""
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from pdf_processor import InvoiceFieldExtractor

    extractor = InvoiceFieldExtractor()
    pdf_files = list(Path("invoices").glob("*.pdf"))
    
    assert len(pdf_files) > 0, "No PDF files found in invoices folder"
    
    for pdf_file in pdf_files:
        invoice = extractor.extract_invoice_fields(str(pdf_file))
        
        # Verify all expected fields are present
        assert invoice.file_name
        assert invoice.invoice_number  # Should extract invoice number
        assert invoice.invoice_date  # Should extract date
        assert invoice.total_amount >= 0  # Should extract total
        assert 0 <= invoice.confidence_score <= 1  # Confidence should be 0-1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
