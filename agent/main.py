"""
CUA Controller entry point.

This module initializes and runs the FastAPI server that receives
streaming requests from the Jamie Bot and manages CUA agent sessions.

Usage:
    uvicorn jamie.agent.main:app --host 0.0.0.0 --port 8000

Environment Variables:
    DISCORD_EMAIL: Discord account email for automation
    DISCORD_PASSWORD: Discord account password
    ANTHROPIC_API_KEY: API key for Claude model access
"""


def create_app():
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    # TODO: Implement FastAPI app creation
    # - Set up routes from controller
    # - Configure CORS if needed
    # - Initialize agent manager
    raise NotImplementedError("App creation not yet implemented")


# FastAPI app instance for uvicorn
app = None  # TODO: app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("jamie.agent.main:app", host="0.0.0.0", port=8000, reload=True)
