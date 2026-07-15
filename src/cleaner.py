"""Deterministic cleaning and traceable data classification."""

from __future__ import annotations

from dataclasses import dataclass
import logging

import pandas as pd

from src.models import DataQualityReport


LOGGER = logging.getLogger(__name__)
TEXT_COLUMNS = ["order_id", "region", "category", "product", "status"]
VALID_STATUSES = {"已完成", "已退款", "已取消", "未知状态"}
RULES = [
    "字符串字段去除前后空格",
    "缺失地区填充为未知地区，缺失品类填充为未分类",
    "缺失折扣填充为 0",
    "重复订单保留第一条，其余进入拒绝集",
    "关键字段或业务数值非法的记录进入拒绝集",
    "非法日期进入部分有效集，不参与时间趋势",
]


@dataclass
class CleaningResult:
    clean_df: pd.DataFrame
    rejected_df: pd.DataFrame
    partial_df: pd.DataFrame
    quality_report: DataQualityReport


class DataCleaner:
    def clean(self, raw_df: pd.DataFrame) -> CleaningResult:
        frame = raw_df.copy(deep=True)
        frame.insert(0, "source_row", range(2, len(frame) + 2))

        for column in TEXT_COLUMNS:
            frame[column] = frame[column].astype("string").str.strip()
            frame[column] = frame[column].replace("", pd.NA)

        missing_counts = {
            column: int(frame[column].isna().sum())
            for column in frame.columns
            if column != "source_row"
        }

        raw_quantity = frame["quantity"].copy()
        raw_price = frame["unit_price"].copy()
        raw_discount = frame["discount"].copy()
        raw_date = frame["order_date"].copy()

        frame["quantity"] = pd.to_numeric(frame["quantity"], errors="coerce")
        frame["unit_price"] = pd.to_numeric(frame["unit_price"], errors="coerce")
        frame["discount"] = pd.to_numeric(frame["discount"], errors="coerce")
        frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")

        discount_missing = raw_discount.isna() | raw_discount.astype("string").str.strip().eq("")
        frame.loc[discount_missing, "discount"] = 0.0
        frame["region"] = frame["region"].fillna("未知地区")
        frame["category"] = frame["category"].fillna("未分类")
        frame["status"] = frame["status"].fillna("未知状态")

        duplicate = frame["order_id"].notna() & frame["order_id"].duplicated(keep="first")
        quantity_parse = raw_quantity.notna() & frame["quantity"].isna()
        fractional_quantity = frame["quantity"].notna() & frame["quantity"].mod(1).ne(0)
        price_parse = raw_price.notna() & frame["unit_price"].isna()
        discount_parse = ~discount_missing & frame["discount"].isna()
        invalid_date = raw_date.notna() & frame["order_date"].isna()
        invalid_status = ~frame["status"].isin(VALID_STATUSES)

        reasons: list[list[str]] = [[] for _ in range(len(frame))]
        issues: list[list[str]] = [[] for _ in range(len(frame))]

        def mark(mask: pd.Series, target: list[list[str]], reason: str) -> None:
            for position in mask.to_numpy().nonzero()[0]:
                target[position].append(reason)

        mark(frame["order_id"].isna(), reasons, "missing_order_id")
        mark(frame["product"].isna(), reasons, "missing_product")
        mark(duplicate, reasons, "duplicate_order_id")
        mark(quantity_parse | frame["quantity"].isna(), reasons, "invalid_quantity")
        mark(fractional_quantity, reasons, "non_integer_quantity")
        mark(frame["quantity"].notna() & frame["quantity"].le(0), reasons, "non_positive_quantity")
        mark(price_parse | frame["unit_price"].isna(), reasons, "invalid_unit_price")
        mark(frame["unit_price"].notna() & frame["unit_price"].le(0), reasons, "non_positive_unit_price")
        mark(discount_parse, reasons, "invalid_discount")
        mark(frame["discount"].notna() & ~frame["discount"].between(0, 1), reasons, "discount_out_of_range")
        mark(invalid_date | raw_date.isna(), issues, "invalid_date")
        mark(invalid_status, issues, "invalid_status")

        frame["rejection_reasons"] = reasons
        frame["quality_issues"] = issues
        rejected_mask = frame["rejection_reasons"].str.len().gt(0)
        partial_mask = ~rejected_mask & frame["quality_issues"].str.len().gt(0)
        valid_mask = ~rejected_mask & ~partial_mask

        accepted = frame.loc[~rejected_mask].copy()
        accepted["quantity"] = accepted["quantity"].astype(int)
        accepted["sales_amount"] = (
            accepted["quantity"] * accepted["unit_price"] * (1 - accepted["discount"])
        ).round(2)

        invalid_counts = {
            "missing_order_id": int(frame["order_id"].isna().sum()),
            "missing_product": int(frame["product"].isna().sum()),
            "duplicate_order_id": int(duplicate.sum()),
            "invalid_date": int((invalid_date | raw_date.isna()).sum()),
            "invalid_quantity": int((quantity_parse | frame["quantity"].isna()).sum()),
            "non_integer_quantity": int(fractional_quantity.sum()),
            "non_positive_quantity": int((frame["quantity"].notna() & frame["quantity"].le(0)).sum()),
            "invalid_unit_price": int((price_parse | frame["unit_price"].isna()).sum()),
            "non_positive_unit_price": int((frame["unit_price"].notna() & frame["unit_price"].le(0)).sum()),
            "invalid_discount": int(discount_parse.sum()),
            "discount_out_of_range": int((frame["discount"].notna() & ~frame["discount"].between(0, 1)).sum()),
            "invalid_status": int(invalid_status.sum()),
        }

        report = DataQualityReport(
            raw_rows=len(frame),
            valid_rows=int(valid_mask.sum()),
            partial_rows=int(partial_mask.sum()),
            rejected_rows=int(rejected_mask.sum()),
            duplicate_rows=int(duplicate.sum()),
            missing_counts=missing_counts,
            invalid_counts=invalid_counts,
            applied_rules=RULES,
        )
        LOGGER.info(
            "Cleaned CSV raw=%s accepted=%s partial=%s rejected=%s",
            len(frame),
            len(accepted),
            report.partial_rows,
            report.rejected_rows,
        )
        return CleaningResult(
            clean_df=accepted.reset_index(drop=True),
            rejected_df=frame.loc[rejected_mask].reset_index(drop=True),
            partial_df=accepted.loc[accepted["quality_issues"].str.len().gt(0)].reset_index(drop=True),
            quality_report=report,
        )
