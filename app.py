import os
import json
import asyncio

from aiohttp import web

from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    ActivityHandler
)
from botbuilder.schema import Activity

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


# ======================
# ENV VARIABLES
# ======================
FOUNDRY_ENDPOINT = os.environ["FOUNDRY_ENDPOINT"]
WORKFLOW_NAME = os.environ["WORKFLOW_NAME"]

MICROSOFT_APP_ID = os.environ["MicrosoftAppId"]
MICROSOFT_APP_PASSWORD = os.environ["MicrosoftAppPassword"]


# ======================
# SIMPLE IN-MEMORY STATE
# (Replace with Redis/Cosmos later)
# ======================
conversation_map = {}


# ======================
# BOT LOGIC
# ======================
class FoundryBot(ActivityHandler):

    async def on_message_activity(self, turn_context: TurnContext):

        user_text = turn_context.activity.text or ""
        bot_conv_id = turn_context.activity.conversation.id

        print("========== BOT REQUEST ==========")
        print(f"Bot Conversation ID: {bot_conv_id}")
        print(f"User Message: {user_text}")
        print("=================================")

        # ---- Map Bot conversation → Foundry conversation ----
        if bot_conv_id in conversation_map:
            foundry_conv_id = conversation_map[bot_conv_id]
        else:
            project_client = AIProjectClient(
                endpoint=FOUNDRY_ENDPOINT,
                credential=DefaultAzureCredential()
            )

            openai_client = project_client.get_openai_client()
            foundry_conv_id = openai_client.conversations.create().id
            conversation_map[bot_conv_id] = foundry_conv_id

        # ---- Call Foundry Workflow ----
        project_client = AIProjectClient(
            endpoint=FOUNDRY_ENDPOINT,
            credential=DefaultAzureCredential()
        )

        with project_client:

            openai_client = project_client.get_openai_client()

            stream = openai_client.responses.create(
                conversation=foundry_conv_id,
                extra_body={
                    "agent_reference": {
                        "name": WORKFLOW_NAME,
                        "type": "agent_reference"
                    }
                },
                input=user_text,
                stream=True
            )

            final_response = ""

            for event in stream:
                if hasattr(event, "text"):
                    final_response += event.text
                if hasattr(event, "delta"):
                    final_response += event.delta

        # ---- Reply to Bot ----
        await turn_context.send_activity(final_response or "No response from workflow")


# ======================
# BOT ADAPTER
# ======================
adapter_settings = BotFrameworkAdapterSettings(
    app_id=MICROSOFT_APP_ID,
    app_password=MICROSOFT_APP_PASSWORD
)

adapter = BotFrameworkAdapter(adapter_settings)
bot = FoundryBot()


# ======================
# HTTP SERVER
# ======================
async def messages(req: web.Request) -> web.Response:

    body = await req.json()
    activity = Activity().deserialize(body)

    auth_header = req.headers.get("Authorization", "")

    response = await adapter.process_activity(
        activity,
        auth_header,
        bot.on_turn
    )

    return web.Response(status=201)


async def health(req):
    return web.Response(text="OK")


app = web.Application()
app.router.add_post("/api/messages", messages)
app.router.add_get("/health", health)


if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8000)