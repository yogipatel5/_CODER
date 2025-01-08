import pytest

from notion.agent.processor import Action, ProcessorConfig, PromptProcessor


@pytest.fixture
def processor() -> PromptProcessor:
    """Create a PromptProcessor instance"""
    return PromptProcessor()


@pytest.mark.asyncio
async def test_create_page_parsing(processor: PromptProcessor) -> None:
    """Test parsing create page prompts"""
    test_cases = [
        (
            'create a new page with title "My Page": This is the content',
            {"title": "my page", "content": "this is the content"},
        ),
        (
            'create page "My Page" with content: This is the content',
            {"title": "my page", "content": "this is the content"},
        ),
        (
            'create new page "My Page": This is the content',
            {"title": "my page", "content": "this is the content"},
        ),
    ]

    for prompt, expected in test_cases:
        action = await processor.parse(prompt)
        assert isinstance(action, Action)
        assert action.tool_name == "create_page"
        assert action.parameters == expected
        assert action.confidence >= 0.8


@pytest.mark.asyncio
async def test_read_page_parsing(processor: PromptProcessor) -> None:
    """Test parsing read page prompts"""
    prompts = [
        "read page abc123",
        "read the page with id abc123",
        "read page abc123 with content",
    ]

    for prompt in prompts:
        action = await processor.parse(prompt)
        assert isinstance(action, Action)
        assert action.tool_name == "read_page"
        assert "page_id" in action.parameters
        assert action.parameters["page_id"] == "abc123"
        assert action.confidence >= 0.8


@pytest.mark.asyncio
async def test_edit_page_parsing(processor: PromptProcessor) -> None:
    """Test parsing edit page prompts"""
    prompts = [
        "edit page abc123 set title to New Title",
        "edit the page with id abc123 title to New Title",
    ]

    for prompt in prompts:
        action = await processor.parse(prompt)
        assert isinstance(action, Action)
        assert action.tool_name == "edit_page"
        assert "page_id" in action.parameters
        assert "title" in action.parameters
        assert action.parameters["page_id"] == "abc123"
        assert action.parameters["title"] == "new title"
        assert action.confidence >= 0.7


@pytest.mark.asyncio
async def test_invalid_prompt(processor: PromptProcessor) -> None:
    """Test handling of invalid prompts"""
    invalid_prompts = [
        "",
        "invalid command",
        "do something",
        "create",
        "read",
        "edit",
    ]

    for prompt in invalid_prompts:
        with pytest.raises(ValueError):
            await processor.parse(prompt)


@pytest.mark.asyncio
async def test_processor_config() -> None:
    """Test processor configuration"""
    config = ProcessorConfig(
        model_name="openai:gpt-3.5-turbo", temperature=0.5, max_tokens=50
    )
    processor = PromptProcessor(config)

    assert processor.config.model_name == "openai:gpt-3.5-turbo"
    assert processor.config.temperature == 0.5
    assert processor.config.max_tokens == 50


@pytest.mark.asyncio
async def test_action_validation() -> None:
    """Test Action model validation"""
    # Valid action
    action = Action(
        tool_name="create_page",
        parameters={"title": "Test", "content": "Content"},
        confidence=0.9,
    )
    assert action.tool_name == "create_page"

    # Invalid confidence
    with pytest.raises(ValueError):
        Action(tool_name="create_page", parameters={}, confidence=1.5)

    # Invalid tool name
    with pytest.raises(ValueError):
        Action(tool_name="", parameters={}, confidence=0.9)
