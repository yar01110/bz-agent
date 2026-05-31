"""Create the single-table DynamoDB table (local or AWS).

Local dev:
    docker run -p 8000:8000 amazon/dynamodb-local
    # set DDB_ENDPOINT_URL=http://localhost:8000 in .env
    python scripts/create_table.py

On AWS, prefer doing this in your CDK/Terraform stack instead — this script is
just for fast local iteration.
"""
from __future__ import annotations

import boto3

from shared.config import get_settings


def main() -> None:
    s = get_settings()
    kwargs = {"region_name": s.aws_region}
    if s.ddb_endpoint_url:
        kwargs["endpoint_url"] = s.ddb_endpoint_url
    ddb = boto3.client("dynamodb", **kwargs)

    existing = ddb.list_tables().get("TableNames", [])
    if s.ddb_table_name in existing:
        print(f"Table {s.ddb_table_name!r} already exists.")
        return

    ddb.create_table(
        TableName=s.ddb_table_name,
        BillingMode="PAY_PER_REQUEST",  # on-demand: no idle cost (pricing objective)
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},   # USER#<id>
            {"AttributeName": "SK", "KeyType": "RANGE"},  # SESSION#<id>
        ],
    )
    print(f"Created table {s.ddb_table_name!r}.")


if __name__ == "__main__":
    main()
