"""
Extraction API — structured data extraction and AI insights report.
"""

from fastapi import APIRouter, HTTPException, Depends
from database.models import ExtractionRequest, ExtractionResponse, ReportResponse
from agents.extraction_agent import extract_data
from agents.summarization_agent import get_summary
from services.rag_service import generate_insights
from database.db import get_db
from bson import ObjectId
from services.auth_middleware import get_current_user

router = APIRouter(tags=["Extraction"])


@router.post("/extract-data", response_model=ExtractionResponse)
async def extract_data_endpoint(request: ExtractionRequest, current_user: dict = Depends(get_current_user)):
    """
    Extract structured data from a document.
    Automatically selects the right schema based on document classification.
    """
    try:
        result = await extract_data(request.document_id, request.fields)
        return ExtractionResponse(
            document_id=result["document_id"],
            extracted_data=result["extracted_data"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.get("/report/{document_id}", response_model=ReportResponse)
async def generate_report(document_id: str, current_user: dict = Depends(get_current_user)):
    """
    Generate a comprehensive AI insights report for a document.
    Includes: summary, structured data, and key insights.
    """
    db = get_db()

    # Fetch document
    doc = await db.documents.find_one({"_id": ObjectId(document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Get summary
        summary_result = await get_summary(document_id)
        summary = summary_result["summary"]

        # Get extracted data
        extraction_result = await extract_data(document_id)
        extracted = extraction_result["extracted_data"]

        # Generate insights
        text = doc.get("text_content", "")
        classification = doc.get("classification")
        insights = await generate_insights(text, classification)

        return ReportResponse(
            document_id=document_id,
            filename=doc.get("original_name", ""),
            classification=classification,
            summary=summary,
            extracted_data=extracted,
            insights=insights,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
