from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


class WorkflowClient:

    def __init__(self):

        self.endpoint = (
            "https://ace-foundry-1.services.ai.azure.com/api/projects/proj-default"
        )

        self.workflow_name = "test"

        credential = DefaultAzureCredential()

        self.project_client = AIProjectClient(
            endpoint=self.endpoint,
            credential=credential
        )

        self.openai_client = (
            self.project_client.get_openai_client()
        )

        print("=" * 80)
        print("WORKFLOW CLIENT INITIALIZED")
        print(f"WORKFLOW: {self.workflow_name}")
        print("=" * 80)

    def create_conversation(self):

        conversation = (
            self.openai_client.conversations.create()
        )

        print("=" * 80)
        print("NEW CONVERSATION CREATED")
        print(f"CONVERSATION ID: {conversation.id}")
        print("=" * 80)

        return conversation.id

    def send_message(
        self,
        conversation_id,
        user_message
    ):

        print("=" * 80)
        print("SEND MESSAGE")
        print(f"CONVERSATION: {conversation_id}")
        print(f"USER MESSAGE: {user_message}")
        print("=" * 80)

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

        print("=" * 80)
        print("DELETE CONVERSATION")
        print(f"CONVERSATION: {conversation_id}")
        print("=" * 80)

        self.openai_client.conversations.delete(
            conversation_id=conversation_id
        )