import os
import traceback

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    Request,
    Response
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

from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ActivityHandler,
    TurnContext
)

from botbuilder.schema import (
    Activity
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

MICROSOFT_APP_ID = os.getenv(
    "MicrosoftAppId",
    ""
)

MICROSOFT_APP_PASSWORD = os.getenv(
    "MicrosoftAppPassword",
    ""
)

app = FastAPI()

initialize_table()

# --------------------------------------------------
# BOT FRAMEWORK
# --------------------------------------------------

settings = BotFrameworkAdapterSettings(
    app_id=MICROSOFT_APP_ID,
    app_password=MICROSOFT_APP_PASSWORD
)

adapter = BotFrameworkAdapter(settings)

# --------------------------------------------------
# FOUNDRY
# --------------------------------------------------


def invoke_workflow(
    user_id: str,
    user_message: str
) -> str:

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

        print("========== RESPONSE ==========")
        print(final_response)
        print("==============================")

        return final_response


# --------------------------------------------------
# BOT
# --------------------------------------------------

class FoundryBot(ActivityHandler):

    async def on_message_activity(
        self,
        turn_context: TurnContext
    ):

        try:

            user_message = (
                turn_context.activity.text
            )

            user_id = (
                turn_context.activity.from_property.id
            )

            print("========== USER ==========")
            print(user_id)

            print("========== MESSAGE ==========")
            print(user_message)

            # response = invoke_workflow(
            #     user_id,
            #     user_message
            # )

            response = "Hello from bot"

            await turn_context.send_activity(
                response
            )

        except Exception:

            print(
                traceback.format_exc()
            )

            await turn_context.send_activity(
                "An error occurred."
            )

    async def on_members_added_activity(
        self,
        members_added,
        turn_context: TurnContext
    ):

        for member in members_added:

            if (
                member.id
                != turn_context.activity.recipient.id
            ):

                await turn_context.send_activity(
                    "Hello from Foundry Bot."
                )


bot = FoundryBot()

# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "workflow": WORKFLOW_NAME
    }

# --------------------------------------------------
# TEST API
# --------------------------------------------------

@app.post("/api/test")
async def test(
    request: Request
):

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

        return JSONResponse(
            status_code=500,
            content={
                "error": str(ex)
            }
        )

# --------------------------------------------------
# RESET
# --------------------------------------------------

@app.post("/api/reset")
async def reset(
    request: Request
):

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

# --------------------------------------------------
# BOT FRAMEWORK ENDPOINT
# --------------------------------------------------

@app.post("/api/messages")
async def messages(
    request: Request
):

    body = await request.json()

    print(body)

    activity = Activity().deserialize(
        body
    )

    auth_header = request.headers.get(
        "Authorization",
        ""
    )

    await adapter.process_activity(
        activity,
        auth_header,
        bot.on_turn
    )

    return Response(
        status_code=200
    )