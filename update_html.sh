#!/bin/bash

# Get the current timestamp
timestamp=$(date +%s)

# Replace the placeholder in the HTML file with the current timestamp
sed -i "s/version=[0-9]\+/version=$timestamp/g" /var/www/stats/index.html
