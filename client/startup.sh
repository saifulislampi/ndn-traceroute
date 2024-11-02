#!/bin/sh

# get socket name from config file
SOCK_PATH="$(sed -n '107p' /config/nfd.conf | sed 's|^[^/]*\([^ ]*\) .*$|\1|')"
trap "rm -f $SOCK_PATH" EXIT

# make SOCK_PATH the default socket
mkdir /root/.ndn
echo "transport=unix://$SOCK_PATH" > /root/.ndn/client.conf

# launch NFD
/usr/bin/nfd --config /config/nfd.conf > stdout.log 2> stderr.log &

# wait for socket to be created
while [ ! -e "$SOCK_PATH" ]
do
    sleep 1
done

# start client
NAME="$1"
HOP_LIMIT="$2"
/traceroute-client "unix://$SOCK_PATH" "$NAME" "$HOP_LIMIT"
