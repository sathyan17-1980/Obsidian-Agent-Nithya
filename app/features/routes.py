"""FastAPI routes for Obsidian AI agent interaction.

This module provides HTTP endpoints for:
- Agent chat interaction
- Agent run history
- Health checks specific to agent functionality
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.features.agent import get_vault_deps, vault_agent

# Import tools to register them with the agent

logger = get_logger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    """Chat request model for agent interaction.

    Attributes:
        message: User message to send to the agent.
        conversation_id: Optional conversation ID for maintaining context.
    """

    message: str = Field(..., description="User message to send to the agent", min_length=1)
    conversation_id: str | None = Field(None, description="Optional conversation ID for context")


class ChatResponse(BaseModel):
    """Chat response model from agent.

    Attributes:
        response: Agent's response message.
        conversation_id: Conversation ID for this interaction.
        model_used: Model that was used for the response.
    """

    response: str = Field(..., description="Agent's response message")
    conversation_id: str = Field(..., description="Conversation ID for this interaction")
    model_used: str = Field(..., description="Model that was used for the response")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a message to the Obsidian AI agent.

    Args:
        request: Chat request with user message.

    Returns:
        Agent response with conversation context.

    Raises:
        HTTPException: If agent interaction fails.
    """
    logger.info("agent.chat_started", message_length=len(request.message))

    try:
        # Get vault dependencies
        deps = get_vault_deps()

        # Run the agent
        result = await vault_agent.run(
            request.message,
            deps=deps,
        )

        logger.info(
            "agent.chat_completed",
            response_length=len(result.output),
            usage=str(result.usage),
        )

        return ChatResponse(
            response=result.output,
            conversation_id="default",  # In MVP, we use a single conversation
            model_used="anthropic:claude-sonnet-4-0",
        )

    except Exception as e:
        logger.error(
            "agent.chat_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Agent interaction failed: {e!s}") from e


@router.get("/health")
async def agent_health() -> dict[str, str]:
    """Check agent health and configuration.

    Returns:
        Agent health status.

    Raises:
        HTTPException: If agent is not properly configured.
    """
    logger.info("agent.health_check_started")

    try:
        # Check vault dependencies
        deps = get_vault_deps()

        logger.info("agent.health_check_completed", vault_path=str(deps.vault_path))

        # Count tools - we have 3 registered tools
        tool_count = 3

        return {
            "status": "healthy",
            "vault_path": str(deps.vault_path),
            "agent_model": "anthropic:claude-sonnet-4-0",
            "tools_registered": str(tool_count),
        }

    except Exception as e:
        logger.error(
            "agent.health_check_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise HTTPException(status_code=503, detail=f"Agent not properly configured: {e!s}") from e
