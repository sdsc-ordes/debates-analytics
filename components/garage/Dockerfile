FROM dxflrs/garage:v2.0.0 AS garage-source

FROM alpine:edge

RUN apk update && \
    apk add --no-cache bash curl python3 py3-boto3

COPY --from=garage-source /garage /usr/bin/garage

COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY setup_cors.py /setup_cors.py
COPY garage.toml /etc/garage.toml

RUN chmod +x /docker-entrypoint.sh

RUN garage --version

ENV RUST_LOG=info
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["garage", "-c", "/etc/garage.toml", "server"]
