import asyncio
import chainlit as cl

from workflow_client import WorkflowClient

workflow = WorkflowClient()


@cl.on_chat_start
async def start():

    try:

        conversation_id = await asyncio.to_thread(
            workflow.create_conversation
        )

        cl.user_session.set(
            "conversation_id",
            conversation_id
        )

        print("=" * 80)
        print("CHAT START")
        print(f"SESSION CONVERSATION: {conversation_id}")
        print("=" * 80)

        await cl.Message(
            content=f"""
# Azure Foundry Workflow UI

✅ Connected successfully

Conversation ID:

{conversation_id}
"""
        ).send()

    except Exception as e:

        await cl.Message(
            content=f"""
❌ Failed to connect

{str(e)}
"""
        ).send()


@cl.on_message
async def main(message: cl.Message):

    conversation_id = cl.user_session.get(
        "conversation_id"
    )

    print("=" * 80)
    print("NEW USER MESSAGE")
    print(f"SESSION CONVERSATION: {conversation_id}")
    print(f"USER INPUT: {message.content}")
    print("=" * 80)

    if not conversation_id:

        await cl.Message(
            content="""
❌ Conversation not initialized.

Please refresh the page.
"""
        ).send()

        return

    try:

        status_msg = cl.Message(
            content="🚀 Starting workflow..."
        )

        await status_msg.send()

        stream = await asyncio.to_thread(
            workflow.send_message,
            conversation_id,
            message.content
        )

        final_response = ""

        for event in stream:

            event_type = getattr(
                event,
                "type",
                ""
            )

            print(
                f"EVENT TYPE: {event_type}"
            )

            #
            # Response created
            #
            if event_type == "response.created":

                response = getattr(
                    event,
                    "response",
                    None
                )

                if response:

                    print("=" * 80)
                    print("RESPONSE CREATED")
                    print(
                        f"RESPONSE ID: {response.id}"
                    )

                    try:
                        print(
                            f"FOUNDRY CONVERSATION: "
                            f"{response.conversation.id}"
                        )
                    except Exception:
                        pass

                    print("=" * 80)

            #
            # Workflow actions
            #
            elif (
                event_type ==
                "response.output_item.added"
            ):

                item = getattr(
                    event,
                    "item",
                    None
                )

                if not item:
                    continue

                item_type = getattr(
                    item,
                    "type",
                    ""
                )

                if (
                    item_type ==
                    "workflow_action"
                ):

                    print("\n" + "=" * 80)
                    print("WORKFLOW ACTION")
                    print("=" * 80)

                    print(
                        "ACTION ID:",
                        getattr(
                            item,
                            "action_id",
                            ""
                        )
                    )

                    print(
                        "KIND:",
                        getattr(
                            item,
                            "kind",
                            ""
                        )
                    )

                    print(
                        "STATUS:",
                        getattr(
                            item,
                            "status",
                            ""
                        )
                    )

                    print(
                        "PARENT:",
                        getattr(
                            item,
                            "parent_action_id",
                            ""
                        )
                    )

                    print(
                        "PREVIOUS:",
                        getattr(
                            item,
                            "previous_action_id",
                            ""
                        )
                    )

                    print(
                        "AGENT:",
                        getattr(
                            item,
                            "agent_reference",
                            {}
                        )
                    )

                    kind = getattr(
                        item,
                        "kind",
                        ""
                    )

                    if (
                        kind ==
                        "InvokeAzureAgent"
                    ):

                        status_msg.content = (
                            "🤖 Running workflow..."
                        )

                        await status_msg.update()

                    elif (
                        kind ==
                        "SendActivity"
                    ):

                        status_msg.content = (
                            "💬 Preparing response..."
                        )

                        await status_msg.update()

            #
            # Stream text
            #
            elif (
                event_type ==
                "response.output_text.delta"
            ):

                delta = getattr(
                    event,
                    "delta",
                    ""
                )

                if delta:

                    print("\nDELTA RECEIVED")
                    print(delta)
                    print("-" * 40)

                    final_response += delta

            #
            # Message object
            #
            elif (
                event_type ==
                "response.output_item.done"
            ):

                item = getattr(
                    event,
                    "item",
                    None
                )

                if not item:
                    continue

                item_type = getattr(
                    item,
                    "type",
                    ""
                )

                if item_type == "message":

                    print("=" * 80)
                    print("MESSAGE ITEM FOUND")
                    print("=" * 80)

                    content = getattr(
                        item,
                        "content",
                        []
                    )

                    for part in content:

                        text = getattr(
                            part,
                            "text",
                            ""
                        )

                        if (
                            text and
                            text not in final_response
                        ):
                            final_response += text

        print("=" * 80)
        print("FINAL RESPONSE")
        print(final_response)
        print("=" * 80)

        status_msg.content = (
            "✅ Completed"
        )

        await status_msg.update()

        if final_response.strip():

            await cl.Message(
                content=final_response
            ).send()

        else:

            await cl.Message(
                content="""
⚠️ No response returned.

Check App Service logs for workflow events.
"""
            ).send()

    except Exception as e:

        print("=" * 80)
        print("WORKFLOW ERROR")
        print(str(e))
        print("=" * 80)

        await cl.Message(
            content=f"""
❌ Workflow Error

{str(e)}
"""
        ).send()


@cl.on_chat_end
async def end():

    conversation_id = cl.user_session.get(
        "conversation_id"
    )

    if not conversation_id:
        return

    try:

        await asyncio.to_thread(
            workflow.delete_conversation,
            conversation_id
        )

        print(
            f"Conversation deleted: {conversation_id}"
        )

    except Exception as e:

        print(
            f"Cleanup failed: {e}"
        )