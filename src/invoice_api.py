"""FastAPI server for serving invoice UI and API endpoints."""

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .pdf_processor import InvoiceFieldExtractor, process_invoices_in_directory

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Invoice Processor API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize invoice extractor
extractor = InvoiceFieldExtractor()
INVOICE_DIR = "invoices"


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the invoice processor UI."""
    ui_path = Path(__file__).parent / "invoice_ui.html"
    if ui_path.exists():
        return ui_path.read_text()
    return "<h1>Invoice Processor - UI not found</h1>"


@app.get("/api/invoices")
async def get_all_invoices():
    """Get all processed invoices with summary statistics."""
    try:
        result = process_invoices_in_directory(INVOICE_DIR)
        return result
    except Exception as e:
        logger.error(f"Error fetching invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/summary")
async def get_invoice_summary():
    """Get invoice summary statistics."""
    try:
        result = process_invoices_in_directory(INVOICE_DIR)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result.get("summary", {})
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/search")
async def search_invoices(query: str):
    """Search invoices by query string."""
    try:
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter required")
        
        result = process_invoices_in_directory(INVOICE_DIR)
        invoices = result.get("invoices", [])
        query_lower = query.lower()
        
        matches = [
            inv
            for inv in invoices
            if query_lower in inv.get("invoice_number", "").lower()
            or query_lower in inv.get("invoice_date", "")
            or query_lower in inv.get("file_name", "").lower()
            or query_lower in inv.get("vendor_name", "").lower()
        ]
        
        return {
            "query": query,
            "matches": len(matches),
            "invoices": matches
        }
    except Exception as e:
        logger.error(f"Error searching invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/{file_name}")
async def get_invoice_details(file_name: str):
    """Get detailed information for a specific invoice."""
    try:
        pdf_path = Path(INVOICE_DIR) / file_name
        
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        invoice = extractor.extract_invoice_fields(str(pdf_path))
        return invoice.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invoice details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/invoices/export")
async def export_invoices(output_format: str = "json"):
    """Export all invoices in specified format."""
    try:
        result = process_invoices_in_directory(INVOICE_DIR)
        
        if output_format.lower() == "json":
            return result
        elif output_format.lower() == "csv":
            # Simple CSV export
            invoices = result.get("invoices", [])
            if not invoices:
                return {"error": "No invoices to export"}
            
            import csv
            import io
            
            output = io.StringIO()
            fieldnames = [
                "file_name",
                "invoice_number",
                "invoice_date",
                "due_date",
                "vendor_name",
                "customer_name",
                "subtotal",
                "tax_amount",
                "total_amount",
                "confidence_score"
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for inv in invoices:
                row = {field: inv.get(field, "") for field in fieldnames}
                writer.writerow(row)
            
            return {
                "format": "csv",
                "data": output.getvalue(),
                "count": len(invoices)
            }
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
    
    except Exception as e:
        logger.error(f"Error exporting invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices/list/available")
async def list_available_invoices():
    """List all available PDF files in invoices directory."""
    try:
        invoice_dir = Path(INVOICE_DIR)
        if not invoice_dir.exists():
            return {"error": f"Directory not found: {INVOICE_DIR}"}
        
        invoices = list(invoice_dir.glob("*.pdf"))
        return {
            "directory": INVOICE_DIR,
            "count": len(invoices),
            "files": [f.name for f in invoices]
        }
    except Exception as e:
        logger.error(f"Error listing invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Invoice Processor API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
