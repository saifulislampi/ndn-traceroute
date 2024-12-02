#!/bin/sh

/usr/bin/nfd --config /etc/ndn/nfd.conf &
sleep 1
exec "$@"

