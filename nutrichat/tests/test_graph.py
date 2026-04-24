from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from nutrichat.graph import SYSTEM_PROMPT, GraphManager


async def test_call_model_full_conversation():
    """A multi-turn conversation with both customer_description and pdf_base64."""
    manager = GraphManager()
    mock_response = AIMessage(content="For lunch you could have grilled chicken.")
    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(return_value=mock_response)

    state = {
        "messages": [
            HumanMessage(content="What can I eat for breakfast?"),
            AIMessage(content="You can have oats and fruit."),
            HumanMessage(content="What about lunch?"),
        ]
    }
    config = {
        "configurable": {
            "customer_description": "Athlete, 80 kg, lactose intolerant.",
            "pdf_base64": "dGVzdA==",
        }
    }

    with patch.object(manager, "_get_model", return_value=mock_model):
        result = await manager.call_model(state, config)

    messages = mock_model.ainvoke.call_args[0][0]
    assert messages == [
        SystemMessage(content=SYSTEM_PROMPT + "\n\nBackground notes on this customer:\nAthlete, 80 kg, lactose intolerant."),
        HumanMessage(content=[
            {"type": "text", "text": "Here is the nutritional plan document:"},
            {"type": "file", "base64": "dGVzdA==", "mime_type": "application/pdf"},
        ]),
        HumanMessage(content="What can I eat for breakfast?"),
        AIMessage(content="You can have oats and fruit."),
        HumanMessage(content="What about lunch?"),
    ]
    assert result == {"messages": [mock_response]}


async def test_call_model_with_pdf_base64_only():
    manager = GraphManager()
    mock_response = AIMessage(content="Here is your plan.")
    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(return_value=mock_response)

    state = {"messages": [HumanMessage(content="What should I eat?")]}
    config = {"configurable": {"pdf_base64": "dGVzdA=="}}

    with patch.object(manager, "_get_model", return_value=mock_model):
        result = await manager.call_model(state, config)

    messages = mock_model.ainvoke.call_args[0][0]
    assert messages == [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=[
            {"type": "text", "text": "Here is the nutritional plan document:"},
            {"type": "file", "base64": "dGVzdA==", "mime_type": "application/pdf"},
        ]),
        HumanMessage(content="What should I eat?"),
    ]
    assert result == {"messages": [mock_response]}


async def test_call_model_with_customer_description_only():
    manager = GraphManager()
    mock_response = AIMessage(content="Here is your plan.")
    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(return_value=mock_response)

    state = {"messages": [HumanMessage(content="What are my macros?")]}
    config = {"configurable": {"customer_description": "Diabetic, 60 kg."}}

    with patch.object(manager, "_get_model", return_value=mock_model):
        result = await manager.call_model(state, config)

    messages = mock_model.ainvoke.call_args[0][0]
    assert messages == [
        SystemMessage(content=SYSTEM_PROMPT + "\n\nBackground notes on this customer:\nDiabetic, 60 kg."),
        HumanMessage(content="What are my macros?"),
    ]
    assert result == {"messages": [mock_response]}
