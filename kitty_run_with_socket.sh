#!/bin/sh

PID=$$
FILE="/tmp/.kitty_sock.$PID"
kitty --listen-on="unix:$FILE" "$@"