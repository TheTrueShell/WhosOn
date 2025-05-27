import discord
from discord.ext import commands, tasks
import mcstatus
from mcstatus import JavaServer, BedrockServer
import asyncio
import json
import os
from datetime import datetime
import aiofiles
import traceback
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('WhosOn')

# Bot configuration
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.guilds = True
INTENTS.members = True

bot = commands.Bot(command_prefix='!', intents=INTENTS)

# Data storage file
DATA_FILE = 'whoson_data.json'

# In-memory storage for server data
guild_data = {}

# Colors for embeds
COLOR_ONLINE = 0x00ff00
COLOR_OFFLINE = 0xff0000
COLOR_INFO = 0x00a8ff
COLOR_WARNING = 0xffff00

async def load_data():
    """Load stored data from file"""
    global guild_data
    if os.path.exists(DATA_FILE):
        async with aiofiles.open(DATA_FILE, 'r') as f:
            content = await f.read()
            guild_data = json.loads(content) if content else {}
            logger.info(f"Loaded data for {len(guild_data)} guilds")
    else:
        guild_data = {}
        logger.info("No existing data file found, starting fresh")

async def save_data():
    """Save data to file"""
    async with aiofiles.open(DATA_FILE, 'w') as f:
        await f.write(json.dumps(guild_data, indent=2))
    logger.debug("Data saved to file")

def get_server_type(address):
    """Attempt to determine server type (Java or Bedrock)"""
    logger.info(f"Auto-detecting server type for {address}")
    
    # Try Java first (default)
    try:
        server = JavaServer.lookup(address)
        server.status()
        logger.info(f"Detected {address} as Java server")
        return "java"
    except Exception as e:
        logger.debug(f"Java detection failed for {address}: {e}")
    
    # Try Bedrock
    try:
        # If no port specified, add default Bedrock port
        if ':' not in address:
            bedrock_address = f"{address}:19132"
        else:
            bedrock_address = address
        server = BedrockServer.lookup(bedrock_address)
        server.status()
        logger.info(f"Detected {address} as Bedrock server")
        return "bedrock"
    except Exception as e:
        logger.debug(f"Bedrock detection failed for {address}: {e}")
    
    logger.warning(f"Could not detect server type for {address}")
    return None

async def get_server_status(address, server_type="java"):
    """Get status information from a Minecraft server"""
    try:
        if server_type == "java":
            server = JavaServer.lookup(address)
            status = await asyncio.to_thread(server.status)
            
            # Try to get query data if available
            query_data = None
            try:
                query_data = await asyncio.to_thread(server.query)
                logger.debug(f"Query data retrieved for {address}")
            except:
                logger.debug(f"Query not available for {address}")
            
            return {
                "online": True,
                "type": "java",
                "players_online": status.players.online,
                "players_max": status.players.max,
                "latency": round(status.latency, 2),
                "version": status.version.name,
                "motd": status.description if isinstance(status.description, str) else str(status.description),
                "player_list": [p.name for p in (status.players.sample or [])] if status.players.sample else [],
                "query_data": {
                    "software": query_data.software.brand if query_data and hasattr(query_data.software, 'brand') else None,
                    "plugins": query_data.software.plugins if query_data and hasattr(query_data.software, 'plugins') else [],
                    "map": query_data.map if query_data else None
                } if query_data else None
            }
        
        elif server_type == "bedrock":
            server = BedrockServer.lookup(address)
            status = await asyncio.to_thread(server.status)
            
            return {
                "online": True,
                "type": "bedrock",
                "players_online": status.players.online,
                "players_max": status.players.max,
                "latency": round(status.latency, 2),
                "version": status.version.version if hasattr(status.version, 'version') else "Bedrock",
                "motd": status.motd,
                "map": status.map if hasattr(status, 'map') else None,
                "gamemode": status.gamemode if hasattr(status, 'gamemode') else None
            }
    
    except Exception as e:
        logger.error(f"Error getting status for {address}: {e}")
        return {
            "online": False,
            "error": str(e),
            "type": server_type
        }

