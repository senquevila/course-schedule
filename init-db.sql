-- Create the coursecal database
CREATE DATABASE coursecal;

-- Create the coursecal_user
CREATE USER coursecal_user WITH PASSWORD 'coursecal_password';

-- Grant privileges
ALTER USER coursecal_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE coursecal TO coursecal_user;
