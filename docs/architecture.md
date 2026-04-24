# Architecture Notes

## LangGraph / AsyncPostgresSaver

`thread_id` equals `Conversation.pk` (as a string). LangGraph manages its own tables (`checkpoints`, `checkpoint_blobs`,
etc.) via `AsyncPostgresSaver` — these are not Django-managed. Deleting a `Conversation` row does **not** cascade to
LangGraph checkpoint data; cleanup must be handled manually.

## Pending message handoff (tech debt)

Sending a message requires two HTTP requests: a POST to `/send/` that queues the message, followed immediately by a
GET SSE connection to `/stream/` that consumes it. The message text is bridged between these two requests via
`request.session`, keyed as `pending_message_<conv_id>`.

**Why this is tech debt:** the session is a poor semantic fit for sub-second transient data, and it requires an extra
DB write on every message send (the explicit `session.save()` call). The correct solution is a shared cache backend
(Redis) with a short TTL (≤30s). This was deferred because the project has no Redis dependency yet.
