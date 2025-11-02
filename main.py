import asyncio
import signal
import sys
import os
import time
from threading import Thread

from trading.trader import SelfLearningTrader
from web.dashboard import create_app, set_trader, set_initialization_error
from utils.logger import setup_logger, get_logger
from config import SYSTEM_CONFIG

setup_logger()
logger = get_logger(__name__)

trader = None
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    logger.info("shutdown_signal_received", signal=signum)
    shutdown_event.set()

async def initialize_trader():
    """Initialize trader asynchronously in background"""
    global trader
    
    try:
        logger.info("trader_initialization_starting")
        
        trader = SelfLearningTrader()
        await trader.start()
        
        set_trader(trader)
        
        logger.info("trader_initialization_completed")
        
        await shutdown_event.wait()
        
        logger.info("shutdown_initiated")
        await trader.stop()
        logger.info("system_stopped")
        
    except Exception as e:
        logger.error("trader_initialization_failed", error=str(e))
        set_initialization_error(e)
        raise

def run_server():
    """Run Flask server - starts immediately for health checks"""
    port = int(os.getenv('PORT', 5000))
    
    logger.info("system_starting", 
               environment=SYSTEM_CONFIG["ENVIRONMENT"],
               log_level=SYSTEM_CONFIG["LOG_LEVEL"],
               port=port)
    
    app, socketio = create_app()
    
    logger.info("web_server_starting", port=port)
    
    def start_trader_async():
        """Start trader initialization in background"""
        time.sleep(2)
        try:
            asyncio.run(initialize_trader())
        except Exception as e:
            logger.error("trader_async_init_failed", error=str(e))
    
    trader_thread = Thread(target=start_trader_async, daemon=True)
    trader_thread.start()
    
    logger.info("web_dashboard_started", url=f"http://0.0.0.0:{port}")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt")
        if trader:
            asyncio.run(trader.stop())
    except Exception as e:
        logger.error("fatal_error", error=str(e))
        sys.exit(1)
