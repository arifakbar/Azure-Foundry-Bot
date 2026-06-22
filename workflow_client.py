from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


class WorkflowClient:

    def __init__(self):

        self.endpoint = (
            "https://ace-foundry-1.services.ai.azure.com/api/projects/proj-default"
        )

        self.workflow_name = "test"

        self.project_client = AIProjectClient(
            endpoint=self.endpoint,
            credential=DefaultAzureCredential()
        )

        self.openai_client = (
            self.project_client.get_openai_client()
        )

    def create_conversation(self):

        conversation = (
            self.openai_client.conversations.create()
        )

        return conversation.id

    def send_message(
        self,
        conversation_id,
        user_message
    ):

        return self.openai_client.responses.create(
            conversation=conversation_id,
            input=user_message,
            stream=True,
            extra_body={
                "agent_reference": {
                    "name": self.workflow_name,
                    "type": "agent_reference"
                }
            },
            metadata={
                "x-ms-debug-mode-enabled": "1"
            }
        )

    def delete_conversation(
        self,
        conversation_id
    ):

        self.openai_client.conversations.delete(
            conversation_id=conversation_id
        )