def create_status_embed(server_data, address, nickname=None):
    """Create an embed with server status information"""
    if server_data["online"]:
        embed = discord.Embed(
            title=f"📊 {nickname or address}",
            color=COLOR_ONLINE,
            timestamp=datetime.utcnow()
        )
        
        # Basic info
        embed.add_field(
            name="Status",
            value="🟢 Online",
            inline=True
        )
        embed.add_field(
            name="Players",
            value=f"{server_data['players_online']}/{server_data['players_max']}",
            inline=True
        )
        embed.add_field(
            name="Latency",
            value=f"{server_data['latency']}ms",
            inline=True
        )
        
        # Server type and version
        embed.add_field(
            name="Type",
            value=server_data['type'].capitalize(),
            inline=True
        )
        embed.add_field(
            name="Version",
            value=server_data.get('version', 'Unknown'),
            inline=True
        )
        
        # MOTD
        if server_data.get('motd'):
            # Clean MOTD of formatting codes
            motd = server_data['motd']
            if isinstance(motd, str):
                # Remove Minecraft color codes
                import re
                motd = re.sub(r'§[0-9a-fklmnor]', '', motd)
            embed.add_field(
                name="MOTD",
                value=f"`{motd[:1024]}`",  # Discord field limit
                inline=False
            )
        
        # Player list (Java only)
        if server_data['type'] == 'java' and server_data.get('player_list'):
            players = server_data['player_list'][:20]  # Limit to 20 players
            if players:
                player_str = ", ".join(players)
                if len(server_data['player_list']) > 20:
                    player_str += f" ... and {len(server_data['player_list']) - 20} more"
                embed.add_field(
                    name="Online Players",
                    value=player_str[:1024],
                    inline=False
                )
        
        # Bedrock specific info
        if server_data['type'] == 'bedrock':
            if server_data.get('gamemode'):
                embed.add_field(
                    name="Gamemode",
                    value=server_data['gamemode'],
                    inline=True
                )
            if server_data.get('map'):
                embed.add_field(
                    name="Map",
                    value=server_data['map'],
                    inline=True
                )
        
        # Query data (Java only)
        if server_data.get('query_data'):
            query = server_data['query_data']
            if query.get('software'):
                embed.add_field(
                    name="Software",
                    value=query['software'],
                    inline=True
                )
            if query.get('map'):
                embed.add_field(
                    name="Map",
                    value=query['map'],
                    inline=True
                )
            if query.get('plugins'):
                plugins = query['plugins'][:5]  # Limit to 5 plugins
                plugin_str = ", ".join(plugins)
                if len(query['plugins']) > 5:
                    plugin_str += f" ... and {len(query['plugins']) - 5} more"
                embed.add_field(
                    name="Plugins",
                    value=plugin_str[:1024],
                    inline=False
                )
        
        embed.set_footer(text=f"Server: {address}")
        
    else:
        embed = discord.Embed(
            title=f"📊 {nickname or address}",
            description="🔴 **Server Offline**",
            color=COLOR_OFFLINE,
            timestamp=datetime.utcnow()
        )
        if server_data.get('error'):
            embed.add_field(
                name="Error",
                value=str(server_data['error'])[:1024],
                inline=False
            )
        embed.set_footer(text=f"Server: {address}")
    
    return embed

def check_bot_permissions(guild):
    """Check if bot has required permissions"""
    bot_member = guild.me
    permissions = bot_member.guild_permissions
    
    required = {
        "manage_channels": permissions.manage_channels,
        "manage_roles": permissions.manage_roles,
        "view_channel": permissions.view_channel,
        "send_messages": permissions.send_messages,
        "embed_links": permissions.embed_links,
        "read_message_history": permissions.read_message_history,
    }
    
    missing = [perm for perm, has in required.items() if not has]
    
    if missing:
        logger.warning(f"Missing permissions in {guild.name}: {missing}")
    
    return missing

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Connected to {len(bot.guilds)} guilds')
    
    # Check permissions in each guild
    for guild in bot.guilds:
        missing = check_bot_permissions(guild)
        if missing:
            logger.warning(f"Missing permissions in {guild.name}: {missing}")
    
    await load_data()
    update_all_servers.start()

