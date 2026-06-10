import os
import traceback

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    Request
)

from fastapi.responses import (
    JSONResponse
)

from azure.identity import (
    DefaultAzureCredential
)

from azure.ai.projects import (
    AIProjectClient
)

from conversation_store import (
    initialize_table,
    get_conversation_id,
    save_conversation_id,
    delete_conversation_id
)

load_dotenv()

FOUNDRY_ENDPOINT = os.getenv(
    "FOUNDRY_ENDPOINT"
)

WORKFLOW_NAME = os.getenv(
    "WORKFLOW_NAME"
)

app = FastAPI()

initialize_table()


def invoke_workflow(
    user_id: str,
    user_message: str
):

    project_client = AIProjectClient(
        endpoint=FOUNDRY_ENDPOINT,
        credential=DefaultAzureCredential()
    )

    final_response = ""

    with project_client:

        openai_client = (
            project_client.get_openai_client()
        )

        conversation_id = (
            get_conversation_id(user_id)
        )

        if conversation_id:

            print(
                f"Reusing conversation: {conversation_id}"
            )

        else:

            conversation = (
                openai_client.conversations.create()
            )

            conversation_id = (
                conversation.id
            )

            save_conversation_id(
                user_id,
                conversation_id
            )

            print(
                f"Created conversation: {conversation_id}"
            )

        stream = openai_client.responses.create(
            conversation=conversation_id,
            extra_body={
                "agent_reference": {
                    "name": WORKFLOW_NAME,
                    "type": "agent_reference"
                }
            },
            input=user_message,
            stream=True
        )

        for event in stream:

            event_type = getattr(
                event,
                "type",
                ""
            )

            if (
                event_type
                == "response.output_text.done"
            ):
                final_response = event.text

        return final_response


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "workflow": WORKFLOW_NAME
    }


@app.post("/api/test")
async def test(request: Request):

    try:

        body = await request.json()

        user_id = body.get(
            "user_id",
            "default-user"
        )

        user_message = body.get(
            "text",
            ""
        )

        response = invoke_workflow(
            user_id,
            user_message
        )

        return {
            "response": response
        }

    except Exception as ex:

        print(
            traceback.format_exc()
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": str(ex)
            }
        )


@app.post("/api/reset")
async def reset(request: Request):

    try:

        body = await request.json()

        user_id = body.get(
            "user_id"
        )

        delete_conversation_id(
            user_id
        )

        return {
            "message":
            f"Conversation reset for {user_id}"
        }

    except Exception as ex:

        return JSONResponse(
            status_code=500,
            content={
                "error": str(ex)
            }
        )