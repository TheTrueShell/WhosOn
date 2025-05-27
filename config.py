"""
Configuration file for WhosOn Discord Bot

This file contains all global configuration variables, constants, and settings
used throughout the bot. Modify these values to customize bot behaviour.
"""

import os
import discord
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# BOT CONFIGURATION
# ============================================================================

# Bot command prefix (for legacy commands if needed)
COMMAND_PREFIX = '!'

# Bot intents configuration
BOT_INTENTS = discord.Intents.default()
BOT_INTENTS.message_content = True
BOT_INTENTS.guilds = True
BOT_INTENTS.members = True

# Bot token from environment
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Log level from environment (defaults to INFO)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# Log format string
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Logger name
LOGGER_NAME = 'WhosOn'

# ============================================================================
# DATA STORAGE
# ============================================================================

# Main data storage file
DATA_FILE = 'whoson_data.json'

# JSON indentation for pretty printing
JSON_INDENT = 2

# ============================================================================
# DISCORD EMBED COLOURS
# ============================================================================

# Colour scheme for Discord embeds (hex values)
COLOR_ONLINE = 0x00ff00      # Green - server online
COLOR_OFFLINE = 0xff0000     # Red - server offline  
COLOR_INFO = 0x00a8ff        # Blue - informational messages
COLOR_WARNING = 0xffff00     # Yellow - warnings

# ============================================================================
# MINECRAFT SERVER CONFIGURATION
# ============================================================================

# Default ports for different server types
DEFAULT_JAVA_PORT = 25565
DEFAULT_BEDROCK_PORT = 19132

# Server type options
SERVER_TYPES = ["auto", "java", "bedrock"]

# Maximum number of players to display in embed
MAX_PLAYERS_DISPLAY = 20

# Maximum number of plugins to display in embed
MAX_PLUGINS_DISPLAY = 5

# Discord field character limits
DISCORD_FIELD_LIMIT = 1024
DISCORD_MOTD_LIMIT = 1024

# Minecraft colour code regex pattern
MINECRAFT_COLOR_REGEX = r'§[0-9a-fklmnor]'

# ============================================================================
# UPDATE INTERVALS
# ============================================================================

# How often to update server statuses (in seconds)
UPDATE_INTERVAL = 120  # 2 minutes

# Delay between individual server updates to spread API calls (in seconds)
UPDATE_DELAY_BETWEEN_SERVERS = 2

# ============================================================================
# DISCORD CHANNEL CONFIGURATION
# ============================================================================

# Category name for bot channels
CATEGORY_NAME = "WhosOn Tracking"

# Voice channel name format (will be formatted with status emoji, nickname/address, and player count)
VOICE_CHANNEL_FORMAT = "{status} {name}: {players_online}/{players_max}"
VOICE_CHANNEL_OFFLINE_FORMAT = "{status} {name}: Offline"

# Maximum length for Discord channel names
MAX_CHANNEL_NAME_LENGTH = 100

# Voice channel user limit (0 = no one can join)
VOICE_CHANNEL_USER_LIMIT = 0

# Status emojis for voice channels
STATUS_EMOJI_ONLINE = "🟢"
STATUS_EMOJI_OFFLINE = "🔴"

# ============================================================================
# BOT PERMISSIONS
# ============================================================================

# Required guild permissions for the bot
REQUIRED_GUILD_PERMISSIONS = [
    "manage_channels",
    "manage_roles", 
    "view_channel",
    "send_messages",
    "embed_links",
    "read_message_history"
]

# Required category permissions for the bot
REQUIRED_CATEGORY_PERMISSIONS = [
    "manage_channels",
    "view_channel",
    "send_messages", 
    "embed_links",
    "read_message_history",
    "manage_messages",
    "connect",
    "manage_roles"
]

# Permissions for bot invite link
INVITE_PERMISSIONS = discord.Permissions(
    manage_channels=True,
    manage_roles=True,
    view_channel=True,
    send_messages=True,
    embed_links=True,
    read_message_history=True,
    use_slash_commands=True
)

# ============================================================================
# DISCORD UI CONFIGURATION
# ============================================================================

# Confirmation timeout for dangerous operations (in seconds)
CONFIRMATION_TIMEOUT = 30

# Button labels and emojis
BUTTON_CONFIRM_CLEANUP = "Confirm Cleanup"
BUTTON_CANCEL = "Cancel"
EMOJI_TRASH = "🗑️"
EMOJI_CANCEL = "❌"

