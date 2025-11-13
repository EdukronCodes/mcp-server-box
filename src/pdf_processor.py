"""PDF content reader and invoice field extractor using multi-agent approach."""

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

logger = logging.getLogger(__name__)


@dataclass
class InvoiceField:
    """Represents an extracted invoice field."""

    name: str
    value: Any
    confidence: float = 1.0
    source: str = "extracted"


@dataclass
class ExtractedInvoice:
    """Represents a complete extracted invoice."""

    file_name: str
    invoice_number: str = ""
    invoice_date: str = ""
    due_date: str = ""
    vendor_name: str = ""
    vendor_address: str = ""
    customer_name: str = ""
    customer_address: str = ""
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    currency: str = "USD"
    line_items: list = field(default_factory=list)
    raw_text: str = ""
    confidence_score: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class PDFContentReader:
    """Reads and extracts text from PDF files."""

    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """Extract text from PDF file."""
        if PyPDF2 is None:
            raise ImportError("PyPDF2 is required. Install with: pip install PyPDF2")

        try:
            text_content = []
            with open(pdf_path, "rb") as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())
            return "\n".join(text_content)
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise


class PatternExtractor:
    """Extracts specific fields using regex patterns."""

    # Pattern definitions for common invoice fields
    PATTERNS = {
        "invoice_number": [
            r"Invoice\s*(?:Number|No\.?|#)[\s:]*([A-Z0-9\-]+)",
            r"Invoice\s*#?[\s:]*([A-Z0-9\-]{4,})",
            r"INV[\s\-]?([A-Z0-9\-]+)",
        ],
        "invoice_date": [
            r"Invoice\s*Date[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"Date[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        ],
        "due_date": [
            r"Due\s*Date[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"Payment\s*Due[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        ],
        "total_amount": [
            r"Total[\s:]*\$?([0-9,]+\.[0-9]{2})",
            r"Grand\s*Total[\s:]*\$?([0-9,]+\.[0-9]{2})",
            r"TOTAL[\s:]*\$?([0-9,]+\.[0-9]{2})",
        ],
        "tax_amount": [
            r"Tax[\s:]*\$?([0-9,]+\.[0-9]{2})",
            r"GST[\s:]*\$?([0-9,]+\.[0-9]{2})",
            r"VAT[\s:]*\$?([0-9,]+\.[0-9]{2})",
        ],
        "subtotal": [
            r"Subtotal[\s:]*\$?([0-9,]+\.[0-9]{2})",
            r"Sub[\s-]?Total[\s:]*\$?([0-9,]+\.[0-9]{2})",
        ],
    }

    @staticmethod
    def extract_field(text: str, field_type: str) -> tuple[str | None, float]:
        """Extract a field using patterns with confidence scoring."""
        patterns = PatternExtractor.PATTERNS.get(field_type, [])

        for pattern_idx, pattern in enumerate(patterns):
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Higher confidence for earlier patterns
                confidence = 1.0 - (pattern_idx * 0.1)
                return value, confidence

        return None, 0.0

    @staticmethod
    def extract_vendor_name(text: str) -> tuple[str, float]:
        """Extract vendor name from invoice."""
        lines = text.split("\n")
        # Usually vendor name is in the first few non-empty lines
        for line in lines[:20]:
            stripped = line.strip()
            if stripped and len(stripped) > 5 and len(stripped) < 100:
                # Skip common header words
                if not any(
                    keyword in stripped.lower()
                    for keyword in [
                        "invoice",
                        "bill",
                        "receipt",
                        "quote",
                        "date:",
                        "invoice #",
                    ]
                ):
                    return stripped, 0.7
        return "", 0.0

    @staticmethod
    def extract_amounts(text: str) -> dict[str, tuple[float, float]]:
        """Extract all amounts from text."""
        amounts = {}

        # Extract total
        total_str, total_conf = PatternExtractor.extract_field(text, "total_amount")
        if total_str:
            amounts["total"] = (
                float(total_str.replace(",", "").replace("$", "")),
                total_conf,
            )

        # Extract tax
        tax_str, tax_conf = PatternExtractor.extract_field(text, "tax_amount")
        if tax_str:
            amounts["tax"] = (
                float(tax_str.replace(",", "").replace("$", "")),
                tax_conf,
            )

        # Extract subtotal
        subtotal_str, subtotal_conf = PatternExtractor.extract_field(
            text, "subtotal"
        )
        if subtotal_str:
            amounts["subtotal"] = (
                float(subtotal_str.replace(",", "").replace("$", "")),
                subtotal_conf,
            )

        return amounts


class InvoiceFieldExtractor:
    """Multi-agent approach to extract invoice fields."""

    def __init__(self):
        """Initialize extractor with PDF reader and pattern matcher."""
        self.pdf_reader = PDFContentReader()
        self.pattern_extractor = PatternExtractor()

    def extract_invoice_fields(self, pdf_path: str) -> ExtractedInvoice:
        """Extract invoice fields from PDF using multi-agent approach."""
        file_name = Path(pdf_path).name
        invoice = ExtractedInvoice(file_name=file_name)

        try:
            # Agent 1: Extract raw text
            raw_text = self.pdf_reader.extract_text(pdf_path)
            invoice.raw_text = raw_text

            # Agent 2: Extract structured fields using patterns
            invoice_number, inv_conf = self.pattern_extractor.extract_field(
                raw_text, "invoice_number"
            )
            invoice.invoice_number = invoice_number or ""

            invoice_date, date_conf = self.pattern_extractor.extract_field(
                raw_text, "invoice_date"
            )
            invoice.invoice_date = invoice_date or ""

            due_date, due_conf = self.pattern_extractor.extract_field(
                raw_text, "due_date"
            )
            invoice.due_date = due_date or ""

            # Agent 3: Extract amounts
            amounts = self.pattern_extractor.extract_amounts(raw_text)
            if "total" in amounts:
                invoice.total_amount, _ = amounts["total"]
            if "tax" in amounts:
                invoice.tax_amount, _ = amounts["tax"]
            if "subtotal" in amounts:
                invoice.subtotal, _ = amounts["subtotal"]

            # Agent 4: Extract vendor and customer info
            vendor_name, vendor_conf = self.pattern_extractor.extract_vendor_name(
                raw_text
            )
            invoice.vendor_name = vendor_name

            # Calculate overall confidence
            confidences = [
                inv_conf if invoice.invoice_number else 0,
                date_conf if invoice.invoice_date else 0,
                0.8 if invoice.total_amount > 0 else 0,
            ]
            valid_confidences = [c for c in confidences if c > 0]
            invoice.confidence_score = (
                sum(valid_confidences) / len(valid_confidences)
                if valid_confidences
                else 0
            )

            logger.info(f"Successfully extracted invoice from {file_name}")

        except Exception as e:
            logger.error(f"Error extracting invoice fields from {pdf_path}: {e}")

        return invoice

    def extract_multiple_invoices(self, directory: str) -> list[ExtractedInvoice]:
        """Extract invoices from all PDFs in a directory."""
        invoices = []
        pdf_dir = Path(directory)

        if not pdf_dir.exists():
            logger.warning(f"Directory not found: {directory}")
            return invoices

        for pdf_file in pdf_dir.glob("*.pdf"):
            try:
                invoice = self.extract_invoice_fields(str(pdf_file))
                invoices.append(invoice)
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")

        return invoices


def process_invoices_in_directory(directory: str) -> dict:
    """Process all invoices in a directory and return results."""
    extractor = InvoiceFieldExtractor()
    invoices = extractor.extract_multiple_invoices(directory)

    return {
        "total_processed": len(invoices),
        "invoices": [inv.to_dict() for inv in invoices],
        "summary": {
            "total_amount": sum(inv.total_amount for inv in invoices),
            "total_tax": sum(inv.tax_amount for inv in invoices),
            "average_confidence": (
                sum(inv.confidence_score for inv in invoices) / len(invoices)
                if invoices
                else 0
            ),
        },
    }
