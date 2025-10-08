# Quick Start: Database Switching

## Test Archive Import in New Database

### Step 1: Create Fresh Test Database

```bash
cd backend

# Create database
./dbinit create humanizer_import_test

# Initialize schema
./dbinit schema humanizer_import_test

# Verify it was created
./dbinit stats humanizer_import_test
```

### Step 2: Create Profile for New Database

```bash
# Create profile
./dbswitch create import_test

# When prompted:
# - Database name: humanizer_import_test
# - User: humanizer
# - Password: humanizer
# - Host: localhost
# - Port: 5432
```

### Step 3: Switch to New Database

```bash
# Switch to import_test profile
./dbswitch switch import_test

# Verify switch
./dbswitch current
# Should show: Active Profile: import_test

# Restart backend server
./start.sh
```

### Step 4: Import Your Archive

Now the backend is connected to `humanizer_import_test`. Use the frontend to import:

1. Open http://localhost:5173
2. Navigate to Import section
3. Upload your ChatGPT/Claude archive
4. Watch it import into the test database

### Step 5: Verify Import

```bash
# Check database stats
./dbinit stats humanizer_import_test

# Should show tables with data:
# - collections (conversations)
# - messages
# - chunks
# - media

# Or connect directly:
psql -U humanizer -h localhost -d humanizer_import_test -c "SELECT COUNT(*) FROM collections;"
psql -U humanizer -h localhost -d humanizer_import_test -c "SELECT COUNT(*) FROM messages;"
```

### Step 6: Switch Back to Production

```bash
# Switch back
./dbswitch switch production

# Restart backend
./start.sh
```

Your test database `humanizer_import_test` remains intact. You can switch back anytime:

```bash
./dbswitch switch import_test
./start.sh
```

## Common Commands

### Listing & Switching

```bash
./dbswitch list              # Show all profiles
./dbswitch current           # Show active profile
./dbswitch switch test       # Switch to test database
./dbswitch switch production # Switch to production
```

### Database Management

```bash
./dbinit stats humanizer             # Show database stats
./dbinit backup humanizer            # Backup to SQL file
./dbinit create humanizer_new        # Create new database
./dbinit schema humanizer_new        # Initialize schema
```

### Quick Test Workflow

```bash
# 1. Create and setup
./dbinit create humanizer_test2 && ./dbinit schema humanizer_test2

# 2. Create profile
./dbswitch create test2  # Follow prompts

# 3. Switch and restart
./dbswitch switch test2 && ./start.sh

# 4. Import via frontend (http://localhost:5173)

# 5. Switch back
./dbswitch switch production && ./start.sh
```

## Tips

- **Always restart backend after switching**: Changes only take effect on server restart
- **Databases persist**: Switching doesn't delete data, just changes connection
- **Backup before experiments**: `./dbinit backup humanizer`
- **Check active database**: `./dbswitch current`
- **Clone production to test**: Backup production, restore to test database

## Troubleshooting

**Backend still using old database?**
→ Restart the server (Ctrl+C then `./start.sh`)

**Schema errors?**
→ Run `./dbinit schema <database_name>`

**Profile not found?**
→ Check `./dbswitch list` for available profiles

**Want to see database size?**
→ `./dbinit stats <database_name>`

## Architecture

```
Production DB ←→ dbswitch ←→ Test DB
    ↓                           ↓
humanizer                  humanizer_test
(1.8 GB)                  (10 MB, empty)

Your archives can be imported into EITHER database.
They remain completely separate and isolated.
```

## Next Steps

1. **Try it now:**
   ```bash
   ./dbswitch list
   ./dbswitch switch test
   ./start.sh
   ```

2. **Import a small test archive** to verify it works

3. **Switch back to production:**
   ```bash
   ./dbswitch switch production
   ./start.sh
   ```

You now have complete database isolation! 🎉

For more details, see [DATABASE_SWITCHING.md](./DATABASE_SWITCHING.md)
