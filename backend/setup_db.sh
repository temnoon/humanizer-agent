#!/bin/bash

# Database setup script for Humanizer Agent PostgreSQL + pgvector

echo "🗄️  Setting up Humanizer Agent Database (PostgreSQL 17 + pgvector)"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL first:"
    echo ""
    echo "  macOS:   brew install postgresql@17"
    echo "  Ubuntu:  sudo apt-get install postgresql postgresql-contrib"
    echo "  Fedora:  sudo dnf install postgresql-server postgresql-contrib"
    echo ""
    exit 1
fi

# Detect PostgreSQL version on macOS
PG_VERSION=""
if command -v brew &> /dev/null; then
    if brew list postgresql@17 &> /dev/null; then
        PG_VERSION="17"
        echo "✓ Detected PostgreSQL 17"
    elif brew list postgresql@16 &> /dev/null; then
        PG_VERSION="16"
        echo "✓ Detected PostgreSQL 16"
    elif brew list postgresql@15 &> /dev/null; then
        PG_VERSION="15"
        echo "✓ Detected PostgreSQL 15"
    fi
fi

# Check if PostgreSQL is running
if ! pg_isready &> /dev/null; then
    echo "⚠️  PostgreSQL is not running. Starting PostgreSQL..."
    if command -v brew &> /dev/null && [ -n "$PG_VERSION" ]; then
        brew services start postgresql@$PG_VERSION
        echo "Started PostgreSQL $PG_VERSION"
    else
        sudo systemctl start postgresql
    fi
    sleep 3

    # Verify it started
    if ! pg_isready &> /dev/null; then
        echo "❌ Failed to start PostgreSQL. Please start it manually:"
        if [ -n "$PG_VERSION" ]; then
            echo "  brew services start postgresql@$PG_VERSION"
        fi
        exit 1
    fi
fi

echo "✓ PostgreSQL is running"
echo ""

# Set database credentials
DB_NAME="humanizer"
DB_USER="humanizer"
DB_PASSWORD="humanizer"
DB_HOST="localhost"
DB_PORT="5432"

echo "Creating database and user..."

# Create user and database (run as postgres superuser)
psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "User already exists"
psql postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || echo "Database already exists"

# Grant privileges
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo ""
echo "Installing pgvector extension..."

# Install pgvector extension (requires superuser)
psql -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo ""
echo "Running schema migrations..."

# Run schema creation
psql -d $DB_NAME -U $DB_USER -f database/schema.sql

echo ""
echo "✅ Database setup complete!"
echo ""

# Show PostgreSQL version
PG_VERSION_INFO=$(psql -V)
echo "PostgreSQL version: $PG_VERSION_INFO"
echo ""

echo "Connection details:"
echo "  Database: $DB_NAME"
echo "  User:     $DB_USER"
echo "  Host:     $DB_HOST"
echo "  Port:     $DB_PORT"
echo ""
echo "Connection string:"
echo "  postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "Update your .env file with:"
echo "  DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "To verify pgvector installation:"
echo "  psql -d humanizer -c \"SELECT * FROM pg_extension WHERE extname = 'vector';\""
echo ""
