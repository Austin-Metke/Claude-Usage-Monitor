# API Reset Time Monitor

Continuously monitors an API endpoint for reset times and sends email notifications when resets occur.

## Features

- ✅ **Intelligent sleep scheduling** - sleeps until reset time instead of continuous polling
- ✅ Monitors multiple reset periods (e.g., five_hour, seven_day)
- ✅ Sends Gmail notifications when resets occur
- ✅ Automatically fetches fresh data after each reset
- ✅ Robust error handling and exponential backoff
- ✅ Minimal API calls - only fetches when needed
- ✅ Can run as a systemd service

## Prerequisites

- Python 3.7+
- One of the following for notifications:
  - Gmail account with App Password enabled, OR
  - Webhook endpoint (Discord, Slack channel), OR
  - Slack Bot for direct messages, OR
  - Any combination of the above
- Linux server (optional, for systemd service)

## Notification Methods

The script supports four notification methods:

### 1. Email (SMTP)
Send notifications via any SMTP server (Gmail, Outlook, custom mail server).

**Pros:**
- Easy to set up with Gmail
- Familiar notification method
- Works anywhere

**Cons:**
- Requires App Password for Gmail
- Credentials stored in environment

### 2. Webhook
Send JSON payload to any webhook endpoint (Discord channels, Slack channels, custom servers).

**Pros:**
- No credentials needed (just a URL)
- Works with Discord, Slack, custom servers
- More secure than storing email passwords
- Can trigger other automations

**Cons:**
- Posts to a channel (public to channel members)
- Requires setting up a webhook receiver

### 3. Slack Direct Message (Recommended!)
Send messages directly to your Slack DMs via a Slack bot.

**Pros:**
- **Private** - Only you see notifications
- No channel spam
- Mobile push notifications via Slack app
- Works across workspaces
- Searchable message history

**Cons:**
- Requires creating a Slack app (5 minutes)
- Need bot token and user ID

See **[SLACK_SETUP.md](SLACK_SETUP.md)** for step-by-step instructions.

### 4. Multiple Methods
Send notifications via multiple methods simultaneously (e.g., email + Slack DM).

