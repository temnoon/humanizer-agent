# Database Switching Guide

## Overview

The Humanizer Agent now supports clean switching between multiple databases. This allows you to:

- **Test imports** in isolated databases without affecting production
- **Maintain separate environments** (production, test, staging, archive)
- **Switch instantly** between databases with a single command
- **Backup and restore** databases easily

## Quick Start

### 1. List Available Profiles

```bash
cd backend
./dbswitch list
```

Shows all configured database profiles (production, test, archive, etc.)

### 2. Switch to a Database

```bash
./dbswitch switch test
```

Switches to the test database. The backend will use this database on next startup.

### 3. Check Current Database

```bash
./dbswitch current
```

Shows which database profile is currently active.

## Tools Provided

### `dbswitch` - Database Profile Switcher

Manages database profiles and switching between them.

**Commands:**
- `list` - Show all available database profiles
- `switch <profile>` - Switch to a specific database
- `current` - Show currently active database
- `info <profile>` - Show profile details
- `create <name>` - Create a new database profile

**Example Workflow:**
```bash
# See what's available
./dbswitch list

# Switch to test database
./dbswitch switch test

# Restart backend to apply changes
./start.sh

# Switch back to production
./dbswitch switch production
```

### `dbinit` - Database Initializer

Creates and manages PostgreSQL databases.

**Commands:**
- `create <name>` - Create a new database
- `schema <name>` - Initialize schema in existing database
- `stats <name>` - Show database statistics (table counts, sizes)
- `backup <name>` - Backup database to SQL file
- `restore <name> <file>` - Restore from backup
- `reset <name>` - Drop and recreate database (with automatic backup)

**Example Workflow:**
```bash
# Create a new database for testing
./dbinit create humanizer_import_test

# Initialize the schema
./dbinit schema humanizer_import_test

# Check it worked
./dbinit stats humanizer_import_test

# Create a profile for it
./dbswitch create import_test
# (follow prompts, use database name: humanizer_import_test)

# Switch to it
./dbswitch switch import_test
```

## Database Profiles

Profiles are stored in `backend/db_profiles/` as `.env` files.

### Built-in Profiles

**production** (`production.env`)
- Database: `humanizer`
- Main production database with full dataset

**test** (`test.env`)
- Database: `humanizer_test`
- Testing database for experiments and QA

**archive** (`archive.env`)
- Database: `humanizer_archive`
- Long-term archive storage

### Creating Custom Profiles

```bash
./dbswitch create staging
```

Follow prompts to configure:
- Database name
- User/password
- Host/port

Profile saved to `db_profiles/staging.env`

## Testing Archive Imports

To test importing archives into a fresh database:

### 1. Create and Setup New Database

```bash
# Create database
./dbinit create humanizer_import_test

# Initialize schema
./dbinit schema humanizer_import_test

# Create profile
./dbswitch create import_test
# Enter database name: humanizer_import_test

# Switch to it
./dbswitch switch import_test

# Restart backend
./start.sh
```

### 2. Import Archives

With backend running on the new database:

```bash
# Frontend should now connect to humanizer_import_test
# Use the import UI to import your ChatGPT/Claude archives
```

### 3. Verify Import

```bash
# Check database stats
./dbinit stats humanizer_import_test

# Should show:
# - conversations (collections)
# - messages
# - chunks
# - media
```

### 4. Switch Back to Production

```bash
./dbswitch switch production
./start.sh  # Restart backend
```

Your test database remains intact and you can switch back anytime.

## Safety Features

### Automatic Backups

- `dbinit reset` creates backup before dropping database
- Backups saved as `<database>-pre-reset-YYYYMMDD-HHMMSS.sql`

### Confirmation Prompts

All destructive operations require explicit confirmation:
- Dropping databases
- Resetting databases
- Overwriting existing databases

### API Key Preservation

When switching profiles, your `ANTHROPIC_API_KEY` is automatically preserved from the previous `.env`.

## Advanced Usage

### Backup Production Before Testing

