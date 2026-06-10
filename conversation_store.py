import os

from azure.data.tables import (
    TableServiceClient
)

from azure.identity import (
    DefaultAzureCredential
)


STORAGE_ACCOUNT_NAME = os.getenv(
    "STORAGE_ACCOUNT_NAME"
)

TABLE_NAME = os.getenv(
    "TABLE_NAME",
    "foundryconversations"
)


table_service = TableServiceClient(
    endpoint=f"https://{STORAGE_ACCOUNT_NAME}.table.core.windows.net",
    credential=DefaultAzureCredential()
)

table_client = table_service.get_table_client(
    TABLE_NAME
)


def initialize_table():

    try:

        table_client.create_table()

        print(
            f"Created table: {TABLE_NAME}"
        )

    except Exception:

        print(
            f"Table already exists: {TABLE_NAME}"
        )


def get_conversation_id(
    user_id: str
):

    try:

        entity = table_client.get_entity(
            partition_key="users",
            row_key=user_id
        )

        conversation_id = entity.get(
            "conversation_id"
        )

        print(
            f"Found conversation for {user_id}: {conversation_id}"
        )

        return conversation_id

    except Exception:

        print(
            f"No conversation found for {user_id}"
        )

        return None


def save_conversation_id(
    user_id: str,
    conversation_id: str
):

    entity = {
        "PartitionKey": "users",
        "RowKey": user_id,
        "conversation_id": conversation_id
    }

    table_client.upsert_entity(entity)

    print(
        f"Saved conversation for {user_id}: {conversation_id}"
    )


def delete_conversation_id(
    user_id: str
):

    try:

        table_client.delete_entity(
            partition_key="users",
            row_key=user_id
        )

        print(
            f"Deleted conversation for {user_id}"
        )

    except Exception as ex:

        print(
            f"Delete failed: {str(ex)}"
        )