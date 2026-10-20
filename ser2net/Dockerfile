ARG BUILD_FROM
FROM ${BUILD_FROM}
ARG BUILD_VERSION
ENV APP_VERSION=${BUILD_VERSION}

RUN apk add --no-cache ser2net

COPY app /app
WORKDIR /app
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD ["python3", "-m", "ser2net_app.health"]
CMD ["python3", "-m", "ser2net_app"]