**Webhook Payload Example:**
```json
{
  "reset_type": "five_hour",
  "reset_time": "2026-02-17T04:00:00+00:00",
  "utilization": 27.0,
  "message": "API reset: five_hour",
  "timestamp": "2026-02-17T04:00:05+00:00"
}
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Create Environment File

Copy the example environment file and edit it with your configuration:

```bash
cp .env.example .env
nano .env
```

**Required for all:**
- `API_URL` - Your API endpoint
- `NOTIFICATION_METHOD` - Choose `email`, `webhook`, `slack_dm`, or `both`

**Required for email notifications:**
- `SMTP_USER` - Your email address
- `SMTP_PASSWORD` - Your email password/app password
- `RECIPIENT_EMAIL` - Where to send notifications
- `SMTP_HOST` - SMTP server (default: smtp.gmail.com)
- `SMTP_PORT` - SMTP port (default: 587)

**Required for webhook notifications:**
- `WEBHOOK_URL` - Your webhook endpoint URL

**Required for Slack DM notifications:**
- `SLACK_BOT_TOKEN` - Your Slack bot token (starts with `xoxb-`)
- `SLACK_USER_ID` - Your Slack user ID (starts with `U`)

### 3a. Gmail Setup (if using email)

You need a Gmail App Password (not your regular password):

1. Go to your Google Account: https://myaccount.google.com/
2. Select **Security** from the left menu
3. Under "How you sign in to Google," select **2-Step Verification** (you must enable this first)
4. At the bottom, select **App passwords**
5. Select **Mail** and your device
6. Google will generate a 16-character password - **copy this!**
7. Add it to your `.env` file as `SMTP_PASSWORD`

### 3b. Webhook Setup (if using webhook)

#### Discord Webhook:
1. Go to your Discord server settings → Integrations → Webhooks
2. Create a webhook, copy the URL
3. Add to `.env` as `WEBHOOK_URL`

#### Slack Webhook:
1. Go to https://api.slack.com/messaging/webhooks
2. Create an incoming webhook
3. Copy the webhook URL
4. Add to `.env` as `WEBHOOK_URL`

#### Custom Webhook:
Point `WEBHOOK_URL` to your own server endpoint that accepts POST requests with JSON.

### 3c. Slack DM Setup (if using Slack DMs)

**Quick Setup (5 minutes):**

1. Create a Slack App at https://api.slack.com/apps
2. Add the `chat:write` bot scope
3. Install app to workspace → Copy **Bot User OAuth Token** (starts with `xoxb-`)
4. Get your **User ID**:
   - Click your profile → Profile → ⋯ → Copy member ID (starts with `U`)
5. Add to `.env`:
   ```env
   NOTIFICATION_METHOD=slack_dm
   SLACK_BOT_TOKEN=xoxb-your-token-here
   SLACK_USER_ID=U01234567
   ```

**Full instructions:** See **[SLACK_SETUP.md](SLACK_SETUP.md)** for detailed step-by-step guide.

### 4. Test the Script

Run manually to verify everything works:

```bash
python3 reset_monitor.py
```

You should see log output like:
```
2026-02-16 10:30:00 - INFO - Starting reset monitor...
2026-02-16 10:30:00 - INFO - API URL: https://...
2026-02-16 10:30:01 - INFO - Fetching reset time data from API...
2026-02-16 10:30:01 - INFO - five_hour: 17.49 hours until reset
2026-02-16 10:30:01 - INFO - seven_day: 63.49 hours until reset
2026-02-16 10:30:01 - INFO - ⏰ Sleeping for 17.49 hours until five_hour reset
2026-02-16 10:30:01 - INFO -    Will wake at 2026-02-17T03:59:55+00:00
```

Press `Ctrl+C` to stop.

## Running as a Background Service

### Option 1: Using systemd (Recommended)

1. **Edit the service file** to match your paths:
   ```bash
   nano reset-monitor.service
   ```
   
   Update these lines:
   ```ini
   User=austin  # Your username
   WorkingDirectory=/home/austin/reset-monitor  # Your script directory
   ExecStart=/usr/bin/python3 /home/austin/reset-monitor/reset_monitor.py
   ```

2. **Copy to systemd directory:**
   ```bash
   sudo cp reset-monitor.service /etc/systemd/system/
   ```

3. **Enable and start the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable reset-monitor
   sudo systemctl start reset-monitor
   ```

4. **Check status:**
   ```bash
   sudo systemctl status reset-monitor
   ```

5. **View logs:**
   ```bash
   sudo journalctl -u reset-monitor -f
   # OR
   tail -f reset_monitor.log
   ```

### Option 2: Using screen/tmux

```bash
screen -S reset-monitor
python3 reset_monitor.py
# Press Ctrl+A, then D to detach

# Reattach later:
screen -r reset-monitor
```

### Option 3: Using nohup

```bash
nohup python3 reset_monitor.py &
tail -f reset_monitor.log
```

## Managing the Service

```bash
# Start the service
sudo systemctl start reset-monitor

# Stop the service
sudo systemctl stop reset-monitor

# Restart the service
sudo systemctl restart reset-monitor

# View status
sudo systemctl status reset-monitor

# View logs
sudo journalctl -u reset-monitor -f
```

## How It Works

1. **Fetches API data** to get all reset times
2. **Parses reset times** from the JSON response (five_hour, seven_day, etc.)
3. **Finds the earliest upcoming reset** time
4. **Sleeps until that time** (wakes up 5 seconds before to account for clock drift)
5. **Sends email notification** when reset time is reached
6. **Makes fresh GET request** immediately after reset
7. **Repeats** - finds next reset time and sleeps again
8. **Logs everything** to `reset_monitor.log`

This approach is much more efficient than polling - instead of checking every 30 seconds, it only wakes up when needed!

## Example JSON Structure

The script expects JSON like this:

```json
{
    "five_hour": {
        "utilization": 27.0,
        "resets_at": "2026-02-17T04:00:00.621176+00:00"
    },
    "seven_day": {
        "utilization": 81.0,
        "resets_at": "2026-02-19T01:59:59.621201+00:00"
    }
}
```

