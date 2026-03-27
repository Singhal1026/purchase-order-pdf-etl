import re
import logging
import pdfplumber



logger = logging.getLogger(__name__)


_SPLIT_START = "PLEASE SUPPLY IN GOOD ORDER AND CONDITION"
_SPLIT_END_1 = "Signed................................."
_SPLIT_END_2 = "This is system generated Purchase"



def extract_text_from_pdf(pdf_path: str) -> tuple[str, str, str]:
    """
    Returns (dc_code, po_number, items_text).
    Returns ("", "", "") if the PDF cannot be parsed.
    """

    try:
        all_pages = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_pages.append(page_text)

        if not all_pages:
            logger.warning(f"No text found in PDF: {pdf_path}")
            return "", "", ""
        
        full_text = "\n".join(all_pages)

        lines = full_text.split("\n")
        text = "\n".join(lines[5:])

        # Extract DC code and PO number using regex
        dc_match  = re.search(r"\bD\d{3}\b", text)
        po_match  = re.search(r"PURCHASE\s*ORDER\s*:?\s*(\d+)", text)
 
        dc_code = dc_match.group(0)  if dc_match else ""
        po_num  = po_match.group(1)  if po_match else ""

        if not dc_code:
            logger.warning(f"No DC code found in: {pdf_path}")
            return "", "", ""

        if not po_num:
            logger.warning(f"No PO number found in: {pdf_path}")
            return "", "", ""
        
        
        # Trim text to just the items table
        if _SPLIT_START in text:
            text = text.split(_SPLIT_START)[1].strip()
 
        if _SPLIT_END_1 in text:
            text = text.split(_SPLIT_END_1)[0].strip()
        elif _SPLIT_END_2 in text:
            text = text.split(_SPLIT_END_2)[0].strip()
        
        # Start from the Article Code header
        table_start = re.search(r"Article\s*Code", text)
        if table_start:
            text = text[table_start.start():]
 
        logger.info(f"{pdf_path} — Extracted PO: {po_num} | DC: {dc_code}")
        return dc_code, po_num, text


    except Exception as e:
        logger.error(f"Error extracting text from PDF: {pdf_path} — {e}", exc_info=True)
        return "", "", ""
