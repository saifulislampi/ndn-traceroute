FROM nfd-base

RUN apt-get install -Uy --no-install-recommends \
        cmake sudo \
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

RUN cp /etc/ndn/nfd.conf.sample /etc/ndn/nfd.conf

ENTRYPOINT ["sh", "-c"]
CMD ["/bin/nfd-start; while ! /bin/nfd-status > /dev/null 2> /dev/null; do :; done"]
