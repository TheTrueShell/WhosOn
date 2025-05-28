"""
Migration script to convert WhosOn bot data from JSON to SQLite

This script will:
1. Read the existing whoson_data.json file
2. Create a new SQLite database with the proper schema
3. Migrate all server data to the new database
4. Create a backup of the original JSON file
"""

import json
import os
import asyncio
import logging
from datetime import datetime
import shutil

# Import the database module
from database import db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('WhosOn.Migration')

# File paths
JSON_FILE = 'whoson_data.json'
JSON_BACKUP = f'whoson_data.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'


async def migrate_data():
    """Main migration function"""
    logger.info("Starting migration from JSON to SQLite...")
    
    # Check if JSON file exists
    if not os.path.exists(JSON_FILE):
        logger.error(f"JSON file '{JSON_FILE}' not found. Nothing to migrate.")
        return False
    
    # Create backup of JSON file
    try:
        shutil.copy2(JSON_FILE, JSON_BACKUP)
        logger.info(f"Created backup: {JSON_BACKUP}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False
    
    # Load JSON data
    try:
        with open(JSON_FILE, 'r') as f:
            json_data = json.load(f)
        logger.info(f"Loaded data for {len(json_data)} guilds")
    except Exception as e:
        logger.error(f"Failed to load JSON data: {e}")
        return False
    
    # Initialize database
    try:
        await db.init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False
    
    # Migrate data
    total_servers = 0
    migrated_servers = 0
    failed_servers = 0
    
    for guild_id, guild_data in json_data.items():
        logger.info(f"Migrating guild {guild_id}...")
        
        if 'servers' not in guild_data:
            logger.warning(f"No servers found for guild {guild_id}")
            continue
        
        for server_key, server_info in guild_data['servers'].items():
            total_servers += 1
            
            try:
                # Prepare server data for database
                server_data = {
                    'address': server_info['address'],
                    'nickname': server_info.get('nickname'),
                    'type': server_info['type'],
                    'voice_channel_id': server_info['voice_channel_id'],
                    'text_channel_id': server_info['text_channel_id'],
                    'message_id': server_info['message_id']
                }
                
                # Add to database
                success = await db.add_server(guild_id, server_key, server_data)
                
                if success:
                    migrated_servers += 1
                    logger.debug(f"  ✓ Migrated server: {server_info['address']}")
                else:
                    failed_servers += 1
                    logger.error(f"  ✗ Failed to migrate server: {server_info['address']}")
                    
            except Exception as e:
                failed_servers += 1
                logger.error(f"  ✗ Error migrating server {server_key}: {e}")
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("MIGRATION SUMMARY")
    logger.info("="*50)
    logger.info(f"Total servers found: {total_servers}")
    logger.info(f"Successfully migrated: {migrated_servers}")
    logger.info(f"Failed to migrate: {failed_servers}")
    logger.info(f"JSON backup saved as: {JSON_BACKUP}")
    
    if failed_servers == 0:
        logger.info("\n✅ Migration completed successfully!")
        logger.info(f"\nYou can now delete the old JSON file: {JSON_FILE}")
        logger.info("The backup will be kept for safety.")
    else:
        logger.warning("\n⚠️ Migration completed with errors!")
        logger.warning("Please check the logs above for details.")
        logger.warning("The original JSON file has been preserved.")
    
    # Verify migration
    stats = await db.get_server_stats()
    logger.info(f"\nDatabase statistics:")
    logger.info(f"  - Total servers: {stats['total_servers']}")
    logger.info(f"  - Java servers: {stats['java_servers']}")
    logger.info(f"  - Bedrock servers: {stats['bedrock_servers']}")
    logger.info(f"  - Guilds: {stats['guilds']}")
    
    return failed_servers == 0


async def verify_migration():
    """Verify that the migration was successful by comparing counts"""
    logger.info("\nVerifying migration...")
    
    # Load JSON data
    try:
        with open(JSON_FILE, 'r') as f:
            json_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON data for verification: {e}")
        return False
    
    # Count servers in JSON
    json_server_count = 0
    for guild_data in json_data.values():
        if 'servers' in guild_data:
            json_server_count += len(guild_data['servers'])
    
    # Get database count
    db_stats = await db.get_server_stats()
    db_server_count = db_stats['total_servers']
    
    logger.info(f"Servers in JSON: {json_server_count}")
    logger.info(f"Servers in database: {db_server_count}")
    
    if json_server_count == db_server_count:
        logger.info("✅ Verification passed! All servers migrated successfully.")
        return True
    else:
        logger.error(f"❌ Verification failed! Server count mismatch.")
        logger.error(f"Missing servers: {json_server_count - db_server_count}")
        return False


async def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("WhosOn Bot - JSON to SQLite Migration Tool")
    print("="*60)
    print("\nThis tool will migrate your bot data from JSON to SQLite.")
    print(f"It will create a backup of your data at: {JSON_BACKUP}")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nMigration cancelled.")
        return
    
    # Run migration
    success = await migrate_data()
    
    if success:
        # Verify migration
        await verify_migration()
        
        print("\n" + "="*60)
        print("MIGRATION COMPLETE!")
        print("="*60)
        print("\nNext steps:")
        print("1. Start your bot - it will now use SQLite")
        print(f"2. Verify everything is working correctly")
        print(f"3. Delete the old JSON file: {JSON_FILE}")
        print(f"4. Keep the backup for safety: {JSON_BACKUP}")
    else:
        print("\n" + "="*60)
        print("MIGRATION FAILED!")
        print("="*60)
        print("\nPlease check the logs above for errors.")
        print("Your original data is preserved.")
        print("The bot will continue to work with the JSON file.")


if __name__ == "__main__":
    asyncio.run(main())