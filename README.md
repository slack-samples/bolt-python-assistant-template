# AI Agent App Template (Bolt for Python)

This Bolt for Python template demonstrates how to build [AI Apps](https://docs.slack.dev/ai/) in Slack.

Models from [OpenAI](https://openai.com) are used and can be customized for prompts of all kinds.

## Setup

Before getting started, make sure you have a development workspace where you have permissions to install apps. If you don’t have one setup, go ahead and [create one](https://slack.com/create).

### Developer Program

Join the [Slack Developer Program](https://api.slack.com/developer-program) for exclusive access to sandbox environments for building and testing your apps, tooling, and resources created to help you build and grow.

## Installation

Add this app to your workspace using either the Slack CLI or other development tooling, then read ahead to configuring LLM responses in the **[Providers](#providers)** section.

### Using Slack CLI

Install the latest version of the Slack CLI for your operating system:

- [Slack CLI for macOS & Linux](https://docs.slack.dev/tools/slack-cli/guides/installing-the-slack-cli-for-mac-and-linux/)
- [Slack CLI for Windows](https://docs.slack.dev/tools/slack-cli/guides/installing-the-slack-cli-for-windows/)

You'll also need to log in if this is your first time using the Slack CLI.

```sh
slack login
```

#### Initializing the project

```sh
slack create my-bolt-python-assistant --template slack-samples/bolt-python-assistant-template
cd my-bolt-python-assistant
```

#### Creating the Slack app

Use the following command to add your new Slack app to your development workspace. Choose a "local" app environment for upcoming development:

```sh
slack install
```

After the Slack app has been created you're all set to configure the LLM provider!

### Using Terminal

1. Open [https://api.slack.com/apps/new](https://api.slack.com/apps/new) and choose "From an app manifest"
2. Choose the workspace you want to install the application to
3. Copy the contents of [manifest.json](./manifest.json) into the text box that says `*Paste your manifest code here*` (within the JSON tab) and click _Next_
4. Review the configuration and click _Create_
5. Click _Install to Workspace_ and _Allow_ on the screen that follows. You'll then be redirected to the App Configuration dashboard.

#### Environment Variables

Before you can run the app, you'll need to store some environment variables.

1. Rename `.env.sample` to `.env`.
2. Open your apps setting page from [this list](https://api.slack.com/apps), click _OAuth & Permissions_ in the left hand menu, then copy the _Bot User OAuth Token_ into your `.env` file under `SLACK_BOT_TOKEN`.

```sh
SLACK_BOT_TOKEN=YOUR_SLACK_BOT_TOKEN
```

3. Click _Basic Information_ from the left hand menu and follow the steps in the _App-Level Tokens_ section to create an app-level token with the `connections:write` scope. Copy that token into your `.env` as `SLACK_APP_TOKEN`.

```sh
SLACK_APP_TOKEN=YOUR_SLACK_APP_TOKEN
```

#### Initializing the project

```sh
git clone https://github.com/slack-samples/bolt-python-assistant-template.git my-bolt-python-assistant
cd my-bolt-python-assistant
```

#### Setup your python virtual environment

```sh
python3 -m venv .venv
source .venv/bin/activate  # for Windows OS, .\.venv\Scripts\Activate instead should work
```

#### Install dependencies

```sh
pip install -r requirements.txt
```

## Providers

### OpenAI Setup

Unlock the OpenAI models from your OpenAI account dashboard by clicking [create a new secret key](https://platform.openai.com/api-keys), then save your OpenAI key into the `.env` file as `OPENAI_API_KEY` like so:

```zsh
OPENAI_API_KEY=YOUR_OPEN_API_KEY
```

## Development

### Starting the app

#### Slack CLI

```sh
slack run
```

#### Terminal

```sh
python3 app.py
```

Start talking to the bot! Start a new DM or thread and click the feedback button when it responds.

### Linting

```sh
# Run ruff check from root directory for linting
ruff check

# Run ruff format from root directory for code formatting
ruff format
```

## Project Structure

### `manifest.json`

`manifest.json` is a configuration for Slack apps. With a manifest, you can create an app with a pre-defined configuration, or adjust the configuration of an existing app.

### `app.py`

`app.py` is the entry point for the application and is the file you'll run to start the server. This project aims to keep this file as thin as possible, primarily using it as a way to route inbound requests.

### `/listeners`

Every incoming request is routed to a "listener". This directory groups each listener based on the Slack Platform feature used, so `/listeners/events` handles incoming events, `/listeners/shortcuts` would handle incoming [Shortcuts](https://docs.slack.dev/interactivity/implementing-shortcuts/) requests, and so on.

**`/listeners/assistant`**

Configures the new Slack Assistant features, providing a dedicated side panel UI for users to interact with the AI chatbot. This module includes:

- The `assistant_thread_started.py` file, which responds to new app threads with a list of suggested prompts.
- The `message.py` file, which responds to user messages sent to app threads or from the **Chat** and **History** tab with an LLM generated response.

### `/ai`

The `llm_caller.py` file, which handles OpenAI API integration and message formatting. It includes the `call_llm()` function that sends conversation threads to OpenAI's models.

## App Distribution / OAuth

Only implement OAuth if you plan to distribute your application across multiple workspaces. A separate `app_oauth.py` file can be found with relevant OAuth settings.

When using OAuth, Slack requires a public URL where it can send requests. In this template app, we've used [`ngrok`](https://ngrok.com/download). Checkout [this guide](https://ngrok.com/docs#getting-started-expose) for setting it up.

Start `ngrok` to access the app on an external network and create a redirect URL for OAuth.

```
ngrok http 3000
```

This output should include a forwarding address for `http` and `https` (we'll use `https`). It should look something like the following:

```
Forwarding   https://3cb89939.ngrok.io -> http://localhost:3000
```

Navigate to **OAuth & Permissions** in your app configuration and click **Add a Redirect URL**. The redirect URL should be set to your `ngrok` forwarding address with the `slack/oauth_redirect` path appended. For example:

```
https://3cb89939.ngrok.io/slack/oauth_redirect
```
