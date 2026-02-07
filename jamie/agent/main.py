"""Entry point for Jamie CUA agent."""

import sys

import uvicorn

from jamie.shared.config import get_agent_config
from jamie.shared.logging import setup_logging, get_logger


def main():
    """Run the CUA agent controller."""
    
    # Setup logging
    setup_logging(level="INFO", json_output=False, service_name="jamie-agent")
    log = get_logger(__name__)
    
    # Load config
    try:
        config = get_agent_config()
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("Make sure JAMIE_AGENT_* environment variables are set.", file=sys.stderr)
        sys.exit(1)
    
    log.info(
        "agent_starting",
        host=config.host,
        port=config.port,
        model=config.model,
    )
    
    # Run the FastAPI app
    uvicorn.run(
        "jamie.agent.controller:app",
        host=config.host,
        port=config.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
