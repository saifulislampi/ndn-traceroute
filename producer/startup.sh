#!/bin/bash

sed -i "107s|nfd\\.sock|$1|" /config/nfd.conf

/usr/bin/nfd --config /config/nfd.conf > /dev/null 2> /dev/null &

while [ ! -e "/run/nfd/$1" ]
do
    :
done

/simple-producer "unix:///run/nfd/$1"
