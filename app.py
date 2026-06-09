from flask import Flask, request, jsonify

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

import os
import json

app = Flask(__name__)

FOUNDRY_ENDPOINT = os.environ["FOUNDRY_ENDPOINT"]
WORKFLOW_NAME = os.environ["WORKFLOW_NAME"]


@app.route("/health", methods=["GET"])
def health():
    return "V-2", 200


@app.route("/api/messages", methods=["POST"])
def messages():

    try:

        data = request.get_json(silent=True) or {}

        print("========== BOT REQUEST ==========")
        print(json.dumps(data, indent=2))
        print("=================================")

        user_message = data.get("text", "").strip()

        if not user_message:
            return jsonify({
                "error": "text field is required"
            }), 400

        project_client = AIProjectClient(
            endpoint=FOUNDRY_ENDPOINT,
            credential=DefaultAzureCredential()
        )

        final_response = ""

        with project_client:

            openai_client = project_client.get_openai_client()

            conversation = openai_client.conversations.create()

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

                return jsonify({
                    "response": final_response
                })

            finally:

                try:
                    openai_client.conversations.delete(
                        conversation_id=conversation.id
                    )
                except Exception as cleanup_error:
                    print(f"Conversation cleanup failed: {cleanup_error}")

    except Exception as ex:

        print(f"ERROR: {str(ex)}")

        return jsonify({
            "error": str(ex)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000
    )