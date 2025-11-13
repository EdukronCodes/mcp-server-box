"""Tools for processing and managing invoices through the MCP server."""

import json
import logging
from pathlib import Path

from pdf_processor import (
    ExtractedInvoice,
    InvoiceFieldExtractor,
    process_invoices_in_directory,
)

logger = logging.getLogger(__name__)


class InvoiceTools:
    """Collection of invoice processing tools."""

    def __init__(self, invoice_directory: str = "invoices"):
        """Initialize invoice tools."""
        self.invoice_directory = invoice_directory
        self.extractor = InvoiceFieldExtractor()
        self._cache = {}

    def process_single_invoice(self, file_name: str) -> dict:
        """
        Process a single invoice PDF and extract fields.

        Args:
            file_name: Name of the PDF file in the invoice directory

        Returns:
            Dictionary with extracted invoice data
        """
        pdf_path = Path(self.invoice_directory) / file_name

        if not pdf_path.exists():
            return {"error": f"Invoice file not found: {file_name}"}

        try:
            invoice = self.extractor.extract_invoice_fields(str(pdf_path))
            result = invoice.to_dict()
            # Cache the result
            self._cache[file_name] = result
            return result
        except Exception as e:
            logger.error(f"Error processing invoice {file_name}: {e}")
            return {"error": str(e)}

    def process_all_invoices(self) -> dict:
        """
        Process all invoices in the invoice directory.

        Returns:
            Dictionary with all extracted invoices and summary statistics
        """
        try:
            result = process_invoices_in_directory(self.invoice_directory)
            return result
        except Exception as e:
            logger.error(f"Error processing invoices: {e}")
            return {"error": str(e)}

    def list_invoices(self) -> dict:
        """
        List all available invoice files.

        Returns:
            Dictionary with list of invoice files
        """
        try:
            invoice_dir = Path(self.invoice_directory)
            if not invoice_dir.exists():
                return {"error": f"Invoice directory not found: {self.invoice_directory}"}

            invoices = list(invoice_dir.glob("*.pdf"))
            return {
                "directory": self.invoice_directory,
                "count": len(invoices),
                "files": [f.name for f in invoices],
            }
        except Exception as e:
            logger.error(f"Error listing invoices: {e}")
            return {"error": str(e)}

    def get_invoice_summary(self) -> dict:
        """
        Get a summary of all processed invoices.

        Returns:
            Dictionary with invoice statistics
        """
        try:
            result = process_invoices_in_directory(self.invoice_directory)
            if "error" in result:
                return result

            invoices = result.get("invoices", [])
            if not invoices:
                return {"total_invoices": 0, "summary": {}}

            return {
                "total_invoices": len(invoices),
                "total_amount": result["summary"]["total_amount"],
                "total_tax": result["summary"]["total_tax"],
                "average_confidence": result["summary"]["average_confidence"],
                "invoices": [
                    {
                        "file_name": inv["file_name"],
                        "invoice_number": inv["invoice_number"],
                        "invoice_date": inv["invoice_date"],
                        "total_amount": inv["total_amount"],
                        "confidence": inv["confidence_score"],
                    }
                    for inv in invoices
                ],
            }
        except Exception as e:
            logger.error(f"Error getting invoice summary: {e}")
            return {"error": str(e)}

    def search_invoices(self, query: str) -> dict:
        """
        Search invoices by invoice number or date.

        Args:
            query: Search query (invoice number or partial date)

        Returns:
            List of matching invoices
        """
        try:
            result = process_invoices_in_directory(self.invoice_directory)
            if "error" in result:
                return result

            invoices = result.get("invoices", [])
            query_lower = query.lower()

            matches = [
                inv
                for inv in invoices
                if query_lower in inv["invoice_number"].lower()
                or query_lower in inv["invoice_date"]
                or query_lower in inv["file_name"].lower()
            ]

            return {"query": query, "matches": len(matches), "invoices": matches}
        except Exception as e:
            logger.error(f"Error searching invoices: {e}")
            return {"error": str(e)}

    def get_invoice_details(self, file_name: str) -> dict:
        """
        Get detailed information for a specific invoice.

        Args:
            file_name: Name of the invoice PDF file

        Returns:
            Detailed invoice information
        """
        if file_name in self._cache:
            return self._cache[file_name]

        return self.process_single_invoice(file_name)

    def export_invoices_as_json(self, output_file: str = None) -> dict:
        """
        Export all invoices as JSON.

        Args:
            output_file: Optional path to save JSON file

        Returns:
            Dictionary with export result
        """
        try:
            result = process_invoices_in_directory(self.invoice_directory)
            if "error" in result:
                return result

            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2)
                return {"status": "success", "saved_to": str(output_path)}

            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Error exporting invoices: {e}")
            return {"error": str(e)}
