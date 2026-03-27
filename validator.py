import logging
import re
import pandas as pd
from typing import List
from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)


class ItemModel(BaseModel):
    portal: str = Field(..., alias="Portal")
    po_num: str = Field(..., alias="po_num")
    bp_code: str = Field(..., alias="BP CODE")
    address_code: str = Field(..., alias="Address Code")
    kent_sku: str = Field(..., alias="KENT SKU_x")  # Note the _x from your merge
    qty: float = Field(..., alias="Qty", gt=0)
    price: float = Field(..., alias="Price", gt=0)
    emp_code: str = Field(..., alias="Emp Code")
    customer_name: str = Field(..., alias="Customer Name")
    wh_code: str = Field(..., alias="W/H Code")

    # @field_validator("dc_code")
    # @classmethod
    # def validate_dc_code(cls, v: str):
    #     if not re.match(r"^D\d{3}$", v):
    #         raise ValueError("Invalid DC code format")
    #     return v


def validate(df: pd.DataFrame, po_num: str) -> bool:
    """
    Validate dataframe rows using Pydantic schema.
    Returns True if all rows are valid.
    """

    if df.empty:
        logger.error(f"PO {po_num} — DataFrame is empty")
        return False

    # critical_cols = ["KENT SKU_x", "BP CODE", "W/H Code"]
    # for col in critical_cols:
    #     if df[col].isna().any():
    #         missing_count = df[col].isna().sum()
    #         logger.error(f"PO {po_num} — {missing_count} rows failed reference lookup for {col}")
    #         return False

    errors = []
    for idx, row in df.iterrows():
        try:
            # Pydantic matches row keys (aliases) to model fields
            ItemModel(**row.to_dict())
        except ValidationError as e:
            for error in e.errors():
                errors.append(f"Row {idx} | Field: {error['loc']} | Error: {error['msg']}")

    if errors:
        for err in errors:
            logger.error(f"PO {po_num} — Validation error: {err}")
        return False

    logger.info(f"PO {po_num} — Validation passed ({len(df)} rows)")
    return True
