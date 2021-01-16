#!/bin/sh

if [ ! -f /etc/ssl/private/key.pem ]; then
    echo "Generating new certificates..."
    openssl req -x509 -nodes -newkey rsa:4096 -keyout /etc/ssl/private/key.pem -out /etc/ssl/private/cert.pem -days 3650 -subj '/CN=example.com'
fi
