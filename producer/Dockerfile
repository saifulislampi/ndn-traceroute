FROM nfd-base

COPY build/producer/simple-producer /simple-producer
COPY producer/startup.sh /startup.sh
COPY --link --from=nfd-base /etc/ndn/nfd.conf.sample /config/nfd.conf

ENV SOCK_NAME=producer

RUN chmod 755 /startup.sh

CMD ["sh", "-c", "/startup.sh ${SOCK_NAME}"]

