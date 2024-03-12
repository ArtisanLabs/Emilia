import os
import logging
import logging.handlers

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    MessageReactionHandler,
    filters,
)

from langchain import hub
from vocode.turn_based.synthesizer import AzureSynthesizer
from vocode.turn_based.transcriber import WhisperTranscriber

from emiliabot.emiliabot import VocodeBotResponder
from emiliabot.database.supabase import SupabaseConfig

from dotenv import load_dotenv

# Fetch the logging level from environment variables, default to 'DEBUG' if not set
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'DEBUG')

# Define a dictionary to map string logging levels to their corresponding logging constants
LEVELS = {
    'DEBUG': logging.DEBUG, 
    'INFO': logging.INFO, 
    'WARNING': logging.WARNING, 
    'ERROR': logging.ERROR, 
    'CRITICAL': logging.CRITICAL
}
log = logging.getLogger(__name__)
log.setLevel(LEVELS.get(LOGGING_LEVEL, logging.DEBUG))

if not os.path.exists('logs'):
    os.makedirs('logs')

# File handler
file_handler = logging.handlers.TimedRotatingFileHandler('logs/telegram_bot.log', when='midnight', interval=1, backupCount=7)
file_handler.setLevel(LEVELS.get(LOGGING_LEVEL, logging.DEBUG))

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(LEVELS.get(LOGGING_LEVEL, logging.DEBUG))

# Add stacktrace to the log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d - %(exc_info)s', datefmt='%Y-%m-%d %H:%M:%S')

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

log.addHandler(file_handler)
log.addHandler(console_handler)

load_dotenv()

##############################################
## CONFIGURATION START
##############################################
# Required environment variables containing API key: 
# OPENAI_API_KEY, TELEGRAM_BOT_KEY,
# and your Vocode synthesizers classes corresponding API key variable

# Your chosen synthesizer provider's corresponding Vocode turn_based class instance
AZURE_SYNTHESIZER_MULTILINGUAL = AzureSynthesizer(voice_name="en-US-JennyMultilingualV2Neural")
OPENAI_WHISPER_TRANSCRIBER_MULTILINGUAL = WhisperTranscriber()
DABASE_CONFIG = SupabaseConfig(url=os.environ["SUPABASE_URL"], key=os.environ["SUPABASE_KEY"])

if os.environ.get("BETA", "0") == "1":
    TELEGRAM_BOT_KEY = os.environ["BETA_TELEGRAM_BOT_KEY"]
    LANGSMITH_SYSTEM_PROMPT = "artisanlabs/emilia"
else:
    TELEGRAM_BOT_KEY = os.environ["TELEGRAM_BOT_KEY"]
    LANGSMITH_SYSTEM_PROMPT = "artisanlabs/emilia"

##############################################
## CONFIGURATION END
##############################################


def main() -> None:
    """Run the bot."""
    voco = VocodeBotResponder(
        transcriber=OPENAI_WHISPER_TRANSCRIBER_MULTILINGUAL, 
        synthesizer=AZURE_SYNTHESIZER_MULTILINGUAL,
        database_config=DABASE_CONFIG,
        langsmith_system_prompt=LANGSMITH_SYSTEM_PROMPT,
        log=log
    )
    application = ApplicationBuilder().token(TELEGRAM_BOT_KEY).build()
    application.post_init = voco.initialize
    application.add_handler(CommandHandler("start", voco.handle_telegram_start))
    application.add_handler(
        MessageHandler(~filters.COMMAND, voco.handle_telegram_message)
    )
    application.add_handler(CommandHandler("status", voco.handle_telegram_status))
    application.add_handler(CommandHandler("help", voco.handle_telegram_help))
    application.add_handler(
        MessageHandler(filters.COMMAND, voco.handle_telegram_unknown_cmd)
    )
    # Add a handler to log MessageReactionHandler events. This handler will log
    # all updates that contain a message reaction. The handler uses the 
    # MessageReactionHandler class from the telegram library.
    application.add_handler(MessageReactionHandler(voco.handle_telegram_emoji_reaction))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()