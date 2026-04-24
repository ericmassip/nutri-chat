import logging
from html import escape

from asgiref.sync import sync_to_async
from django.http import HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import aget_object_or_404, render
from django.utils import timezone
from django.views import View
from langchain_core.messages import HumanMessage
from markdownx.utils import markdownify

from nutrichat.graph import graph_manager
from nutrichat.models import Conversation

log = logging.getLogger(__name__)

_PENDING_MSG_SESSION_KEY = "pending_message"


async def get_conversation(user, conv_id=None):
    """Resolve the conversation for the current user. Users can only see their own chats. Returns None for new chats."""
    conversation = None
    if conv_id:
        conversation = await aget_object_or_404(Conversation, pk=conv_id, user=user)
    return conversation


class ChatView(View):
    """View for rendering the chat interface. Users that open the chat page make a request to this view. If the
    conversation is not new, it fetches the conversation's messages from the db."""
    async def get(self, request, conv_id=None):
        messages_list = []
        conversation = await get_conversation(request.user, conv_id)
        if conversation:
            async with graph_manager.graph() as graph:
                config = {"configurable": {"thread_id": str(conversation.pk)}}
                state = await graph.aget_state(config)
                if not state.values or "messages" not in state.values:
                    log.warning(
                        f"No LangGraph checkpoint found for conversation_id={conversation.id} (user_id={request.user.id}, "
                        f"thread_id={conversation.id}). The conversation exists in the DB but has no checkpoint — the "
                        f"stream may have failed before any message was saved, or the checkpoint tables were wiped."
                    )
                else:
                    for msg in state.values["messages"]:
                        content = msg.content
                        if isinstance(content, list):
                            content = "".join(
                                part if isinstance(part, str) else part.get("text", "")
                                for part in content
                            )
                        content_html = markdownify(content) if msg.type == "ai" else content
                        messages_list.append({"type": msg.type, "content": content, "content_html": content_html})

        return render(request, 'chat.html', {
            'conversation': conversation,
            'conversations': [c async for c in request.user.conversations.all()],
            'messages_list': messages_list,
        })


class ChatSendView(View):
    """View for handling user messages. The message is sent to the LangGraph model and the response is rendered."""
    async def post(self, request, conv_id=None):
        message_text = request.POST.get('message', '').strip()
        if not message_text:
            return HttpResponseBadRequest(f"{request.user.username} sent a message but the message was empty. "
                                          f"conv_id={conv_id}, message={message_text}")

        conversation = await get_conversation(request.user, conv_id)
        is_conversation_new = False
        if not conversation:
            conversation = await Conversation.objects.acreate(user=request.user, title=message_text[:50])
            is_conversation_new = True

        # The message has to live in the session until the streaming starts. We store it in the session under a key that
        # includes the conversation ID and the stream pops it.
        request.session[f"{_PENDING_MSG_SESSION_KEY}_{conversation.pk}"] = message_text
        await request.session.asave()

        return render(request, 'chat.html#send-response', {
            'message_text': message_text,
            'is_conversation_new': is_conversation_new,
            'conversation': conversation,
            'conversations': [c async for c in request.user.conversations.all()],
        })


class ChatStreamView(View):
    async def get(self, request, conv_id):
        conversation = await get_conversation(request.user, conv_id)

        pending = request.session.pop(f"{_PENDING_MSG_SESSION_KEY}_{conv_id}", None)
        if not pending:
            return HttpResponseBadRequest(f"{request.user.username} sent a message in conv_id={conv_id} but it got lost.")
        await request.session.asave()

        attachment = await request.user.attachments.afirst()
        pdf_base64 = await sync_to_async(attachment.read_as_base64)() if attachment else None

        async def event_stream():
            async with graph_manager.graph() as graph:
                try:
                    config = {
                        "configurable": {
                            "thread_id": str(conv_id),
                            "pdf_base64": pdf_base64,
                            "customer_description": request.user.description,
                        }
                    }
                    human_msg = HumanMessage(content=pending)
                    full_response = []

                    async for event in graph.astream(
                        {"messages": [human_msg]},
                        config=config,
                        stream_mode="messages",
                    ):
                        msg, metadata = event
                        if msg.content and metadata.get("langgraph_node") == "call_model":
                            content = msg.content
                            if isinstance(content, list):
                                content = "".join(
                                    part if isinstance(part, str) else part.get("text", "")
                                    for part in content
                                )
                            if content:
                                full_response.append(content)
                                token = escape(content)
                                yield f"event: token\ndata: {token}\n\n"

                    rendered = markdownify("".join(full_response))
                    # SSE data must be single-line; multi-line needs each line prefixed with "data: "
                    sse_data = rendered.replace("\n", "\ndata: ")
                    yield f"event: done\ndata: {sse_data}\n\n"
                except Exception as e:
                    log.exception(f"Streaming error in conv_id={conv_id}. Error: {e}")
                    yield "event: error\ndata: An error occurred during streaming\n\n"
                finally:
                    conversation.last_updated = timezone.now()
                    await conversation.asave(update_fields=['last_updated'])

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
