import asyncio
import signal
import sys
import os
from threading import Thread

from trading.trader import SelfLearningTrader
from web.dashboard import create_app
from utils.logger import setup_logger, get_logger
from config import SYSTEM_CONFIG

setup_logger()
logger = get_logger(__name__)

trader = None
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    logger.info("shutdown_signal_received", signal=signum)
    shutdown_event.set()

async def main():
    global trader
    
    logger.info("system_starting", 
               environment=SYSTEM_CONFIG["ENVIRONMENT"],
               log_level=SYSTEM_CONFIG["LOG_LEVEL"])
    
    try:
        trader = SelfLearningTrader()
        
        await trader.start()
        
        app, socketio = create_app(trader)
        
        port = int(os.getenv('PORT', 5000))
        
        def run_flask():
            socketio.run(app, host='0.0.0.0', port=port, debug=False, use_reloader=False)
        
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        logger.info("web_dashboard_started", url=f"http://0.0.0.0:{port}")
        
        await shutdown_event.wait()
        
        logger.info("shutdown_initiated")
        await trader.stop()
        
        logger.info("system_stopped")
        
    except Exception as e:
        logger.error("system_error", error=str(e))
        raise
    finally:
        if trader:
            await trader.stop()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt")
    except Exception as e:
        logger.error("fatal_error", error=str(e))
        sys.exit(1)
