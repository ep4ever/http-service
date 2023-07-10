#!/bin/sh

openssl req -newkey rsa:4096 -new -nodes -x509 -days 3650 -keyout server.key -out server.crt
