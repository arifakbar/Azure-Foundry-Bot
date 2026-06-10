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

from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ActivityHandler,
    TurnContext
)

from botbuilder.schema import (
    Activity
)

load_dotenv()

MICROSOFT_APP_ID = os.getenv(
    "MicrosoftAppId",
    ""
)

MICROSOFT_APP_PASSWORD = os.getenv(
    "MicrosoftAppPassword",
    ""
)

MICROSOFT_APP_TYPE = os.getenv(
    "MicrosoftAppType"
)

MICROSOFT_APP_TENANT_ID = os.getenv(
    "MicrosoftAppTenantId"
)

print("")
print("====================================")
print("BOT STARTUP")
print("====================================")
print("APP ID =", MICROSOFT_APP_ID)
print(
    "PASSWORD PRESENT =",
    bool(MICROSOFT_APP_PASSWORD)
)
print(
    "APP TYPE =",
    MICROSOFT_APP_TYPE
)
print(
    "TENANT ID =",
    MICROSOFT_APP_TENANT_ID
)
print("====================================")
print("")

app = FastAPI()

settings = BotFrameworkAdapterSettings(
    app_id=MICROSOFT_APP_ID,
    app_password=MICROSOFT_APP_PASSWORD
)

print("")
print("========== ADAPTER SETTINGS ==========")
print(settings.__dict__)
print("======================================")
print("")

adapter = BotFrameworkAdapter(
    settings
)


class DebugBot(ActivityHandler):

    async def on_message_activity(
        self,
        turn_context: TurnContext
    ):

        try:

            print("")
            print("========== MESSAGE ==========")

            print(
                "Channel:",
                turn_context.activity.channel_id
            )

            print(
                "User:",
                turn_context.activity.from_property.id
            )

            print(
                "Conversation:",
                turn_context.activity.conversation.id
            )

            print(
                "Service URL:",
                turn_context.activity.service_url
            )

            print(
                "Text:",
                turn_context.activity.text
            )

            print("=============================")
            print("")

            response_text = (
                "Hello from bot"
            )

            print("")
            print("========== SEND ==========")

            print(
                "About to send:",
                response_text
            )

            print(
                "Channel:",
                turn_context.activity.channel_id
            )

            print(
                "Service URL:",
                turn_context.activity.service_url
            )

            print(
                "Conversation:",
                turn_context.activity.conversation.id
            )

            print(
                "APP ID:",
                MICROSOFT_APP_ID
            )

            print(
                "PASSWORD PRESENT:",
                bool(MICROSOFT_APP_PASSWORD)
            )

            print("==========================")
            print("")

            try:

                result = await turn_context.send_activity(
                    response_text
                )

                print("")
                print("SEND SUCCESS")
                print(result)
                print("")

            except Exception as send_error:

                print("")
                print("SEND FAILED")
                print("")

                print(
                    "ERROR TYPE:"
                )
                print(
                    type(send_error)
                )

                print("")
                print(
                    "ERROR MESSAGE:"
                )
                print(
                    str(send_error)
                )

                print("")
                print(
                    "TRACEBACK:"
                )
                print(
                    traceback.format_exc()
                )

                print("")

                if hasattr(
                    send_error,
                    "response"
                ):

                    try:

                        print(
                            "HTTP STATUS:"
                        )

                        print(
                            send_error.response.status_code
                        )

                    except Exception:
                        pass

                raise

        except Exception as ex:

            print("")
            print("BOT ERROR")
            print(str(ex))
            print(traceback.format_exc())
            print("")

            raise


bot = DebugBot()


@app.get("/health")
async def health():

    return {
        "status": "healthy"
    }


@app.get("/debug")
async def debug():

    return {
        "app_id":
        MICROSOFT_APP_ID,

        "password_present":
        bool(
            MICROSOFT_APP_PASSWORD
        ),

        "app_type":
        MICROSOFT_APP_TYPE,

        "tenant_id":
        MICROSOFT_APP_TENANT_ID
    }


@app.post("/api/messages")
async def messages(
    request: Request
):

    try:

        body = await request.json()

        print("")
        print("========== RAW REQUEST ==========")
        print(body)
        print("=================================")
        print("")

        activity = Activity().deserialize(
            body
        )

        auth_header = request.headers.get(
            "Authorization",
            ""
        )

        print(
            "AUTH HEADER PRESENT:",
            bool(auth_header)
        )

        print(
            "AUTH HEADER LENGTH:",
            len(auth_header)
        )

        response = (
            await adapter.process_activity(
                activity,
                auth_header,
                bot.on_turn
            )
        )

        print("")
        print(
            "PROCESS_ACTIVITY COMPLETE"
        )

        print(
            "RESPONSE OBJECT:"
        )

        print(response)

        print("")

        if response:

            print(
                "HTTP RESPONSE STATUS:",
                response.status
            )

            return Response(
                content=response.body,
                status_code=response.status
            )

        return Response(
            status_code=201
        )

    except Exception as ex:

        print("")
        print("API ERROR")
        print(str(ex))
        print(traceback.format_exc())
        print("")

        return JSONResponse(
            status_code=500,
            content={
                "error": str(ex)
            }
        )