# ============================================================================
# ERROR HANDLING
# ============================================================================

# Maximum number of errors to display in embeds
MAX_ERRORS_DISPLAY = 10

# Rate limit handling
RATE_LIMIT_RETRY_DELAY = 5  # seconds

# ============================================================================
# EMBED CONFIGURATION
# ============================================================================

# Standard embed titles and descriptions
EMBED_TITLES = {
    'server_status': "📊 {name}",
    'server_added': "✅ Server Added", 
    'server_removed': "✅ Server Removed",
    'server_not_found': "❌ Server Not Found",
    'server_offline': "⚠️ Server Offline",
    'missing_permissions': "❌ Missing Permissions",
    'permission_error': "❌ Permission Error",
    'update_complete': "✅ Update Complete",
    'tracked_servers': "📋 Tracked Servers",
    'cleanup_confirm': "⚠️ Confirm Cleanup",
    'cleanup_cancelled': "❌ Cleanup Cancelled",
    'cleanup_complete': "✅ Cleanup Complete",
    'cleanup_progress': "🧹 Cleanup in Progress",
    'permission_check': "🔍 Permission Check & Fix"
}

# Standard embed field names
EMBED_FIELDS = {
    'status': "Status",
    'players': "Players", 
    'latency': "Latency",
    'type': "Type",
    'version': "Version",
    'motd': "MOTD",
    'online_players': "Online Players",
    'gamemode': "Gamemode",
    'map': "Map",
    'software': "Software",
    'plugins': "Plugins",
    'error': "Error",
    'channels_created': "Channels Created",
    'channels_deleted': "Channels Deleted",
    'missing_permissions': "Missing Permissions",
    'solutions': "💡 Solutions",
    'important': "💡 Important",
    'warning': "⚠️ Warning",
    'summary': "Summary",
    'next_steps': "ℹ️ Next Steps",
    'no_more_servers': "ℹ️ No More Servers"
}

# ============================================================================
# COMMAND DESCRIPTIONS
# ============================================================================

COMMAND_DESCRIPTIONS = {
    'add': "Add a Minecraft server to track",
    'remove': "Stop tracking a Minecraft server", 
    'list': "List all tracked Minecraft servers",
    'update': "Force update all server statuses",
    'permissions': "Check and fix bot permissions",
    'cleanup': "Remove all tracked servers and clean up all WhosOn channels"
}

# Command option descriptions
OPTION_DESCRIPTIONS = {
    'address': "Server address (e.g., play.example.com or play.example.com:25565)",
    'nickname': "Friendly name for the server",
    'server_type': "Server type",
    'server_to_remove': "Server to remove"
}

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate that all required configuration is present"""
    errors = []
    
    if not DISCORD_BOT_TOKEN:
        errors.append("DISCORD_BOT_TOKEN environment variable is not set")
    
    if LOG_LEVEL not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        errors.append(f"Invalid LOG_LEVEL: {LOG_LEVEL}")
    
    if UPDATE_INTERVAL < 60:
        errors.append("UPDATE_INTERVAL should be at least 60 seconds to avoid rate limits")
    
    if len(CATEGORY_NAME) > 100:
        errors.append("CATEGORY_NAME is too long for Discord")
    
    return errors

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_voice_channel_name(status_online, nickname, address, players_online=None, players_max=None):
    """Generate voice channel name based on server status"""
    name = nickname or address
    status_emoji = STATUS_EMOJI_ONLINE if status_online else STATUS_EMOJI_OFFLINE
    
    if status_online and players_online is not None and players_max is not None:
        channel_name = VOICE_CHANNEL_FORMAT.format(
            status=status_emoji,
            name=name,
            players_online=players_online,
            players_max=players_max
        )
    else:
        channel_name = VOICE_CHANNEL_OFFLINE_FORMAT.format(
            status=status_emoji,
            name=name
        )
    
    # Truncate if too long
    if len(channel_name) > MAX_CHANNEL_NAME_LENGTH:
        channel_name = channel_name[:MAX_CHANNEL_NAME_LENGTH-3] + "..."
    
    return channel_name

def get_text_channel_name(nickname, address):
    """Generate text channel name from server nickname or address"""
    name = nickname or address
    # Make it Discord channel name safe
    return name.lower().replace(" ", "-").replace(".", "-").replace(":", "")

def create_server_key(address):
    """Create a safe key for storing server data"""
    return address.replace(":", "_").replace(".", "_") 