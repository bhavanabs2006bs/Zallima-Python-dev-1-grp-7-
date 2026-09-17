
import pandas as pd


def clean_customers(records):
    """
    Clean customer records before loading into the database.
    """

    if not records:
        return []

    df = pd.DataFrame(records)

    # Remove duplicate customer IDs
    if "customer_id" in df.columns:
        df = df.drop_duplicates(subset=["customer_id"])

    # Replace empty strings with missing values
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    # Normalize email addresses
    if "email" in df.columns:
        df["email"] = df["email"].apply(
            lambda x: x.strip().lower()
            if isinstance(x, str)
            else x
        )

    # Clean customer names
    if "name" in df.columns:
        df["name"] = df["name"].apply(
            lambda x: x.strip()
            if isinstance(x, str)
            else x
        )

    # Convert missing values to None for Python/SQLAlchemy
    df = df.where(pd.notna(df), None)

    return df.to_dict(orient="records")


def clean_payments(records):
    """
    Clean payment records before loading into the database.
    """

    if not records:
        return []

    df = pd.DataFrame(records)

    # Remove duplicate payment IDs
    if "payment_id" in df.columns:
        df = df.drop_duplicates(subset=["payment_id"])

    # Replace empty strings with missing values
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    # Normalize currency
    if "currency" in df.columns:
        df["currency"] = df["currency"].apply(
            lambda x: x.strip().lower()
            if isinstance(x, str)
            else x
        )

    # Normalize payment status
    if "status" in df.columns:
        df["status"] = df["status"].apply(
            lambda x: x.strip().lower()
            if isinstance(x, str)
            else x
        )

    # Convert amount to numeric
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

    # Convert missing values to None
    df = df.where(pd.notna(df), None)

    return df.to_dict(orient="records")

