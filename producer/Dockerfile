FROM nfd-base

COPY build/producer/simple-producer /simple-producer
COPY producer/startup.sh /startup.sh

VOLUME /config

RUN chmod 755 /startup.sh
CMD ["sh", "-c", "/startup.sh"]

