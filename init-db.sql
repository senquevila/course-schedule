-- Create the course_schedule database
CREATE DATABASE course_schedule;

-- Create the course_schedule_user
CREATE USER course_schedule_user WITH PASSWORD 'course_schedule_password';

-- Grant privileges
ALTER USER course_schedule_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE course_schedule TO course_schedule_user;
