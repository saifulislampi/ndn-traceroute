FROM nfd-base

COPY build/client/traceroute-client /traceroute-client
COPY client/startup.sh /startup.sh

VOLUME /config

ENV NAME=/example/test
ENV HOP_LIMIT=30

RUN chmod 755 /startup.sh
CMD ["sh", "-c", "/startup.sh ${NAME} ${HOP_LIMIT}"]