## Email Notification Example

When a reset occurs, you'll receive an email like:

```
Subject: 🔄 API Reset: five_hour

API Reset Notification
======================

Reset Type: five_hour
Reset Time: 2026-02-17T04:00:00.621176+00:00
Previous Utilization: 27.0%

The API has been reset and is ready for new requests.
```

## Troubleshooting

### Configuration Issues

- Verify `.env` file exists and is in the same directory as the script
- Check that all required environment variables are set
- Make sure there are no quotes around values in `.env` file
- Verify API_URL is accessible: `curl $API_URL`

### Email Not Sending

- Verify Gmail App Password is correct (16 characters, no spaces in .env)
- Check that 2-Step Verification is enabled on your Google Account
- Try sending a test email manually with the same credentials
- Check firewall isn't blocking port 587
- Verify SMTP_USER and RECIPIENT_EMAIL are valid email addresses

### Webhook Not Working

- Test webhook URL with curl: `curl -X POST -H "Content-Type: application/json" -d '{"test":"data"}' $WEBHOOK_URL`
- For Discord: Verify webhook hasn't been deleted
- For Slack: Check workspace permissions
- Check webhook server logs for errors
- Verify URL is complete and correctly formatted

### Slack DM Not Working

- Verify bot token starts with `xoxb-` (not `xoxp-`)
- Verify user ID starts with `U` (not `C` for channels)
- Check that `chat:write` scope is added to the bot
- Reinstall the Slack app after adding scopes
- Make sure bot is installed to your workspace
- Test manually: 
  ```bash
  curl -X POST -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"channel":"'$SLACK_USER_ID'","text":"Test"}' \
    https://slack.com/api/chat.postMessage
  ```

### Script Not Finding Resets

- Verify API_URL is correct and accessible
- Check that JSON structure matches expected format
- Look at `reset_monitor.log` for parsing errors
- Test API manually: `curl -s $API_URL | jq .`

### Service Won't Start

- Check file paths in `reset-monitor.service`
- Verify Python path: `which python3`
- Check permissions on script: `chmod +x reset_monitor.py`
- View errors: `sudo journalctl -u reset-monitor -n 50`

## Configuration Options

All configuration is done via environment variables in the `.env` file:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `API_URL` | Your API endpoint | Yes | - |
| `NOTIFICATION_METHOD` | `email`, `webhook`, `slack_dm`, or `both` | Yes | `email` |
| `SMTP_HOST` | SMTP server hostname | If using email | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | If using email | `587` |
| `SMTP_USER` | Your email address | If using email | - |
| `SMTP_PASSWORD` | Email password/app password | If using email | - |
| `RECIPIENT_EMAIL` | Notification recipient email | If using email | - |
| `WEBHOOK_URL` | Webhook endpoint URL | If using webhook | - |
| `SLACK_BOT_TOKEN` | Slack bot token (xoxb-...) | If using Slack DM | - |
| `SLACK_USER_ID` | Your Slack user ID (U...) | If using Slack DM | - |
| `SLEEP_BUFFER` | Seconds to wake before reset | No | `5` |
| `MAX_RETRY_DELAY` | Max seconds between retries | No | `300` |

## Log Files

- `reset_monitor.log` - Main application log with all events
- Also outputs to console/systemd journal

## Notes

- The script uses UTC timezone for all comparisons
- Intelligently sleeps until the next reset time instead of continuous polling
- Wakes up 5 seconds before reset to account for clock drift
- Fetches fresh data immediately after each reset
- Script automatically recovers from network errors with exponential backoff
- Handles multiple concurrent reset periods efficiently

## Security Best Practices

🔒 **Never commit your `.env` file to Git!** It contains sensitive credentials.

- The `.env` file is already in `.gitignore`
- Always use `.env.example` as a template
- For production, consider using:
  - System environment variables
  - Secret management services (AWS Secrets Manager, HashiCorp Vault)
  - Encrypted configuration files
- Webhook method is more secure than email (no password storage)
- Use restrictive file permissions: `chmod 600 .env`

## License

MIT - Feel free to modify as needed!
