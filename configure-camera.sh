#! /bin/sh

#
# Configure the USB camera
#

# Fix power line frequency
uvcdynctrl -v -d video0 --set='Power Line Frequency' 1

# Disable autofocus
uvcdynctrl -v -d video0 --set='Focus, Auto' 0

# Fix the focus
uvcdynctrl -v -d video0 --set='Focus (absolute)' 0

