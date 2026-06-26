import json
import logging
from services.llm_client import call_llm
from utils.llm_helpers import parse_llm_json

logger = logging.getLogger(__name__)

# Default extraction schemas per document type
EXTRACTION_SCHEMAS = {
    "invoice": {
        "invoice_number": "",
        "vendor_name": "",
        "vendor_address": "",
        "customer_name": "",
        "date": "",
        "due_date": "",
        "line_items": [],
        "subtotal": "",
        "tax": "",
        "total_amount": "",
        "currency": "",
    },
    "bank_statement": {
        "bank_name": "",
        "account_number": "",
        "statement_period": "",
        "opening_balance": "",
        "closing_balance": "",
        "total_deposits": "",
        "total_withdrawals": "",
        "currency": "",
    },
    "contract": {
        "contract_title": "",
        "parties": [],
        "effective_date": "",
        "expiration_date": "",
        "key_terms": [],
        "governing_law": "",
        "signatures": [],
    },
    "resume": {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "summary": "",
        "skills": [],
        "experience": [],
        "education": [],
    },
    "receipt": {
        "store_name": "",
        "date": "",
        "items": [],
        "subtotal": "",
        "tax": "",
        "total": "",
        "payment_method": "",
    },
    "report": {
        "title": "",
        "author": "",
        "date": "",
        "executive_summary": "",
        "key_findings": [],
        "recommendations": [],
    },
}


async def extract_structured_data(
    text: str,
    document_type: str | None = None,
    custom_fields: list[str] | None = None,
) -> dict:
    """
    Extract structured data from document text.

    Args:
        text:           Document text.
        document_type:  Classification category for selecting the right schema.
        custom_fields:  Optional user-defined fields to extract.

    Returns:
        Dictionary of extracted fields.
    """
    text_sample = text[:5000]

    if custom_fields:
        schema = {field: "" for field in custom_fields}
    elif document_type and document_type in EXTRACTION_SCHEMAS:
        schema = EXTRACTION_SCHEMAS[document_type]
    else:
        schema = {
            "title": "",
            "date": "",
            "author": "",
            "key_information": [],
            "summary": "",
        }

    schema_str = json.dumps(schema, indent=2)

    prompt = f"""Extract structured data from the following document.
Return a valid JSON object matching this schema (fill in the values):

{schema_str}

Rules:
- Return ONLY a valid JSON object, no other text.
- If a field value is not found, use null.
- For list fields, return an array of strings or objects.
- Be accurate; only extract what is explicitly stated.

DOCUMENT TEXT:
{text_sample}

JSON:"""

    try:
        content = await call_llm(prompt, temperature=0.0, max_tokens=2048)
        result = parse_llm_json(content)
        if not result:
            return {"error": "Failed to parse extraction output", "raw_output": content}
        return result
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return {"error": f"Extraction failed: {str(e)}"}
