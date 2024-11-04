FROM ghcr.io/named-data/nfd-build:latest AS build

RUN apt-get install -Uy --no-install-recommends \
        cmake \
    && apt-get distclean

RUN --mount=type=bind,source=client,target=/tmp/client,rw <<EOF
    mkdir /tmp/client/build
    cd /tmp/client/build
    cmake ..
    make
    cp traceroute-client /
EOF

RUN --mount=type=bind,source=producer,target=/tmp/producer,rw <<EOF
    mkdir /tmp/producer/build
    cd /tmp/producer/build
    cmake ..
    make
    cp simple-producer /
EOF

RUN mkdir /config
RUN cp /etc/ndn/nfd.conf.sample /config/nfd.conf

ENTRYPOINT ["sh", "-c"]
CMD ["/usr/bin/nfd --config /config/nfd.conf"]

