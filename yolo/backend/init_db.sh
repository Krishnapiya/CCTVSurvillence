#!/usr/bin/env bash
# Execute SQL script to create tables in surveillance_system database
psql postgresql://surveillance_user:password@localhost:5432/surveillance_system -f init_backend_tables.sql
