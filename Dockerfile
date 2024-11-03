FROM nfd-base

COPY build/producer/simple-producer /simple-producer
COPY build/client/traceroute-client /traceroute-client

ENTRYPOINT ["sh", "-c"]
CMD ["/usr/bin/nfd --config /config/nfd.conf"]

