"""Entry point for Jamie Discord bot.

Usage:
    python -m jamie.bot
    jamie-bot
"""

import asyncio
import signal
import sys
from typing import Optional

from jamie.bot.bot import JamieBot, create_bot
from jamie.shared.config import get_bot_config, get_observability_config, BotConfig
from jamie.shared.logging import get_logger, setup_logging

log = get_logger(__name__)


def main() -> None:
    """Main entry point for the bot."""
    # Configure structured logging from observability config
    try:
        obs_config = get_observability_config()
        setup_logging(level=obs_config.log_level, json_output=obs_config.log_json)
    except Exception:
        # Fall back to defaults if config fails
        setup_logging()
    
    log.info("jamie_bot_starting")
    
    # Load configuration from environment
    try:
        config = get_bot_config()
    except Exception as e:
        log.error("config_load_failed", error=str(e))
        print(f"Failed to load configuration: {e}", file=sys.stderr)
        print("Ensure JAMIE_BOT_DISCORD_TOKEN is set.", file=sys.stderr)
        sys.exit(1)
    
    # Create bot instance
    bot = create_bot(config)
    
    # Run with graceful shutdown handling
    try:
        asyncio.run(run_bot(bot, config))
    except KeyboardInterrupt:
        log.info("keyboard_interrupt")
    except Exception as e:
        log.error("bot_crashed", error=str(e))
        sys.exit(1)
    
    log.info("jamie_bot_stopped")


async def run_bot(bot: JamieBot, config: BotConfig) -> None:
    """Run the bot with signal handlers for graceful shutdown."""
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig: signal.Signals) -> None:
        log.info("shutdown_signal_received", signal=sig.name)
        shutdown_event.set()
    
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler, sig)
    
    # Start the bot
    token = config.discord_token.get_secret_value()
    
    async with bot:
        # Create tasks for bot and shutdown watcher
        bot_task = asyncio.create_task(bot.start(token))
        shutdown_task = asyncio.create_task(shutdown_event.wait())
        
        # Wait for either shutdown signal or bot exit
        done, pending = await asyncio.wait(
            [bot_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        
        # If shutdown was requested, close the bot gracefully
        if shutdown_task in done:
            log.info("initiating_graceful_shutdown")
            await bot.close()
            
            # Cancel the bot task if still pending
            if bot_task in pending:
                bot_task.cancel()
                try:
                    await bot_task
                except asyncio.CancelledError:
                    pass
        
        # If bot exited on its own, check for errors
        if bot_task in done:
            try:
                bot_task.result()
            except Exception as e:
                log.error("bot_task_error", error=str(e))
                raise


if __name__ == "__main__":
    main()
