#!/bin/bash

# Start virtual display for development
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99

# Wait for X server to start
sleep 2

# Execute the main command
exec "$@"
