import asyncio
import chainlit as cl

from workflow_client import WorkflowClient

workflow = WorkflowClient()


ACTION_STATUS = {

    # Router
    "node-1781245541040":
        "🧠 Understanding request...",

    # Search
    "node-1781500525410":
        "🔍 Searching resources...",

    # Metadata
    "node-1781500809326":
        "📋 Fetching resource metadata...",

    # KQL
    "node-1781500766941":
        "📊 Executing KQL query...",

    # Generic Action
    "node-1781501456526":
        "⚡ Executing action...",

    # VM Snapshot
    "node-1781501643305":
        "📸 Creating snapshot...",

    # Email
    "node-1781501539073":
        "📧 Sending email...",

    # Formatter
    "node-1781501473149":
        "📝 Formatting response...",

    "node-1781501571540":
        "📝 Formatting response...",

    "node-1781501652513":
        "📝 Formatting response..."
}


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
        print("NEW CHAT SESSION")
        print("CONVERSATION:", conversation_id)
        print("=" * 80)

        await cl.Message(
            content="""
# Azure Foundry Workflow UI

✅ Connected successfully
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

    if not conversation_id:

        await cl.Message(
            content="Conversation not initialized."
        ).send()

        return

    try:

        print("=" * 80)
        print("NEW USER MESSAGE")
        print("SESSION CONVERSATION:", conversation_id)
        print("USER INPUT:", message.content)
        print("=" * 80)

        status_msg = cl.Message(
            content="🚀 Starting workflow..."
        )

        await status_msg.send()

        response_msg = cl.Message(
            content=""
        )

        await response_msg.send()

        stream = await asyncio.to_thread(
            workflow.send_message,
            conversation_id,
            message.content
        )

        streamed_text = ""
        final_message_text = ""

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
            # RESPONSE CREATED
            #
            if event_type == "response.created":

                print("=" * 80)
                print("RESPONSE CREATED")

                print(
                    "RESPONSE ID:",
                    getattr(
                        event.response,
                        "id",
                        ""
                    )
                )

                print(
                    "FOUNDRY CONVERSATION:",
                    getattr(
                        event.response,
                        "conversation",
                        ""
                    )
                )

                print("=" * 80)

            #
            # WORKFLOW ACTIONS
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

                    action_id = getattr(
                        item,
                        "action_id",
                        ""
                    )

                    print(
                        "ACTION ID:",
                        action_id
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

                    if (
                        action_id
                        in ACTION_STATUS
                    ):

                        status_msg.content = (
                            ACTION_STATUS[action_id]
                        )

                        await status_msg.update()

            #
            # STREAM TOKENS
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

                    print()
                    print(
                        "DELTA RECEIVED"
                    )

                    print(
                        delta
                    )

                    print(
                        "-" * 40
                    )

                    streamed_text += delta

                    await response_msg.stream_token(
                        delta
                    )

            #
            # FINAL MESSAGE
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

                if (
                    item_type ==
                    "message"
                ):

                    print("=" * 80)
                    print(
                        "MESSAGE ITEM FOUND"
                    )
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
                            None
                        )

                        if text:

                            final_message_text += text

            #
            # COMPLETED
            #
            elif (
                event_type ==
                "response.completed"
            ):

                print("=" * 80)

                print(
                    "RESPONSE COMPLETED"
                )

                print("=" * 80)

        #
        # FINISH STATUS
        #
        status_msg.content = (
            "✅ Completed"
        )

        await status_msg.update()

        #
        # FALLBACK LOGIC
        #
        if (
            not streamed_text.strip()
            and final_message_text.strip()
        ):

            response_msg.content = (
                final_message_text
            )

            await response_msg.update()

        elif (
            not streamed_text.strip()
            and not final_message_text.strip()
        ):

            response_msg.content = (
                "⚠️ No response returned."
            )

            await response_msg.update()

        print("=" * 80)

        print(
            "FINAL RESPONSE"
        )

        print(
            streamed_text
            or final_message_text
        )

        print("=" * 80)

    except Exception as e:

        print("=" * 80)
        print("ERROR")
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