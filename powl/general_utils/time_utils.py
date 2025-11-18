import pandas as pd


def should_parse_column_as_date(df, column):
    """Check the first non-empty value in a column to decide datetime parsing."""
    try:
        first_val = df[column].dropna().astype(str).iloc[0]
        pd.to_datetime(first_val, errors="raise")
        return True
    except Exception:
        return False