@bot.event
async def on_guild_remove(guild):
    """Clean up data when bot is removed from a guild"""
    guild_id = str(guild.id)
    if guild_id in guild_data:
        del guild_data[guild_id]
        await save_data()
        logger.info(f"Cleaned up data for removed guild: {guild.name}")

# Slash Commands
@bot.slash_command(name="add", description="Add a Minecraft server to track")
@discord.default_permissions(manage_guild=True)
async def add_server(
    ctx: discord.ApplicationContext,
    address: discord.Option(str, "Server address (e.g., play.example.com or play.example.com:25565)", required=True),
    nickname: discord.Option(str, "Friendly name for the server", required=False),
    server_type: discord.Option(str, "Server type", choices=["auto", "java", "bedrock"], default="auto")
):
    """Add a new Minecraft server to track"""
    guild_id = str(ctx.guild.id)
    
    logger.info(f"Adding server {address} to guild {ctx.guild.name}")
    
    # Initialize guild data if not set up
    if guild_id not in guild_data:
        # Check bot permissions first
        missing = check_bot_permissions(ctx.guild)
        if missing:
            # Generate invite link with required permissions
            permissions = discord.Permissions(
                manage_channels=True,
                manage_roles=True,
                view_channel=True,
                send_messages=True,
                embed_links=True,
                read_message_history=True,
                use_slash_commands=True
            )
            invite_link = discord.utils.oauth_url(bot.user.id, permissions=permissions, guild=ctx.guild)
            
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description=f"The bot is missing required permissions:\n**{', '.join(missing)}**\n\nPlease grant these permissions or [re-invite the bot]({invite_link}) with the correct permissions.",
                color=COLOR_OFFLINE
            )
            embed.add_field(
                name="💡 Important",
                value="Make sure the bot's role is positioned high enough in the role hierarchy to manage channels effectively.",
                inline=False
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        # Initialize guild data
        guild_data[guild_id] = {
            "servers": {},
            "voice_channels": {},
            "text_channels": {}
        }
        await save_data()
        logger.info(f"Initialized guild data for: {ctx.guild.name}")
    
    # Defer response as this might take a moment
    await ctx.defer()
    
    # Auto-detect server type if needed
    actual_type = server_type
    if server_type == "auto":
        detected_type = get_server_type(address)
        if detected_type:
            actual_type = detected_type
        else:
            embed = discord.Embed(
                title="❌ Server Not Found",
                description=f"Could not connect to `{address}`. Please check the address and try again.",
                color=COLOR_OFFLINE
            )
            await ctx.followup.send(embed=embed)
            return
    
    # Test connection
    status = await get_server_status(address, actual_type)
    if not status["online"]:
        embed = discord.Embed(
            title="⚠️ Server Offline",
            description=f"The server at `{address}` appears to be offline. Adding it anyway...",
            color=COLOR_WARNING
        )
        embed.add_field(name="Error", value=status.get('error', 'Unknown error'), inline=False)
    else:
        embed = discord.Embed(
            title="✅ Server Added",
            description=f"Successfully connected to {actual_type.capitalize()} server!",
            color=COLOR_ONLINE
        )
    
    # Create a safe key for the server
    server_key = address.replace(":", "_").replace(".", "_")
    
    try:
        # Create channels
        category = discord.utils.get(ctx.guild.categories, name="WhosOn Tracking")
        if not category:
            logger.info("Creating WhosOn Tracking category")
            category = await ctx.guild.create_category("WhosOn Tracking")
        
        # Create voice channel for stats
        voice_channel_name = f"📊 {nickname or address}"
        logger.info(f"Creating voice channel: {voice_channel_name}")
        
        # Create permission overwrites to ensure bot has manage_channels
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(connect=False),
            ctx.guild.me: discord.PermissionOverwrite(
                manage_channels=True,
                view_channel=True,
                connect=True
            )
        }
        
        voice_channel = await ctx.guild.create_voice_channel(
            voice_channel_name,
            category=category,
            user_limit=0,  # No one can join
            overwrites=overwrites
        )
        
        logger.info("Created voice channel with explicit bot permissions")
        
        # Verify permissions were set correctly
        bot_perms = voice_channel.permissions_for(ctx.guild.me)
        if not bot_perms.manage_channels:
            logger.warning("Bot still lacks manage_channels permission after creation, attempting to fix...")
            try:
                await voice_channel.set_permissions(ctx.guild.me, manage_channels=True, overwrite=True)
                logger.info("Successfully fixed bot permissions on voice channel")
            except discord.Forbidden:
                logger.error("Could not fix bot permissions - this may cause update issues")
                embed.add_field(
                    name="⚠️ Warning",
                    value="Could not ensure bot has manage permissions. Voice channel updates may fail.",
                    inline=False
                )
        else:
            logger.info("Bot permissions verified successfully")
        
        # Create text channel for detailed info
        text_channel_name = f"{nickname or address}".lower().replace(" ", "-").replace(".", "-").replace(":", "")
        logger.info(f"Creating text channel: {text_channel_name}")
        
        # Create permission overwrites for text channel - read-only for users
        text_overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(
                send_messages=False,
                add_reactions=True,
                create_public_threads=False,
                create_private_threads=False,
                send_messages_in_threads=False,
                view_channel=True,
                read_message_history=True
            ),
            ctx.guild.me: discord.PermissionOverwrite(
                send_messages=True,
                embed_links=True,
                view_channel=True,
                read_message_history=True,
                manage_messages=True
            )
        }
        
        text_channel = await ctx.guild.create_text_channel(
            text_channel_name,
            category=category,
            topic=f"Tracking {address}",
            overwrites=text_overwrites
        )
        
        # Send initial embed
        status_embed = create_status_embed(status, address, nickname)
        message = await text_channel.send(embed=status_embed)
        
        # Store server data
        guild_data[guild_id]["servers"][server_key] = {
            "address": address,
            "nickname": nickname,
            "type": actual_type,
            "voice_channel_id": voice_channel.id,
            "text_channel_id": text_channel.id,
            "message_id": message.id
        }
        
        await save_data()
        
        embed.add_field(
            name="Channels Created",
            value=f"Voice: {voice_channel.mention}\nText: {text_channel.mention}",
            inline=False
        )
        
        logger.info(f"Successfully added server {address} to guild {ctx.guild.name}")
        
    except Exception as e:
        logger.error(f"Error adding server: {e}")
        logger.error(traceback.format_exc())
        embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred while adding the server: {str(e)}",
            color=COLOR_OFFLINE
        )
    
    await ctx.followup.send(embed=embed)

