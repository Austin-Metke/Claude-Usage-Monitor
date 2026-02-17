# Slack Direct Message Setup Guide

Get notifications sent directly to your Slack DMs - cleaner than channel webhooks!

## Why Slack DMs vs Webhooks?

**Slack Webhooks:**
- ✅ Easy to set up (2 minutes)
- ❌ Posts to a channel (not private)
- ❌ Can't send to DMs

**Slack Bot DMs:**
- ✅ Sends directly to your DMs (private)
- ✅ Works across multiple workspaces
- ✅ Can mention you (@user)
- ❌ Slightly more setup (5 minutes)

## Setup Steps

### 1. Create a Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Select **"From scratch"**
4. Name your app (e.g., "Reset Monitor")
5. Choose your workspace
6. Click **"Create App"**

### 2. Add Bot Permissions

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll down to **"Scopes"** → **"Bot Token Scopes"**
3. Click **"Add an OAuth Scope"**
4. Add the following scope:
   - `chat:write` - Send messages as the bot

That's all you need for DMs!

### 3. Install the App to Your Workspace

1. Scroll to the top of the **"OAuth & Permissions"** page
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. You'll see a **"Bot User OAuth Token"** starting with `xoxb-`
5. **Copy this token** - this is your `SLACK_BOT_TOKEN`

### 4. Get Your User ID

You need to find your Slack User ID (it starts with `U`):

**Method 1: View Profile**
1. In Slack, click your profile picture (top right)
2. Click **"Profile"**
3. Click the **three dots** (⋯) → **"Copy member ID"**
4. This is your `SLACK_USER_ID` (e.g., `U01234567`)

**Method 2: From a Message**
1. Right-click your name in any message
2. Select **"Copy member ID"**

**Method 3: Via API (if above don't work)**
```bash
curl -H "Authorization: Bearer xoxb-YOUR-BOT-TOKEN" \
  https://slack.com/api/users.list | grep -o 'U[A-Z0-9]\{8,\}'
```

### 5. Configure Your Monitor

Add to your `.env` file:

```env
NOTIFICATION_METHOD=slack_dm
SLACK_BOT_TOKEN=xoxb-1234567890-1234567890123-AbCdEfGhIjKlMnOpQrStUvWx
SLACK_USER_ID=U01234567
```

### 6. Test It!

Run your monitor and it should send you a DM when a reset occurs!

## Example Slack DM

When a reset occurs, you'll receive a DM like:

```
🔄 API Reset: five_hour

Reset Time: 2026-02-17T04:00:00+00:00
Previous Utilization: 27.0%

The API has been reset and is ready for new requests.
```

## Troubleshooting

### "Not in channel" Error
- The bot doesn't need to be invited to any channel for DMs
- Make sure you're using your User ID, not a channel ID

### Token Issues
- Verify token starts with `xoxb-` (not `xoxp-`)
- Make sure you copied the **Bot User OAuth Token**, not the User OAuth Token
- Reinstall the app if needed

### Permission Denied
- Verify you added the `chat:write` scope
- Reinstall the app after adding scopes

### Can't Find User ID
- Try all three methods above
- User IDs start with `U` (not `C` for channels or `W` for workspace)

## Advanced: Custom Formatting

You can customize the Slack message format with Slack's Block Kit:

```python
def send_slack_dm(reset_type: str, reset_time: str, utilization: float) -> bool:
    """Send formatted Slack message with blocks"""
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🔄 API Reset: {reset_type}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Reset Time:*\n{reset_time}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Utilization:*\n{utilization}%"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "The API has been reset and is ready for new requests."
                }
            ]
        }
    ]
    
    payload = {
        "channel": SLACK_USER_ID,
        "blocks": blocks
    }
    
    # ... rest of function
```

## Benefits of Slack DMs

✅ **Private** - Only you see the notifications  
✅ **Mobile** - Slack app on your phone  
✅ **No spam** - Doesn't clutter channels  
✅ **Searchable** - Easy to find past notifications  
✅ **Cross-workspace** - Works if you're in multiple workspaces  

## Security Notes

- Treat your bot token like a password
- Never commit it to Git (it's in .env which is gitignored)
- If exposed, regenerate it in the Slack App settings
- The bot can only DM users in workspaces where it's installed

## Multiple Users

To send to multiple people:
1. Each person needs to get their User ID
2. Store them in `.env` as comma-separated: `SLACK_USER_IDS=U123,U456,U789`
3. Update the script to loop through and send to each:

```python
user_ids = os.getenv('SLACK_USER_IDS', '').split(',')
for user_id in user_ids:
    send_slack_dm_to_user(user_id, message)
```

---

For more info on Slack apps: https://api.slack.com/start/building