```bash
# Backup production
./dbinit backup humanizer
# Creates: humanizer-20251007-123456.sql

# Switch to test
./dbswitch switch test

# If you mess up test, restore production backup
./dbinit restore humanizer_test humanizer-20251007-123456.sql
```

### Clone Production to Test

```bash
# Backup production
./dbinit backup humanizer humanizer-snapshot.sql

# Reset test database
./dbinit reset humanizer_test

# Restore production data to test
./dbinit restore humanizer_test humanizer-snapshot.sql

# Switch to test
./dbswitch switch test
```

### Multiple Test Environments

```bash
# Create test1
./dbinit create humanizer_test1
./dbinit schema humanizer_test1
./dbswitch create test1

# Create test2
./dbinit create humanizer_test2
./dbinit schema humanizer_test2
./dbswitch create test2

# Switch between them
./dbswitch switch test1
./dbswitch switch test2
./dbswitch switch production
```

## Troubleshooting

### Profile not taking effect

**Problem:** Switched profile but backend still uses old database

**Solution:** Restart the backend server
```bash
# Stop backend (Ctrl+C)
./start.sh  # Start again
```

### Schema errors after switching

**Problem:** New database missing tables

**Solution:** Initialize schema
```bash
./dbinit schema <database_name>
```

### Database doesn't exist

**Problem:** Profile points to non-existent database

**Solution:** Create the database
```bash
./dbinit create <database_name>
./dbinit schema <database_name>
```

### Check which database is actually connected

```bash
# With backend running, check logs on startup
# Should show: "Initializing database connection: postgresql+asyncpg://..."

# Or query database directly
psql -U humanizer -h localhost -c "SELECT current_database();"
```

## Architecture

### How Profiles Work

1. Profiles stored as `.env` files in `db_profiles/`
2. `dbswitch` copies selected profile to `backend/.env`
3. Backend reads `DATABASE_URL` from `.env` on startup
4. Active profile tracked in `.active_db_profile`

### File Locations

```
backend/
├── .env                        # Active configuration (copied from profile)
├── .env.backup                 # Automatic backup of previous .env
├── .active_db_profile          # Tracks current profile name
├── db_profiles/
│   ├── production.env          # Production database
│   ├── test.env                # Test database
│   ├── archive.env             # Archive database
│   └── custom.env              # Your custom profiles
├── dbswitch                    # Profile switcher CLI
└── dbinit                      # Database initializer CLI
```

## Best Practices

1. **Always backup before destructive operations**
   ```bash
   ./dbinit backup humanizer
   ```

2. **Use test databases for experiments**
   ```bash
   ./dbswitch switch test
   ```

3. **Document custom profiles**
   - Add comments to profile `.env` files
   - Note what each database is for

4. **Keep production and test separate**
   - Never test imports in production
   - Use test database first, then copy to production if satisfied

5. **Regular backups**
   ```bash
   # Daily backup cron job
   0 2 * * * cd /path/to/backend && ./dbinit backup humanizer
   ```

## FAQ

**Q: Can I switch databases without restarting?**

A: No. The backend reads `DATABASE_URL` from `.env` only at startup. You must restart after switching.

**Q: Will switching delete my data?**

A: No. Switching only changes which database the backend connects to. All databases remain intact.

**Q: Can I have the same archive in multiple databases?**

A: Yes. Import the same archive files into different databases. They're completely isolated.

**Q: How do I see all my databases?**

A: `psql -U humanizer -h localhost -l | grep humanizer`

**Q: Can I use this in production?**

A: Yes, but be careful with destructive operations. Always backup first.

## Next Steps

1. **Test the system:**
   ```bash
   ./dbswitch list
   ./dbswitch switch test
   ./start.sh
   ```

2. **Import test data:**
   - Use frontend to import a small archive
   - Verify it imported correctly
   - Check database stats

3. **Switch back to production:**
   ```bash
   ./dbswitch switch production
   ./start.sh
   ```

Now you have isolated, switchable databases! 🎉
