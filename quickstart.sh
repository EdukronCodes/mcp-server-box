#!/bin/bash
# Quick start script for Invoice Processor

set -e

echo "🚀 Invoice Processor - Quick Start"
echo "=================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python --version

# Install dependencies
echo ""
echo "✓ Installing dependencies..."
pip install -e . -q > /dev/null 2>&1 || true

# Display available commands
echo ""
echo "📋 Available Commands:"
echo ""
echo "1. Start Web UI Server:"
echo "   python -m src.invoice_api"
echo "   Then open: http://localhost:8000"
echo ""
echo "2. Test PDF Processing:"
echo "   python -c \"from src.pdf_processor import process_invoices_in_directory; import json; print(json.dumps(process_invoices_in_directory('invoices'), indent=2))\""
echo ""
echo "3. Start MCP Box Server with Invoice Tools:"
echo "   mcp-server-box --transport stdio"
echo ""
echo "4. Use Python Module:"
echo "   python -c \"from src.pdf_processor import InvoiceFieldExtractor; e = InvoiceFieldExtractor(); inv = e.extract_invoice_fields('invoices/demo-invoice-20tax-2.pdf'); print(inv.to_dict())\""
echo ""
echo "✓ Setup complete! Choose an option above to get started."
