# WhosOn Discord Bot

WhosOn is a Discord bot that tracks Minecraft servers (both Java and Bedrock editions) and displays their status in real-time using voice channels for at-a-glance stats and text channels for detailed information.

## Files Included

- `main.py` - The main bot file
- `requirements.txt` - Python dependencies
- `generate_invite.py` - Helper to generate bot invite link
- `setup_check.py` - Verify your installation
- `.env.example` - Example environment configuration
- `.gitignore` - Git ignore file
- `README.md` - This file

## Features

- **Multi-Server Support**: Each Discord server can track multiple Minecraft servers independently
- **Automatic Server Detection**: Automatically detects whether a server is Java or Bedrock edition
- **Real-Time Updates**: Updates server status every 60 seconds
- **Voice Channel Stats**: Shows online/offline status and player count in an unjoinable voice channel
- **Detailed Text Channel Info**: Displays comprehensive server information including:
  - Online/Offline status
  - Player count and list (Java only)
  - Server latency
  - MOTD (Message of the Day)
  - Version information
  - Gamemode and map (Bedrock only)
  - Plugin information (Java with Query enabled)
- **Clean Slash Commands**: Intuitive command interface with proper permissions
- **Persistent Storage**: Saves configuration between bot restarts
- **Debug Logging**: Comprehensive logging for troubleshooting

## Required Permissions

The bot requires these Discord permissions to function properly:
- **Manage Channels**: To create and manage tracking channels
- **Manage Roles**: To restrict voice channel access (prevent users from joining)
- **View Channels**: To see channels in the server
- **Send Messages**: To post status embeds
- **Embed Links**: To create rich embeds
- **Read Message History**: To update existing status messages
- **Use Slash Commands**: To register and respond to slash commands

**Important**: The bot's role must be positioned above @everyone in the role hierarchy for voice channel restrictions to work.

## Requirements

- Python 3.8 or higher
- Discord Bot Token
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository or download the bot files

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the bot directory with your Discord bot token:
```
DISCORD_BOT_TOKEN=your_bot_token_here
```

4. Verify your setup:
```bash
python setup_check.py
```

5. Generate a bot invite link with the correct permissions:
```bash
python generate_invite.py
```

6. Use the generated link to invite the bot to your Discord server

## Usage

### Initial Setup

1. Run the bot:
```bash
python main.py
```

For debug logging, set the LOG_LEVEL in your .env file:
```
LOG_LEVEL=DEBUG
```

2. In your Discord server, use the `/add` command to add your first server (requires Manage Server permission)

### Commands

All commands are slash commands:

- `/add` - Add a Minecraft server to track (Manage Server permission required)
  - `address`: Server address (e.g., play.example.com:25565)
  - `nickname`: Optional friendly name for the server
  - `server_type`: auto/java/bedrock (default: auto)
- `/remove` - Stop tracking a server (Manage Server permission required)
  - `server`: Select from autocomplete list
- `/list` - View all tracked servers
- `/update` - Manually update all server statuses (Manage Server permission required)
- `/permissions` - Check and fix bot permissions (Manage Server permission required)
- `/cleanup` - Remove all tracked servers and clean up all WhosOn channels (Administrator permission required)

### Adding a Server

1. Use `/add` command
2. Enter the server address (with or without port)
3. Optionally provide a nickname
4. Choose server type or leave as "auto" for automatic detection
5. The bot will create:
   - A voice channel showing server status and player count
   - A text channel with detailed server information

### Channel Organisation

The bot creates a "WhosOn Tracking" category with:
- Voice channels named: 🟢/🔴 [Server Name]: X/Y players
- Text channels with persistent embeds showing detailed information

## Server Type Detection

The bot will automatically detect whether a server is Java or Bedrock:
- Java servers typically use port 25565
- Bedrock servers typically use port 19132
- If auto-detection fails, you can manually specify the server type

## Troubleshooting

### "Missing Permissions" Error
If you get a "403 Forbidden: Missing Permissions" error:
- Ensure the bot has the "Manage Roles" permission
- Check that the bot's role is higher than @everyone in the role hierarchy
- Re-invite the bot using `python generate_invite.py` to ensure all permissions are granted
- Use the `/permissions` command to check for missing permissions
- Enable debug logging to see detailed permission checks:
  ```
  LOG_LEVEL=DEBUG
  ```

### Voice Channel Access
If the bot cannot restrict voice channel access:
- The bot needs "Manage Roles" permission
- The bot's role must be higher than @everyone in the server's role hierarchy
- Go to Server Settings > Roles and drag the bot's role above @everyone

### Server Shows as Offline
- Verify the server address and port
- Check if the server is actually online
- For Bedrock servers, ensure you're using the correct port (usually 19132)
- Some servers may have firewall rules blocking status queries

### Query Information Not Showing (Java)
- Query must be enabled in the server's `server.properties` file
- Set `enable-query=true` and restart the Minecraft server

### Bot Not Responding
- Ensure the bot has proper permissions in your Discord server
- Check that slash commands are enabled
- Verify the bot is online and running

## Data Storage

The bot stores configuration in `whoson_data.json`. This file contains:
- Guild-specific server configurations
- Channel IDs for updates
- Server nicknames and types

Back up this file regularly to preserve your configuration.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This bot is provided as-is for educational and personal use.