from fastapi import FastAPI, Request
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
import os

app = FastAPI()

FOUNDRY_ENDPOINT = os.getenv("FOUNDRY_ENDPOINT")
WORKFLOW_NAME = os.getenv("WORKFLOW_NAME")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/messages")
async def messages(request: Request):

    data = await request.json()
    user_message = data.get("text", "")

    if not user_message:
        return {"error": "text is required"}

    project_client = AIProjectClient(
        endpoint=FOUNDRY_ENDPOINT,
        credential=DefaultAzureCredential()
    )

    with project_client:

        openai_client = project_client.get_openai_client()

        conversation = openai_client.conversations.create()

        response = openai_client.responses.create(
            conversation=conversation.id,
            extra_body={
                "agent_reference": {
                    "name": WORKFLOW_NAME,
                    "type": "agent_reference"
                }
            },
            input=user_message,
            stream=False
        )

    # extract final text safely
    try:
        final_text = response.output[0].content[0].text
    except:
        final_text = str(response)

    return {
        "response": final_text
    }