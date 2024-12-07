#!/bin/bash

# Pre-set the database connection details
export DB_HOST="your_host_here"
export DB_PORT="your_port_here"
export DB_NAME="your_db_name_here"
export DB_USER="your_username_here"
export DB_PASSWORD="your_password_here"

# Optionally, print the environment variables to verify
echo "Environment variables have been set."
echo "DB_HOST=$DB_HOST"
echo "DB_PORT=$DB_PORT"
echo "DB_NAME=$DB_NAME"
echo "DB_USER=$DB_USER"
# Don't print the password for security reasons
