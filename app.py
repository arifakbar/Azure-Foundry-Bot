import os
import traceback

from dotenv import load_dotenv

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ActivityHandler,
    TurnContext
)

from botbuilder.schema import Activity


load_dotenv()

FOUNDRY_ENDPOINT = os.getenv("FOUNDRY_ENDPOINT")
WORKFLOW_NAME = os.getenv("WORKFLOW_NAME")

MICROSOFT_APP_ID = os.getenv("MicrosoftAppId", "")
MICROSOFT_APP_PASSWORD = os.getenv("MicrosoftAppPassword", "")

app = FastAPI()


# --------------------------------------------------
# Foundry helper
# --------------------------------------------------

def invoke_workflow(user_message: str) -> str:

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

                event_type = getattr(event, "type", "")

                if event_type == "response.output_text.done":
                    final_response = event.text

            print("========== RESPONSE ==========")
            print(final_response)
            print("==============================")

            return final_response

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
                    f"Cleanup failed: {cleanup_error}"
                )


# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "workflow": WORKFLOW_NAME
    }


# --------------------------------------------------
# EASY TEST ENDPOINT
# --------------------------------------------------

@app.post("/api/test")
async def test(request: Request):

    try:

        body = await request.json()

        print("========== REQUEST ==========")
        print(body)
        print("=============================")

        user_message = body.get("text", "")

        response = invoke_workflow(user_message)

        return {
            "response": response
        }

    except Exception as ex:

        print(traceback.format_exc())

        return JSONResponse(
            status_code=500,
            content={
                "error": str(ex)
            }
        )


# --------------------------------------------------
# BOT FRAMEWORK
# --------------------------------------------------

settings = BotFrameworkAdapterSettings(
    MICROSOFT_APP_ID,
    MICROSOFT_APP_PASSWORD
)

adapter = BotFrameworkAdapter(settings)


class FoundryBot(ActivityHandler):

    async def on_message_activity(
        self,
        turn_context: TurnContext
    ):

        try:

            user_message = turn_context.activity.text

            print("========== BOT MESSAGE ==========")
            print(user_message)
            print("=================================")

            response = invoke_workflow(user_message)

            await turn_context.send_activity(
                response or "No response."
            )

        except Exception:

            print(traceback.format_exc())

            await turn_context.send_activity(
                "An error occurred."
            )


bot = FoundryBot()


@app.post("/api/messages")
async def messages(request: Request):

    body = await request.json()

    print("========== BOT ACTIVITY ==========")
    print(body)
    print("==================================")

    activity = Activity().deserialize(body)

    auth_header = request.headers.get(
        "Authorization",
        ""
    )

    response = await adapter.process_activity(
        activity,
        auth_header,
        bot.on_turn
    )

    if response:

        return Response(
            content=response.body,
            status_code=response.status
        )

    return Response(status_code=201)