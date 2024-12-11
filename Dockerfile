FROM nfd-build

RUN apt-get update && apt-get install -Uy --no-install-recommends \
        build-essential cmake sudo \
    && apt-get distclean

COPY producer /producer
RUN <<EOF
    mkdir /producer/build
    cd /producer/build
    cmake ..
    make
EOF

COPY client /client
RUN <<EOF
    mkdir /client/build
    cd /client/build
    cmake ..
    make
EOF

# Copy the start script
COPY utils/start-nfd.sh /start-nfd.sh
RUN chmod +x /start-nfd.sh

VOLUME /etc/ndn/nfd.conf

CMD ["sh", "-c", "/start-nfd.sh; tail -f /dev/null"]
