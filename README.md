A script that scrapes a local cinema's site for new films and publishes them to Telegram.
Requires at least Python 3.12 as well as the `python-dotenv` and `requests` libraries.
I don't know why you'd ever need this.

## Configuring

Copy `.env.example` into `.env` and configure as necessary:
- **TG_BOT_TOKEN** - the bot token you got from BotFather
- **TG_USER_ID** - your Telegram user ID, or of whoever's gonna be receiving the messages
  (note that this user must already have a chat with the bot started, or sending messages will fail)
- **TG_API** - API server to connect to, this allows you to use a proxy if you have issues accessing the Telegram API
- **TG_PROXY_KEY** - the authentication key for your proxy (if you're using one)
- **MK_SITE** - cinema site URL, not sure why you'd want to change this but it's here
- **MK_CINEMA_ID** - numeric location ID, obtained from site API
- **MK_CINEMA_LOCATION** - location name, obtained from URL (first path segment)

## Usage

Running `python check.py` will fetch upcoming films from the site API and send any new ones to the specified Telegram chat.
A log of previously seen films will be kept in the `.seen_ids` file.

This script does not set up any polling or automatic checks. If you want to check for updates periodically,
consider creating a cron job or something equivalent.

## API proxy

You can optionally provide a proxy server for the Telegram API. It should:
- accept POST requests with a JSON body
- handle the same URL format as the real Telegram API
- relay requests to the actual API servers and forward responses as-is

Proxy authentication can be optionally implemented by using a secret token,
which this script will send in the `X-Proxy-Auth` header.

If an error occurs on the proxy side, it should be returned as a standard API error with
the additional field `proxy_error` set to `true`:
```json
{"ok": false, "proxy_error": true, "description": "Something is wrong"}
```

An example implementation as a Cloudflare Worker can be seen in [proxy_worker.js](proxy_worker.js).