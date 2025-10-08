#!/bin/bash
# Create test database for backend API tests

set -e

DB_NAME="humanizer_test"
DB_USER="humanizer"
DB_HOST="localhost"
DB_PORT="5432"

echo "🔧 Creating test database: $DB_NAME"

# Check if database exists
DB_EXISTS=$(psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")

if [ "$DB_EXISTS" = "1" ]; then
    echo "⚠️  Database $DB_NAME already exists"
    read -p "Drop and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Dropping existing database..."
        psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d postgres -c "DROP DATABASE $DB_NAME;"
    else
        echo "✅ Using existing database"
        exit 0
    fi
fi

# Create database
echo "📦 Creating database $DB_NAME..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d postgres <<EOF
CREATE DATABASE $DB_NAME
    WITH
    OWNER = $DB_USER
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;
EOF

# Enable pgvector extension
echo "🔌 Enabling pgvector extension..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" <<EOF
CREATE EXTENSION IF NOT EXISTS vector;
EOF

echo "✅ Test database created successfully!"
echo ""
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Connection: postgresql://$DB_USER:***@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "📝 Next steps:"
echo "   1. Update conftest.py with: postgresql+asyncpg://$DB_USER:humanizer@$DB_HOST:$DB_PORT/$DB_NAME"
echo "   2. Run tests: pytest tests/api/ -v"
