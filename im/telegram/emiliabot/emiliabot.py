import io
import re
import logging
import pickle

from datetime import datetime
from pydub import AudioSegment
from typing import Tuple, Union, Dict
from collections import defaultdict

from vocode.turn_based.transcriber import BaseTranscriber
from vocode.turn_based.agent import ChatGPTAgent
from vocode.turn_based.synthesizer import (
    BaseSynthesizer,
)

from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from langchain.text_splitter import MarkdownHeaderTextSplitter
from telegram import Update
from telegram.ext import (
    ContextTypes,
)

from miabot.models.models import Chat, TelegramUser, TelegramMessage
from miabot.database.supabase import SupabaseConfig, SupabaseDB

from telegram.ext._application import Application


class VocodeBotResponder:
    def __init__(
        self,
        transcriber: BaseTranscriber,
        synthesizer: BaseSynthesizer,
        database_config: SupabaseConfig,
        langsmith_system_prompt: str,
        log: logging.Logger,
    ) -> None:
        self.transcriber = transcriber
        self.langsmith_system_prompt = langsmith_system_prompt
        self.system_prompt: ChatPromptTemplate = hub.pull(self.langsmith_system_prompt)
        self.str_system_prompt = self.system_prompt.messages[0].prompt.template
        self.synthesizer = synthesizer
        self.db: Dict[int, Chat] = defaultdict(Chat)
        self.log = log
        self.database = SupabaseDB(database_config, self.log)
        self.all_messages: Dict[int, TelegramMessage] = defaultdict(TelegramMessage)

    async def initialize(self, app: Application):
        """
        This function initizialize all the async components of the bot.
        """
        await self.database.initialize_database()

    async def _format_goals_and_habits(self, goals_and_habits: Dict[str, str]):
        """
        This function formats the goals and habits into markdown format with each goal and habit as a header.
        """
        formatted_goals_and_habits = ""
        for key, value in goals_and_habits.items():
            formatted_goals_and_habits += f"# {key}\n\n{value}\n\n"
        return formatted_goals_and_habits

    async def _remove_markdown_comments(self, message: str) -> str:
        """
        This function removes markdown comments from the message.
        """
        # Remove markdown comments
        message = re.sub(r"<!--.*?-->", "", message, flags=re.DOTALL)
        return message

    async def _send_message(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int, message: str
    ) -> None:
        """
        This function sends a message to the user. It splits the message into parts
        """
        message = await self._remove_markdown_comments(message)

        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            # Add more headers as needed
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on, strip_headers=False
        )
        message_parts = markdown_splitter.split_text(message)

        for part in message_parts:
            part_content = part.page_content
            if len(part_content) <= 4096:
                # self.log.debug(f"Sending message: {part_content}")
                message = await context.bot.send_message(
                    chat_id=chat_id, text=part_content
                )
                # Create a new instance of the TelegramMessage model
                self.log.debug(f"Message: {message}")
                telegram_message = TelegramMessage(
                    message_id=message.message_id,
                    chat_id=message.chat.id,
                    text=message.text,
                    date=message.date,
                    user_id=message.chat.id,
                )
                self.all_messages[message.message_id] = telegram_message

            else:
                sub_parts = [
                    part_content[i : i + 4096]
                    for i in range(0, len(part_content), 4096)
                ]
                for sub_part in sub_parts:
                    message = await context.bot.send_message(
                        chat_id=chat_id, text=sub_part
                    )
                    # Create a new instance of the TelegramMessage model
                    telegram_message = TelegramMessage(
                        message_id=message.message_id,
                        chat_id=message.chat.id,
                        text=message.text,
                        date=message.date,
                        user_id=message.chat.id,
                    )
                    self.all_messages[message.message_id] = telegram_message

    def get_agent(self, chat_id: int) -> ChatGPTAgent:
        """
        This function returns a ChatGPTAgent instance for the given chat_id.
        """
        convo_string = self.db[chat_id].current_conversation
        agent = ChatGPTAgent(
            system_prompt=self.str_system_prompt,
            model_name="gpt-4-turbo-preview",
            max_tokens=2048,
            memory=pickle.loads(convo_string) if convo_string else None,
        )

        return agent

    # input can be audio segment or text
    async def get_response(
        self, chat_id: int, input: Union[str, AudioSegment]
    ) -> Tuple[str, AudioSegment]:
        # If input is audio, transcribe it
        if isinstance(input, AudioSegment):
            input = self.transcriber.transcribe(input)

        self.log.debug(f"User {chat_id}: {input}")
        # self.log.debug(f"current prompt: {self.str_system_prompt}")

        agent = self.get_agent(chat_id)
        agent_response = agent.respond(input)
        self.log.debug(f"Agent {chat_id}: {input}")

        user = self.db[chat_id]

        # Synthesize response
        # TODO make async
        synth_response = self.synthesizer.synthesize(agent_response)

        # Save conversation to DB
        self.db[chat_id].current_conversation = pickle.dumps(agent.memory)

        # log current conversation
        self.log.debug(f"current conversation: {agent.memory}")

        return agent_response, synth_response

    async def handle_telegram_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        # Ensure the chat is defined
        assert update.effective_chat, "Chat must be defined!"
        chat_id = update.effective_chat.id

        if chat_id not in self.db:
            await self.intialize_chat(update)

        self.log.info(f"Starting conversation with chat_id: {chat_id}")
        self.log.debug(f"Start Update: {update}")

        self.system_prompt = hub.pull(self.langsmith_system_prompt)

        # Define the start text
        start_text = (
            "Hi! Let’s set and achieve your goals.\n\n"
            "You can text or send voice notes to Mia. Mia will help you define your long-term goals and then drill down to quarterly, monthly, weekly, and finally daily goals. Mia will make sure to work on daily habits as well.\n\n"
            "To begin, click on this link: /long_term_goals\n\n"
            "If you’re ever stuck, simply write /help"
        )

        # erase the conversation history
        self.db[chat_id].current_conversation = None
        await self.change_stage("onboarding-start", chat_id)

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=start_text
        )

    async def handle_telegram_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat, "Chat must be defined!"
        chat_id = update.effective_chat.id

        # log the start of conversation with chat_id
        # check if the chat_id is in the db
        if chat_id not in self.db:
            self.log.info(f"Starting conversation with chat_id: {chat_id}")
            await self.intialize_chat(update)

        # Accept text or voice messages
        if update.message and update.message.voice:
            user_telegram_voice = await context.bot.get_file(
                update.message.voice.file_id
            )
            bytes = await user_telegram_voice.download_as_bytearray()
            # convert audio bytes to numpy array
            input = AudioSegment.from_file(
                io.BytesIO(bytes), format="ogg", codec="libopus"  # type: ignore
            )
        elif update.message and update.message.text:
            input = update.message.text
        else:
            # No audio or text, complain to user.
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "Sorry, I only respond to commands, voice, or text messages. Use /help for more information."
                ),
            )
            return

        # Get audio response from LLM/synth and reply
        agent_response, synth_response = await self.get_response(int(chat_id), input)
        out_voice = io.BytesIO()
        synth_response.export(out_f=out_voice, format="ogg", codec="libopus")  # type: ignore
        await self._send_message(context, update.effective_chat.id, agent_response)
        await context.bot.send_voice(chat_id=str(chat_id), voice=out_voice)

    async def handle_telegram_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        This function handles the '/status' command from the user. It sends a message back to the user
        with the current system prompt that is being used to generate responses, the current chat_id,
        the current planning stage, and the onboarding status.
        """
        assert update.effective_chat, "Chat must be defined!"
        chat_id = update.effective_chat.id
        # onboarding_status = self.db[chat_id].onboarding_status

        onboarding_status = await self.database.get_onboarding_status(chat_id)
        current_stage = await self.database.get_current_onboarding_stage(chat_id)

        # Format the onboarding status using emojis to represent the stages
        # A checkmark emoji (✅) is used to represent completed stages
        # A reload emoji (🔄) is used to represent the current stage or next stage
        # A soon arrow emoji (🔜) is used to represent future stages
        format_onboarding_status = ""
        for stage, completed in onboarding_status.items():
            if completed:
                format_onboarding_status += f"{stage}: ✅\n"
            elif stage == current_stage:
                format_onboarding_status += f"{stage}: 🔄\n"
            else:
                format_onboarding_status += f"{stage}: 🔜\n"

        # postgres_version = await self.database.get_postgres_version()

        status_message = (
            # f"Current system prompt:\n{self.str_system_prompt}\n"
            f"Current chat_id:\n{chat_id}\n"
            f"Current planning stage:\n{current_stage}\n"
            f"Onboarding status:\n{format_onboarding_status}"
            # f"Postgres version:\n{postgres_version}"
        )
        self.log.info(status_message)
        await self._send_message(context, chat_id, status_message)
    
    async def handle_telegram_detail_status(
            self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        This function handles the '/detail_status' command from the user. It sends a message back to the user
        """
        assert update.effective_chat, "Chat must be defined!"
        chat_id = update.effective_chat.id
        
        status_message = (
            f"Current system prompt:\n\n {self.str_system_prompt}\n\n"
        )
        self.log.info(status_message)
        await self._send_message(context, chat_id, status_message)

    async def intialize_chat(self, update: Update) -> None:
        """
        This function initializes a new chat in the database with the provided chat_id. It sets the
        onboarding status to the default values and sets the current planning stage to 'start'.
        """
        assert update.effective_chat, "Chat must be defined!"
        chat_id = update.effective_chat.id

        user = await self.database.get_telegram_user(chat_id)

        # If the user doesn't exist in the database, it's a new user
        if user is None:
            telegram_user: TelegramUser = TelegramUser(
                chat_id=update.effective_user.id,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name,
                username=update.effective_user.username,
                is_bot=update.effective_user.is_bot,
                language_code=update.effective_user.language_code,
            )
            await self.database.upsert_telegram_user(telegram_user)
            # Create planning stages for the new user
            await self.database.create_planning_stages_for_user(chat_id)
            # start the onboarding stage
            await self.database.start_onboarding_stage(chat_id, "onboarding-start")

    async def change_stage(self, new_prompt_name: str, chat_id: int) -> None:
        """
        This function updates the system prompt with the new prompt provided. The new prompt is fetched
        from the langchain hub using the provided name. This is an internal function and not a handler
        for a telegram command.
        """
        current_stage = await self.database.get_current_onboarding_stage(chat_id)
        if current_stage is not None:
            await self.database.complete_onboarding_stage(chat_id, current_stage)
        await self.database.start_onboarding_stage(chat_id, new_prompt_name)
        self.log.debug(f"Changing stage from {current_stage} to {new_prompt_name}")

        stored_messages_by_stage = (
            await self.database.get_stored_messages_by_planning_stage(chat_id)
        )
        self.log.debug(f"Stored messages by stage: {stored_messages_by_stage}")

        if new_prompt_name == "onboarding-start":
            stage_prompt_name = self.langsmith_system_prompt
            obj = hub.pull(stage_prompt_name)
            current_date = datetime.now().strftime("%Y-%m-%d")
            stage_prompt = self.system_prompt.format_messages(
                current_date=current_date,
                planning_stage_name="onboarding-start",
                planning_stage_prompt="",
                long_term_goals=stored_messages_by_stage["long-term-goals"],
                trimester_goals=stored_messages_by_stage["trimester-goals"],
                monthly_goals=stored_messages_by_stage["monthly-goals"],
                daily_habits=stored_messages_by_stage["daily-habits"],
                next_week_plan=stored_messages_by_stage["next-week-plan"],
                question="",
            )
            self.str_system_prompt = stage_prompt[0].content
            return

        stage_prompt_name = f"artisanlabs/{new_prompt_name}"
        # Fetch the new prompt from the langchain hub
        # TODO: make async
        obj = hub.pull(stage_prompt_name)

        current_date = datetime.now().strftime("%Y-%m-%d")

        stage_prompt = self.system_prompt.format_messages(
            current_date=current_date,
            planning_stage_name=new_prompt_name,
            planning_stage_prompt=obj.messages[0].prompt.template,
            long_term_goals=stored_messages_by_stage["long-term-goals"],
            trimester_goals=stored_messages_by_stage["trimester-goals"],
            monthly_goals=stored_messages_by_stage["monthly-goals"],
            daily_habits=stored_messages_by_stage["daily-habits"],
            next_week_plan=stored_messages_by_stage["next-week-plan"],
            question="",
        )
        # Update the system prompt
        self.str_system_prompt = stage_prompt[0].content

    async def handle_telegram_long_term_goals(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        This function handles the '/long_term_goals' command from the user. It updates the system prompt
        by calling the 'update_prompt' function with the 'long-term-goals' prompt from the langchain hub.
        """
        assert update.effective_chat, "Chat must be defined!"
        chat_id = update.effective_chat.id

        # Call the 'update_prompt' function with the 'long-term-goals' prompt
        await self.change_stage("long-term-goals", chat_id=chat_id)
        await context.bot.send_message(
            chat_id=chat_id, text=f"Planning stage 'long-term-goals'."
        )

        react_text = "When a goal or habit works for you, save it by reacting with the ❤️ emoji. Mia will keep it in mind for later steps.\n\n"

        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=open("assets/videos/react.mp4", "rb"),
            caption=react_text,
        )

        # Get audio response from LLM/synth and reply
        agent_response, synth_response = await self.get_response(
            int(chat_id), "Lets plan long term goals"
        )
        out_voice = io.BytesIO()
        synth_response.export(out_f=out_voice, format="ogg", codec="libopus")  # type: ignore
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=agent_response
        )
        await context.bot.send_voice(chat_id=str(chat_id), voice=out_voice)

    async def handle_telegram_trimester_goals(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        This function handles the '/trimester_goals' command from the user. It updates the system prompt
        by calling the 'update_prompt' function with the 'define-trimester-goals' prompt from the langchain hub.
        """
        assert update.effective_chat, "Chat must be defined!"
        chat_id = update.effective_chat.id
        # Call the 'update_prompt' function with the 'define-trimester-goals' prompt
        await self.change_stage("trimester-goals", chat_id=chat_id)
        await context.bot.send_message(
            chat_id=chat_id, text=f"System prompt updated to 'trimester-goals'."
        )
        # Get audio response from LLM/synth and reply
        agent_response, synth_response = await self.get_response(
            int(chat_id),
            "Lets break down my long term goals into smaller, achievable objectives for the next three months.",
        )
        out_voice = io.BytesIO()
        synth_response.export(out_f=out_voice, format="ogg", codec="libopus")  # type: ignore
        await self._send_message(context, update.effective_chat.id, agent_response)
        await context.bot.send_voice(chat_id=str(chat_id), voice=out_voice)

    async def handle_telegram_monthly_goals(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        This function handles the '/monthly_goals' command from the user. It updates the system prompt
        by calling the 'update_prompt' function with the 'define-monthly-goals' prompt from the langchain hub.
        """
        assert update.effective_chat, "Chat must be defined!"
        chat_id = update.effective_chat.id
        # Call the 'update_prompt' function with the 'define-monthly-goals' prompt
        await self.change_stage("monthly-goals", chat_id=chat_id)
        await context.bot.send_message(
            chat_id=chat_id, text=f"System prompt updated to 'monthly-goals'."
        )
        # Get audio response from LLM/synth and reply
        agent_response, synth_response = await self.get_response(
            int(chat_id),
            "Lets further break down my trimester goals into monthly milestones.",
        )
        out_voice = io.BytesIO()
        synth_response.export(out_f=out_voice, format="ogg", codec="libopus")  # type: ignore
        await self._send_message(context, update.effective_chat.id, agent_response)
        await context.bot.send_voice(chat_id=str(chat_id), voice=out_voice)

    async def handle_telegram_daily_habits(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        This function handles the '/daily_habits' command from the user. It updates the system prompt
        by calling the 'update_prompt' function with the 'daily-habits' prompt from the langchain hub.
        """
        assert update.effective_chat, "Chat must be defined!"
        chat_id = update.effective_chat.id
        # Call the 'update_prompt' function with the 'define-daily-habits' prompt
        await self.change_stage("daily-habits", chat_id=chat_id)
        await context.bot.send_message(
            chat_id=chat_id, text=f"System prompt updated to 'daily-habits'."
        )
        # Get audio response from LLM/synth and reply
        agent_response, synth_response = await self.get_response(
            int(chat_id),
            "Lets establish daily habits that align with my goals and "
            "enable me to make progress on a consistent basis.",
        )
        out_voice = io.BytesIO()
        synth_response.export(out_f=out_voice, format="ogg", codec="libopus")  # type: ignore
        await self._send_message(context, update.effective_chat.id, agent_response)
        await context.bot.send_voice(chat_id=str(chat_id), voice=out_voice)

    async def handle_telegram_next_week_plan(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        this function handles the '/next-week-plan' command from the user. It updates the system prompt
        by calling the 'update_prompt' function with the 'next-week-plan' prompt from the langchain hub.
        """
        assert update.effective_chat, "Chat must be defined!"
        chat_id = update.effective_chat.id
        # Call the 'update_prompt' function with the 'next-week-plan' prompt
        await self.change_stage("next-week-plan", chat_id=chat_id)
        await context.bot.send_message(
            chat_id=chat_id, text=f"System prompt updated to 'next-week-plan'."
        )
        # Get audio response from LLM/synth and reply
        agent_response, synth_response = await self.get_response(
            int(chat_id), "Lets prepare a comprehensive plan for the upcoming week."
        )
        out_voice = io.BytesIO()
        synth_response.export(out_f=out_voice, format="ogg", codec="libopus")  # type: ignore
        await self._send_message(context, update.effective_chat.id, agent_response)
        await context.bot.send_voice(chat_id=str(chat_id), voice=out_voice)

    async def handle_telegram_next_day_plan(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        This function handles the '/next-day-plan' command from the user. It updates the system prompt
        by calling the 'update_prompt' function with the 'next-day-plan' prompt from the langchain hub.
        """
        assert update.effective_chat, "Chat must be defined!"
        chat_id = update.effective_chat.id
        # Call the 'update_prompt' function with the 'next-day-plan' prompt
        await self.change_stage("next-day-plan", chat_id=chat_id)
        await context.bot.send_message(
            chat_id=chat_id, text=f"System prompt updated to 'next-day-plan'."
        )
        # Get audio response from LLM/synth and reply
        agent_response, synth_response = await self.get_response(
            int(chat_id),
            "Lets prepare a comprehensive plan for next day, "
            "taking into account my personal and professional commitments.",
        )
        out_voice = io.BytesIO()
        synth_response.export(out_f=out_voice, format="ogg", codec="libopus")  # type: ignore
        await self._send_message(context, update.effective_chat.id, agent_response)
        await context.bot.send_voice(chat_id=str(chat_id), voice=out_voice)

    async def handle_telegram_unknown_cmd(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat, "Chat must be defined!"
        self.log.info(f"Received update: {update}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "Sorry, I didn't understand that command. Use /help to see available commands"
            ),
        )

    async def handle_telegram_emoji_reaction(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        This function handles the event when a user updates their emoji reaction to a message.
        It first checks if the chat is defined, then it retrieves the chat id, message id, and the new emoji.
        It logs the received new emoji reaction for debugging purposes.
        Then it retrieves the message from the all_messages dictionary using the message id.
        Finally, it stores the message in the database along with the new emoji and the current planning stage.
        """
        # Ensure the chat is defined
        assert update.effective_chat, "Chat must be defined!"
        self.log.debug(f"Received emoji Reaction: {update}")
        # Retrieve the chat id
        chat_id = update.effective_chat.id
        # Retrieve the message id
        message_id = update.message_reaction.message_id
        # Retrieve the new emoji
        new_emoji = update.message_reaction.new_reaction[0].emoji
        # Log the received new emoji reaction
        self.log.info(f"Received new emoji reaction: {new_emoji}")
        # Retrieve the message from the all_messages dictionary
        message = self.all_messages[message_id]
        # Store the message in the database along with the new emoji and the current planning stage
        current_stage = await self.database.get_current_onboarding_stage(chat_id)

        await self.database.store_telegram_message(
            message, new_emoji, current_stage
        )

    # add handler to log all events:
    async def handle_telegram_all(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        self.log.info(f"Received update: {update}")

    async def handle_telegram_list_goals_and_habits(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        This function handles the /list_goals_and_habits command from the user.
        It fetches all the goals and habits associated with the user from the database,
        formats them in a user-friendly way, and sends the formatted data as a response.
        """
        # Ensure the chat is defined
        assert update.effective_chat, "Chat must be defined!"
        # Retrieve the chat id
        chat_id = update.effective_chat.id
        # Fetch goals and habits from the database
        goals_and_habits = await self.database.get_stored_messages_by_planning_stage(
            chat_id
        )

        # Format the fetched data in a user-friendly way
        for key, value in goals_and_habits.items():
            await self._send_message(context, chat_id, f"# {key}")
            await self._send_message(context, chat_id, f"{value}")

    async def handle_telegram_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        help_text = (
            "Hello! I'm your voice chatbot. Here's how you can interact with me:\n"
            "- Send me a voice message, and I'll reply with a voice message.\n"
            "- Use /start to begin the onboarding process.\n"
            "- Use /status to display the status of the user in the onboarding process.\n"
            "- Use /long_term_goals to set your long-term goals.\n"
            "- Use /trimester_goals to define your goals for the trimester.\n"
            "- Use /monthly_goals to define your goals for the month.\n"
            "- Use /daily_habits to define your daily habits.\n"
            "- Use /next_week_plan to plan your next week.\n"
            "- Use /next_day_plan to plan your next day.\n"
            "- Use /list_goals_and_habits to list all your stored goals and habits.\n"
        )
        assert update.effective_chat, "Chat must be defined!"
        # if isinstance(self.synthesizer, CoquiSynthesizer):
        #     help_text += "\n- Use /create <voice_description> to create a new Coqui voice from a text prompt and switch to it."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)
