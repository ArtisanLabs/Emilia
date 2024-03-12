# Telegram Bot

WithMia assists you on defining long-term goals and then narrowing them down to quarters, months, weeks, and days. Use Mia daily to plan your days, gain clarity and focus. Text and voice notes welcome


## Docker

1. Set up the configuration for your telegram bot in `main.py`.
2. Set up an .env file using the template
3. Create a Telegram Bot token and link using The Bot Father: https://t.me/botfather

```
cp .env.template .env
```

Fill in your API keys into .env

3. Build the Docker image

```bash
docker build --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
             --build-arg VCS_REF=$(git rev-parse --short HEAD) \
             --build-arg VERSION=0.1.0 \
             -t ArtisanLabs/telegram-bot-mia:0.1.0 .
```

4. Run the image and forward the port.

```bash
docker run --env-file=.env -t ArtisanLabs/telegram-bot-mia:0.1.0
```

Now you have a telegram bot running. Visit the link you chose during the Telegram bot creation process.

## Non-docker setup

`main.py` is just a simple python script, so you can run it with:

```
poetry install
poetry run python main.py
```

## Developer Environment

To set up the developer environment, you need to install the dependencies listed in the `environment.docker.yml` file. 
We recommend using `mamba`, a fast, robust, and scalable package manager for Python. 
You can install it by following the instructions provided [here](https://github.com/mamba-org/mamba#install-mamba). 
Once installed, proceed with the following steps:

```bash
# 1. Create a new environment and install the dependencies by running the command:
conda env create -f environment.docker.yml

# 2. Activate the new environment by running the command:
conda activate telegram-bot-mia
```

To update the environment with new dependencies, use the following command:

```bash
mamba env update -f environment.docker.yml
```

Now, your developer environment is set up and ready to use.


# commands
```
start - Restart the assistant to begin a new conversation
status - Display the current state of your goal planning
long_term_goals - Start the process of defining your long-term goals
trimester_goals - Break down your long-term goals into achievable objectives for the next three months
monthly_goals - Further break down your trimester goals into monthly milestones
daily_habits - Establish daily habits that align with your goals and enable you to make progress on a consistent basis
next_week_plan - Prepare a comprehensive plan for the next week, taking into account your personal and professional commitments
help - Show available commands and how to interact with the assistant
```
