import re
import json
import time
import logging
import ollama
from typing import List, Dict


logger = logging.getLogger(__name__)


_PROMPT = """
Extract item details from the purchase order text.
 
Return ONLY valid JSON. Do NOT include explanations or markdown.

Format:
 
{
  "items": [
    {
      "Article Code": "",
      "Qty": "",
      "Price": ""
    }
  ]
}
 
If no items are found return:
{"items":[]}
 
Text:
"""


def get_structured_data(text: str, config) -> List[Dict[str, str]]:
    """
    Sends extracted PDF text to the LLM and returns a list of item dicts.
    Retries on failure as per config settings.
    Returns [] if all attempts fail.
    """
    model       = config.get("llm", "model")
    temperature = config.getfloat("llm", "temperature")
    max_retries = config.getint("llm", "max_retries")
    retry_delay = config.getfloat("llm", "retry_delay")
    raw = ""

    for attempt in range(1, max_retries + 1):
        try:
            response = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": _PROMPT + text}],
                options={"temperature": temperature}
            )

            raw = response["message"]["content"]

            logger.info(f"LLLM response: {raw}")
 
            # Strip markdown code fences if present
            # raw = re.sub(r"```json|```", "", raw).strip()
            raw = re.sub(r"```(?:json)?", "", raw).strip()
 
            data = json.loads(raw)
            items = data.get("items", [])
 
            if not items:
                logger.warning("LLM returned empty items list")
                return []
 
            logger.info(f"LLM extracted {len(items)} item(s)")
            return items
 
        except json.JSONDecodeError as e:
            logger.error(f"LLM JSON parse failed (attempt {attempt}/{max_retries}): {e}")
            logger.debug(f"Raw LLM output was: {raw!r}")
 
        except Exception as e:
            logger.error(f"LLM call failed (attempt {attempt}/{max_retries}): {e}", exc_info=True)
 
        if attempt < max_retries:
            logger.info(f"Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
 
    logger.error("All LLM attempts exhausted — skipping this file")
    return []