@bot.slash_command(name="remove", description="Stop tracking a Minecraft server")
@discord.default_permissions(manage_guild=True)
async def remove_server(
    ctx: discord.ApplicationContext,
    server: discord.Option(str, "Server to remove", autocomplete=True)
):
    """Remove a tracked server"""
    guild_id = str(ctx.guild.id)
    
    logger.info(f"Removing server {server} from guild {ctx.guild.name}")
    
    if guild_id not in guild_data or server not in guild_data[guild_id]["servers"]:
        embed = discord.Embed(
            title="❌ Server Not Found",
            description="That server is not being tracked.",
            color=COLOR_OFFLINE
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return
    
    await ctx.defer()
    
    server_data = guild_data[guild_id]["servers"][server]
    
    # Get channels before deletion
    voice_channel = bot.get_channel(server_data["voice_channel_id"])
    text_channel = bot.get_channel(server_data["text_channel_id"])
    category = None
    
    # Get the category from one of the channels
    if voice_channel and voice_channel.category:
        category = voice_channel.category
    elif text_channel and text_channel.category:
        category = text_channel.category
    
    # Delete channels
    channels_deleted = []
    errors = []
    
    try:
        if voice_channel:
            await voice_channel.delete()
            channels_deleted.append("voice")
            logger.info(f"Deleted voice channel: {voice_channel.name}")
    except Exception as e:
        logger.error(f"Error deleting voice channel: {e}")
        errors.append(f"voice channel: {str(e)}")
    
    try:
        if text_channel:
            await text_channel.delete()
            channels_deleted.append("text")
            logger.info(f"Deleted text channel: {text_channel.name}")
    except Exception as e:
        logger.error(f"Error deleting text channel: {e}")
        errors.append(f"text channel: {str(e)}")
    
    # Remove from data
    del guild_data[guild_id]["servers"][server]
    
    # Check if this was the last server and clean up category if needed
    category_deleted = False
    if category and category.name == "WhosOn Tracking":
        # Check if there are any remaining servers
        remaining_servers = len(guild_data[guild_id]["servers"])
        
        if remaining_servers == 0:
            # Check if category is empty (no other channels)
            category_channels = category.channels
            if len(category_channels) == 0:
                try:
                    await category.delete()
                    category_deleted = True
                    logger.info(f"Deleted empty WhosOn Tracking category")
                except Exception as e:
                    logger.error(f"Error deleting category: {e}")
                    errors.append(f"category: {str(e)}")
            else:
                logger.info(f"Category not deleted - contains {len(category_channels)} other channels")
    
    await save_data()
    
    logger.info(f"Removed server {server} from guild {ctx.guild.name}")
    
    # Create response embed
    embed = discord.Embed(
        title="✅ Server Removed",
        description=f"Stopped tracking `{server_data['address']}`",
        color=COLOR_INFO
    )
    
    if channels_deleted:
        embed.add_field(
            name="Channels Deleted",
            value=", ".join(channels_deleted),
            inline=False
        )
    
    if category_deleted:
        embed.add_field(
            name="Category Cleaned Up",
            value="Removed empty 'WhosOn Tracking' category",
            inline=False
        )
    
    if errors:
        embed.add_field(
            name="⚠️ Errors",
            value="\n".join([f"• {error}" for error in errors]),
            inline=False
        )
        embed.color = COLOR_WARNING
    
    # Add helpful info if this was the last server
    remaining_servers = len(guild_data[guild_id]["servers"])
    if remaining_servers == 0:
        embed.add_field(
            name="ℹ️ No More Servers",
            value="You're no longer tracking any servers. Use `/add` to add a new one.",
            inline=False
        )
    
    await ctx.followup.send(embed=embed)

@bot.slash_command(name="list", description="List all tracked Minecraft servers")
async def list_servers(ctx: discord.ApplicationContext):
    """List all tracked servers"""
    guild_id = str(ctx.guild.id)
    
    if guild_id not in guild_data or not guild_data[guild_id]["servers"]:
        embed = discord.Embed(
            title="📋 Tracked Servers",
            description="No servers are currently being tracked.",
            color=COLOR_INFO
        )
        await ctx.respond(embed=embed)
        return
    
    embed = discord.Embed(
        title="📋 Tracked Servers",
        color=COLOR_INFO
    )
    
    for key, server in guild_data[guild_id]["servers"].items():
        value = f"**Address:** `{server['address']}`\n**Type:** {server['type'].capitalize()}"
        embed.add_field(
            name=server.get('nickname') or server['address'],
            value=value,
            inline=False
        )
    
    await ctx.respond(embed=embed)

@bot.slash_command(name="update", description="Force update all server statuses")
@discord.default_permissions(manage_guild=True)
async def force_update(ctx: discord.ApplicationContext):
    """Force an immediate update of all servers"""
    guild_id = str(ctx.guild.id)
    
    if guild_id not in guild_data:
        await ctx.respond("No servers configured.", ephemeral=True)
        return
    
    await ctx.defer()
    
    logger.info(f"Force updating servers for guild {ctx.guild.name}")
    
    updated = 0
    errors = 0
    for server_key, server_info in guild_data[guild_id]["servers"].items():
        try:
            await update_server_status(ctx.guild.id, server_key)
            updated += 1
        except Exception as e:
            logger.error(f"Error updating {server_key}: {e}")
            errors += 1
    
    embed = discord.Embed(
        title="✅ Update Complete",
        description=f"Updated {updated} server(s)",
        color=COLOR_INFO
    )
    if errors > 0:
        embed.add_field(
            name="Errors",
            value=f"{errors} server(s) failed to update",
            inline=False
        )
    await ctx.followup.send(embed=embed)

@bot.slash_command(name="permissions", description="Check and fix bot permissions")
@discord.default_permissions(manage_guild=True)
async def permissions(ctx: discord.ApplicationContext):
    """Check bot permissions and attempt to fix issues"""
    guild_id = str(ctx.guild.id)
    
    if guild_id not in guild_data or not guild_data[guild_id]["servers"]:
        await ctx.respond("No servers are being tracked.", ephemeral=True)
        return
    
    await ctx.defer()
    
    embed = discord.Embed(
        title="🔍 Permission Check & Fix",
        color=COLOR_INFO
    )
    
    # Check general guild permissions
    bot_member = ctx.guild.me
    guild_perms = bot_member.guild_permissions
    
    embed.add_field(
        name="Guild Permissions",
        value=f"Manage Channels: {'✅' if guild_perms.manage_channels else '❌'}\n"
              f"Manage Roles: {'✅' if guild_perms.manage_roles else '❌'}\n"
              f"Send Messages: {'✅' if guild_perms.send_messages else '❌'}",
        inline=False
    )
    
    # Check and fix each voice channel
    issues = []
    fixed = 0
    errors = 0
    
    for server_key, server_info in guild_data[guild_id]["servers"].items():
        voice_channel = bot.get_channel(server_info["voice_channel_id"])
        if voice_channel:
            channel_perms = voice_channel.permissions_for(bot_member)
            
            if not channel_perms.manage_channels:
                # Try to fix permissions
                try:
                    await voice_channel.set_permissions(ctx.guild.me, manage_channels=True)
                    fixed += 1
                    logger.info(f"Fixed permissions for voice channel: {voice_channel.name}")
                except discord.Forbidden:
                    issues.append(f"• {voice_channel.name}: Permission denied")
                    errors += 1
                except Exception as e:
                    issues.append(f"• {voice_channel.name}: {str(e)}")
                    errors += 1
        else:
            issues.append(f"• Channel not found for {server_info['address']}")
            errors += 1
    
    # Add results to embed
    if fixed > 0:
        embed.add_field(
            name="✅ Fixed",
            value=f"Successfully fixed permissions for {fixed} channel(s)",
            inline=False
        )
    
    if issues:
        embed.add_field(
            name="❌ Issues Found",
            value="\n".join(issues[:10]) + ("..." if len(issues) > 10 else ""),
            inline=False
        )
        embed.add_field(
            name="💡 Solutions",
            value="1. Ensure the bot's role is higher than any role restrictions on the voice channels\n"
                  "2. Grant the bot 'Manage Channels' permission server-wide\n"
                  "3. Try removing and re-adding the affected servers",
            inline=False
        )
        embed.color = COLOR_WARNING
    elif fixed == 0:
        embed.add_field(
            name="✅ All Good",
            value="No permission issues detected!",
            inline=False
        )
    
    await ctx.followup.send(embed=embed)

@bot.slash_command(name="cleanup", description="Remove all tracked servers and clean up all WhosOn channels")
@discord.default_permissions(administrator=True)
async def cleanup(ctx: discord.ApplicationContext):
    """Remove all tracked servers and clean up channels"""
    guild_id = str(ctx.guild.id)
    
    if guild_id not in guild_data or not guild_data[guild_id]["servers"]:
        await ctx.respond("No servers are currently being tracked.", ephemeral=True)
        return
    
    # Confirmation check
    embed = discord.Embed(
        title="⚠️ Confirm Cleanup",
        description=f"This will remove **{len(guild_data[guild_id]['servers'])} server(s)** and delete all associated channels and categories.\n\n**This action cannot be undone!**",
        color=COLOR_WARNING
    )
    
    # Create confirmation view
    class ConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.confirmed = False
        
        @discord.ui.button(label="Confirm Cleanup", style=discord.ButtonStyle.danger, emoji="🗑️")
        async def confirm_cleanup(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.confirmed = True
            self.stop()
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)
            
            # Perform cleanup
            await perform_cleanup(interaction)
        
        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
        async def cancel_cleanup(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.stop()
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            cancel_embed = discord.Embed(
                title="❌ Cleanup Cancelled",
                description="No changes were made.",
                color=COLOR_INFO
            )
            await interaction.response.edit_message(embed=cancel_embed, view=self)
    
    async def perform_cleanup(interaction):
        """Perform the actual cleanup"""
        # Update the original message to show cleanup is starting
        cleanup_embed = discord.Embed(
            title="🧹 Cleanup in Progress",
            description="Starting cleanup...",
            color=COLOR_INFO
        )
        await interaction.edit_original_response(embed=cleanup_embed, view=None)
        
        servers_to_remove = list(guild_data[guild_id]["servers"].keys())
        channels_deleted = 0
        categories_deleted = 0
        errors = []
        
        # Delete all server channels
        for server_key in servers_to_remove:
            server_info = guild_data[guild_id]["servers"][server_key]
            
            # Delete voice channel
            try:
                voice_channel = bot.get_channel(server_info["voice_channel_id"])
                if voice_channel:
                    await voice_channel.delete()
                    channels_deleted += 1
                    logger.info(f"Deleted voice channel: {voice_channel.name}")
            except Exception as e:
                logger.error(f"Error deleting voice channel for {server_key}: {e}")
                errors.append(f"Voice channel for {server_info['address']}: {str(e)}")
            
            # Delete text channel
            try:
                text_channel = bot.get_channel(server_info["text_channel_id"])
                if text_channel:
                    await text_channel.delete()
                    channels_deleted += 1
                    logger.info(f"Deleted text channel: {text_channel.name}")
            except Exception as e:
                logger.error(f"Error deleting text channel for {server_key}: {e}")
                errors.append(f"Text channel for {server_info['address']}: {str(e)}")
        
        # Clean up WhosOn Tracking category
        try:
            category = discord.utils.get(ctx.guild.categories, name="WhosOn Tracking")
            if category:
                # Check if category is empty
                if len(category.channels) == 0:
                    await category.delete()
                    categories_deleted += 1
                    logger.info("Deleted WhosOn Tracking category")
                else:
                    logger.info(f"WhosOn Tracking category not deleted - contains {len(category.channels)} other channels")
        except Exception as e:
            logger.error(f"Error deleting category: {e}")
            errors.append(f"Category: {str(e)}")
        
        # Clear all server data
        guild_data[guild_id]["servers"] = {}
        await save_data()
        
        # Create final result embed
        result_embed = discord.Embed(
            title="✅ Cleanup Complete",
            description=f"Successfully removed {len(servers_to_remove)} server(s)",
            color=COLOR_INFO if not errors else COLOR_WARNING
        )
        
        result_embed.add_field(
            name="Summary",
            value=f"Channels deleted: {channels_deleted}\nCategories deleted: {categories_deleted}",
            inline=False
        )
        
        if errors:
            result_embed.add_field(
                name="⚠️ Errors",
                value="\n".join([f"• {error}" for error in errors[:10]]) + ("..." if len(errors) > 10 else ""),
                inline=False
            )
        
        result_embed.add_field(
            name="ℹ️ Next Steps",
            value="Use `/add` to start tracking servers again.",
            inline=False
        )
        
        await interaction.edit_original_response(embed=result_embed, view=None)
    
    view = ConfirmView()
    await ctx.respond(embed=embed, view=view)

# Autocomplete for server selection
async def server_autocomplete(ctx: discord.AutocompleteContext):
    """Provide autocomplete options for server selection"""
    guild_id = str(ctx.interaction.guild.id)
    if guild_id not in guild_data:
        return []
    
    servers = guild_data[guild_id]["servers"]
    return [key for key in servers.keys()]

# Update the remove_server autocomplete
remove_server.options[0].autocomplete = server_autocomplete

# Background task to update server statuses
@tasks.loop(seconds=120)
async def update_all_servers():
    """Update all tracked servers every 2 minutes"""
    for guild_id in guild_data:
        for server_key in guild_data[guild_id]["servers"]:
            try:
                await update_server_status(int(guild_id), server_key)
                # Small delay between updates to spread out API calls
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error updating {server_key} in guild {guild_id}: {e}")

async def update_server_status(guild_id, server_key):
    """Update a specific server's status"""
    guild_id_str = str(guild_id)
    server_info = guild_data[guild_id_str]["servers"][server_key]
    
    # Get current status
    status = await get_server_status(server_info["address"], server_info["type"])
    
    # Update voice channel
    voice_channel = bot.get_channel(server_info["voice_channel_id"])
    if voice_channel:
        if status["online"]:
            name = f"🟢 {server_info.get('nickname') or server_info['address']}: {status['players_online']}/{status['players_max']}"
        else:
            name = f"🔴 {server_info.get('nickname') or server_info['address']}: Offline"
        
        # Truncate if too long
        if len(name) > 100:
            name = name[:97] + "..."
        
        # Only update if the name has actually changed
        if voice_channel.name != name:
            try:
                # Check if bot has permission to manage this specific channel
                bot_permissions = voice_channel.permissions_for(voice_channel.guild.me)
                if not bot_permissions.manage_channels:
                    logger.warning(f"Bot lacks manage_channels permission for voice channel {voice_channel.name} in {voice_channel.guild.name}")
                    return
                
                await voice_channel.edit(name=name)
                logger.info(f"Updated voice channel name from '{voice_channel.name}' to '{name}'")
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    logger.warning(f"Rate limited updating voice channel for {server_key} - will retry next cycle")
                elif e.status == 403:  # Forbidden
                    logger.error(f"Permission denied updating voice channel {voice_channel.name}: {e}. Bot role may be lower than channel permissions.")
                    
                    # Try alternative approaches
                    try:
                        # Attempt 1: Try without emoji
                        if status["online"]:
                            fallback_name = f"{server_info.get('nickname') or server_info['address']}: {status['players_online']}/{status['players_max']} (Online)"
                        else:
                            fallback_name = f"{server_info.get('nickname') or server_info['address']}: Offline"
                        
                        if len(fallback_name) > 100:
                            fallback_name = fallback_name[:97] + "..."
                        
                        if voice_channel.name != fallback_name:
                            await voice_channel.edit(name=fallback_name)
                            logger.info(f"Successfully updated voice channel using fallback name: {fallback_name}")
                        return
                    except discord.HTTPException:
                        pass
                    
                    # Attempt 2: Try to recreate the channel permissions
                    try:
                        await voice_channel.set_permissions(voice_channel.guild.me, manage_channels=True, overwrite=True)
                        await voice_channel.edit(name=name)
                        logger.info(f"Successfully updated voice channel after fixing permissions: {name}")
                        return
                    except discord.HTTPException:
                        pass
                    
                    logger.error(f"All fallback attempts failed for voice channel {voice_channel.name}")
                else:
                    logger.error(f"Error updating voice channel: {e}")
            except Exception as e:
                logger.error(f"Unexpected error updating voice channel: {e}")
        else:
            logger.debug(f"Voice channel name unchanged for {server_key}: {name}")
    
    # Update text channel embed
    text_channel = bot.get_channel(server_info["text_channel_id"])
    if text_channel:
        try:
            message = await text_channel.fetch_message(server_info["message_id"])
            embed = create_status_embed(status, server_info["address"], server_info.get("nickname"))
            await message.edit(embed=embed)
        except discord.NotFound:
            # Message deleted, send a new one
            logger.info(f"Message not found for {server_key}, creating new one")
            embed = create_status_embed(status, server_info["address"], server_info.get("nickname"))
            message = await text_channel.send(embed=embed)
            guild_data[guild_id_str]["servers"][server_key]["message_id"] = message.id
            await save_data()
        except Exception as e:
            logger.error(f"Error updating message: {e}")

# Run the bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("No bot token found! Please set DISCORD_BOT_TOKEN in your .env file")
        exit(1)
    
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")