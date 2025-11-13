# Invoice Processor with MCP Box Server

A multi-agent PDF invoice processor that extracts key fields from invoices and displays them in a beautiful web UI, integrated with the MCP Box server.

## Features

✨ **Multi-Agent PDF Processing**
- Text extraction from PDF files
- Pattern-based field detection with confidence scoring
- Automatic extraction of invoice number, date, amounts, vendor info
- Batch processing of multiple invoices

🎯 **Key Fields Extraction**
- Invoice Number
- Invoice Date & Due Date
- Vendor Name & Address
- Customer Name & Address
- Subtotal, Tax, and Total Amounts
- Currency detection

📊 **Web UI Dashboard**
- Beautiful, responsive invoice card grid
- Real-time search and filtering
- Invoice statistics and summary
- Detailed modal view for each invoice
- Export to JSON/CSV

🔌 **MCP Server Integration**
- Invoice processing tools available as MCP tools
- RESTful API endpoints
- Seamless Box integration

## Project Structure

```
src/
├── pdf_processor.py          # Core PDF processing with multi-agent approach
├── tools/
│   └── box_tools_invoices.py # Invoice tools implementation
├── tool_registry/
│   └── invoice_tools.py      # MCP tool registry for invoices
├── invoice_ui.html           # Web dashboard UI
├── invoice_api.py            # FastAPI server for UI and API
└── server.py                 # MCP server configuration (updated)

invoices/                      # Directory with sample PDF invoices
├── demo-invoice-20tax-2.pdf
├── demo-invoice-20tax-9.pdf
├── demo-invoice-no-tax-6.pdf
├── demo-invoice-no-tax-8.pdf
└── demo-invoice-no-tax-9.pdf
```

## Installation

### Prerequisites
- Python 3.13+
- pip

### Setup

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Verify PDF processing library is installed:**
   ```bash
   pip install PyPDF2>=4.0.0 uvicorn>=0.30.0
   ```

## Usage

### Option 1: Use MCP Tools with Box Server

The invoice processing tools are available as MCP tools in the Box server:

```python
# Available MCP Tools:
- process_single_invoice(file_name)      # Process one invoice
- process_all_invoices()                 # Process all invoices
- list_invoices()                        # List available invoices
- get_invoice_summary()                  # Get summary statistics
- search_invoices(query)                 # Search invoices
- get_invoice_details(file_name)         # Get full invoice details
- export_invoices(output_file)           # Export as JSON
```

### Option 2: Use Web Dashboard

1. **Start the FastAPI server:**
   ```bash
   cd /workspaces/mcp-server-box
   python -m src.invoice_api
   ```

2. **Open in browser:**
   ```
   http://localhost:8000
   ```

3. **Features available:**
   - View all invoices in grid format
   - Search by invoice number, date, or vendor
   - Click cards to view detailed information
   - Export all invoices as JSON
   - Real-time statistics

### Option 3: Use as Python Module

```python
from pdf_processor import InvoiceFieldExtractor, process_invoices_in_directory

# Process single invoice
extractor = InvoiceFieldExtractor()
invoice = extractor.extract_invoice_fields('invoices/demo-invoice-20tax-2.pdf')
print(invoice.to_dict())

# Process all invoices
result = process_invoices_in_directory('invoices')
print(f"Total amount: ${result['summary']['total_amount']}")
```

## API Endpoints

The FastAPI server provides the following endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serve invoice UI dashboard |
| GET | `/api/invoices` | Get all invoices with summary |
| GET | `/api/invoices/summary` | Get summary statistics |
| GET | `/api/invoices/search?query=X` | Search invoices |
| GET | `/api/invoices/{file_name}` | Get invoice details |
| GET | `/api/invoices/list/available` | List all PDF files |
| POST | `/api/invoices/export` | Export invoices (JSON/CSV) |
| GET | `/health` | Health check |

## Example Response

```json
{
  "file_name": "demo-invoice-20tax-2.pdf",
  "invoice_number": "INV-20241113-001",
  "invoice_date": "11/13/2024",
  "due_date": "12/13/2024",
  "vendor_name": "Acme Corporation",
  "vendor_address": "123 Business St",
  "customer_name": "Widget Inc",
  "customer_address": "456 Industrial Ave",
  "subtotal": 5000.00,
  "tax_amount": 1000.00,
  "total_amount": 6000.00,
  "currency": "USD",
  "confidence_score": 0.85
}
```

## Multi-Agent Processing Architecture

The PDF processor uses a multi-agent approach:

1. **PDF Reader Agent** - Extracts raw text from PDF files
2. **Pattern Extractor Agent** - Uses regex patterns to identify structured fields
3. **Amount Extractor Agent** - Specializes in monetary values
4. **Vendor Info Agent** - Identifies vendor and customer information
5. **Confidence Scorer** - Calculates overall extraction confidence

Each agent has specific responsibilities and confidence scoring, allowing for robust extraction even from varied invoice formats.

## Field Extraction Patterns

The system includes pattern recognition for:

- **Invoice Numbers**: Common patterns like "Invoice #", "INV-", "Invoice Number:"
- **Dates**: Various date formats (MM/DD/YYYY, DD-MM-YYYY, etc.)
- **Amounts**: Currency values with optional $ symbol
- **Vendor Info**: Extracted from document headers

Confidence scoring helps identify the most reliable extractions.

## Configuration

### Invoice Directory
Default: `invoices/`
Can be customized by passing `invoice_directory` parameter to `InvoiceTools`

### API Server
- Default Host: `0.0.0.0`
- Default Port: `8000`
- Modify in `invoice_api.py` if needed

## Testing

Run with sample invoices:

```bash
# Using Python module directly
python -c "from pdf_processor import process_invoices_in_directory; import json; print(json.dumps(process_invoices_in_directory('invoices'), indent=2))"

# Using API
curl http://localhost:8000/api/invoices
```

## MCP Server Integration

To use with the MCP Box server:

1. Invoice tools are automatically registered when the MCP server starts
2. Access via MCP protocol as `process_single_invoice`, `process_all_invoices`, etc.
3. Integrate with Box AI workflows

```bash
# Start MCP server with invoice tools enabled
mcp-server-box --transport stdio
```

## Error Handling

- Graceful handling of missing or corrupted PDFs
- Confidence scores indicate extraction reliability
- Detailed error messages in responses
- Fallback patterns for common invoice formats

## Performance

- Single invoice processing: ~100-500ms (depends on PDF size)
- Batch processing: Linear time with number of invoices
- Web UI: Sub-second searches and filtering

## Limitations & Future Improvements

Current:
- Pattern-based extraction may vary with invoice layouts
- No table parsing for line items
- Limited to common invoice formats

Future:
- OCR support for scanned invoices
- ML-based field detection
- Line item extraction
- Multi-language support
- Custom pattern training

## Contributing

Improvements welcome! Areas for enhancement:
- Additional invoice format patterns
- OCR integration
- Custom field configuration
- Advanced statistical analysis

## License

MIT - See LICENSE file for details

## Support

For issues or questions:
1. Check the sample invoices in `/invoices` folder
2. Review error messages and confidence scores
3. Adjust patterns in `PatternExtractor` class if needed
