from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from dotenv import load_dotenv

import os
import traceback

app = FastAPI()

load_dotenv()

FOUNDRY_ENDPOINT = os.getenv("FOUNDRY_ENDPOINT")
WORKFLOW_NAME = os.getenv("WORKFLOW_NAME")


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "workflow": WORKFLOW_NAME
    }


@app.post("/api/messages")
async def messages(request: Request):

    try:

        data = await request.json()

        print("========== REQUEST ==========")
        print(data)
        print("=============================")

        user_message = data.get("text", "").strip()

        if not user_message:

            return JSONResponse(
                status_code=400,
                content={
                    "error": "text field is required"
                }
            )

        project_client = AIProjectClient(
            endpoint=FOUNDRY_ENDPOINT,
            credential=DefaultAzureCredential()
        )

        final_response = ""

        with project_client:

            openai_client = project_client.get_openai_client()

            conversation = openai_client.conversations.create()

            print(f"Conversation created: {conversation.id}")

            try:

                stream = openai_client.responses.create(
                    conversation=conversation.id,
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

                    print(event)

                    event_type = getattr(event, "type", "")

                    if event_type == "response.output_text.done":
                        final_response = event.text

                print("========== RESPONSE ==========")
                print(final_response)
                print("==============================")

                return {
                    "response": final_response
                }

            finally:

                try:

                    openai_client.conversations.delete(
                        conversation_id=conversation.id
                    )

                    print(
                        f"Conversation deleted: {conversation.id}"
                    )

                except Exception as cleanup_error:

                    print(
                        f"Conversation cleanup failed: {cleanup_error}"
                    )

    except Exception as ex:

        print("========== ERROR ==========")
        print(str(ex))
        print(traceback.format_exc())
        print("===========================")

        return JSONResponse(
            status_code=500,
            content={
                "error": str(ex)
            }
        )