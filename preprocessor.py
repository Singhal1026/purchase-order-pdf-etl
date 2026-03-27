import logging 
import pandas as pd
from typing import List, Dict

logger = logging.getLogger(__name__)


def preprocess(items: List[Dict[str, str]], po_num: str, dc_code: str, df_ref: pd.DataFrame) -> pd.DataFrame:
    """
    Takes list of item dicts and returns cleaned DataFrame with DC code and PO number.
    Drops items missing any of the required fields.
    """
    clean_items = []

    for item in items:
        if all(item.get(k) for k in ("Article Code", "Qty", "Price")):
            clean_items.append(item)

    if not clean_items:
        logger.warning(f"No valid items found for PO {po_num} at DC {dc_code}")
        return pd.DataFrame()  # Return empty DataFrame if no valid items

    df = pd.DataFrame(clean_items)
    df["po_num"] = po_num
    df["dc_code"] = dc_code

    df['Article Code'] = df['Article Code'].astype(str).str.strip()
    df_ref['Article code'] = df_ref['Article code'].astype(str).str.strip()

    merged_df = pd.merge(
        df,
        df_ref,
        left_on='Article Code',
        right_on='Article code',
        how='left'
    )

    merged_df = merged_df[['Qty', 'Price', 'po_num', 'dc_code', 'SKU']]

    final_merged = pd.merge(
        merged_df, 
        df_ref, 
        left_on='dc_code', 
        right_on='facility_name 2',
        how='left'
    )

    final_merged['Portal'] = 'ABC'
    final_merged['Customer Name'] = 'ABCD'

    # final_output = final_merged.fillna("")
    final_merged['Qty'] = final_merged['Qty'].fillna(0)
    final_merged['Price'] = final_merged['Price'].fillna(0)

    str_cols = ['Portal', 'Customer Name', 'BP CODE', 'Address Code']
    final_merged[str_cols] = final_merged[str_cols].fillna("")

    # print(final_output.columns)

    # df["Qty"] = pd.to_numeric(df["Qty"], errors="coerce")
    # df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    # df = df.dropna(subset=["Qty", "Price"])

    try:
        final_merged = final_merged[[
            'Portal', 
            'po_num',       
            'BP CODE', 
            'Address Code', 
            'SKU_x', 
            'Qty', 
            'Price', 
            'Emp Code', 
            'Customer Name', 
            'W/H Code'
        ]]

        return final_merged
    except KeyError as e:
        logger.error(f"Mapping failed for PO {po_num}. Missing column in Reference Excel: {e}")
        return pd.DataFrame()