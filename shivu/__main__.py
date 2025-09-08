import importlib
import logging
from shivu import application, ALL_MODULES, shivuu

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load all modules dynamically
for module_name in ALL_MODULES:
    importlib.import_module(f"shivu.modules.{module_name}")

# Start Pyrogram and Telegram bot
if __name__ == "__main__":
    shivuu.start()
    logger.info("Bot started")
    application.run_polling(drop_pending_updates=True)
