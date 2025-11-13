"""Tool registry for invoice processing tools."""

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from tools.box_tools_invoices import InvoiceTools

logger = logging.getLogger(__name__)

# Initialize invoice tools
invoice_tools = InvoiceTools(invoice_directory="invoices")


def register_invoice_tools(mcp: FastMCP) -> None:
    """Register invoice processing tools with the MCP server."""

    @mcp.tool()
    def process_single_invoice(file_name: str) -> dict:
        """
        Process a single invoice PDF and extract key fields.

        Args:
            file_name: Name of the PDF file (e.g., 'demo-invoice-20tax-2.pdf')

        Returns:
            Extracted invoice data including number, date, amounts, etc.
        """
        return invoice_tools.process_single_invoice(file_name)

    @mcp.tool()
    def process_all_invoices() -> dict:
        """
        Process all invoices in the invoices directory.

        Returns:
            Summary of all processed invoices with statistics
        """
        return invoice_tools.process_all_invoices()

    @mcp.tool()
    def list_invoices() -> dict:
        """
        List all available invoice PDF files.

        Returns:
            List of invoice files in the directory
        """
        return invoice_tools.list_invoices()

    @mcp.tool()
    def get_invoice_summary() -> dict:
        """
        Get a summary of all invoices with key statistics.

        Returns:
            Summary statistics and invoice list
        """
        return invoice_tools.get_invoice_summary()

    @mcp.tool()
    def search_invoices(query: str) -> dict:
        """
        Search invoices by invoice number, date, or file name.

        Args:
            query: Search term (invoice number, date, or file name)

        Returns:
            Matching invoices
        """
        return invoice_tools.search_invoices(query)

    @mcp.tool()
    def get_invoice_details(file_name: str) -> dict:
        """
        Get detailed information for a specific invoice.

        Args:
            file_name: Name of the invoice PDF file

        Returns:
            Complete invoice details with extracted fields
        """
        return invoice_tools.get_invoice_details(file_name)

    @mcp.tool()
    def export_invoices(output_file: str = None) -> dict:
        """
        Export all invoices as JSON format.

        Args:
            output_file: Optional path to save the JSON file

        Returns:
            Export status and data
        """
        return invoice_tools.export_invoices_as_json(output_file)

    logger.info("Invoice tools registered successfully")
