-- PostgreSQL initialization script for Document Processing System

-- Create database if not exists (for reference, though docker will create it)
-- CREATE DATABASE IF NOT EXISTS docprocessing;

-- Enable extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance (will be created by SQLAlchemy too)
-- These will be created after tables exist via SQLAlchemy

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE docprocessing TO postgres;