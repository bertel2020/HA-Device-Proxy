ARG BUILD_FROM

# gensio and ser2net from their release tarballs: Alpine ships gensio 2.8, and remaddr with
# networks (e.g. 192.168.0.0/16) needs gensio 3.0.3 or later
FROM ${BUILD_FROM} AS build
ARG GENSIO_VERSION=3.0.4
ARG GENSIO_SHA256=e28c24fc5d9f3cb90005bc008fec8bb8eedce503753024ab650bed0ac250cbe3
ARG SER2NET_VERSION=4.6.8
ARG SER2NET_SHA256=e651adcc4cc0d0ceaa36e5997dab9ea7f8aea732b4c87ba6018d2dcc88fbe8e3
RUN apk add --no-cache build-base linux-headers yaml-dev openssl-dev
WORKDIR /src
RUN wget -q "https://github.com/cminyard/gensio/releases/download/v${GENSIO_VERSION}/gensio-${GENSIO_VERSION}.tar.gz" \
    && echo "${GENSIO_SHA256}  gensio-${GENSIO_VERSION}.tar.gz" | sha256sum -c - \
    && tar xzf "gensio-${GENSIO_VERSION}.tar.gz" \
    && cd "gensio-${GENSIO_VERSION}" \
    && ./configure --prefix=/usr --sysconfdir=/etc --disable-static \
        --with-python=no --with-swig=no --with-go=no --with-tcl=no --with-glib=no \
        --with-cplusplus=no --with-openipmi=no --with-sound=no --with-alsa=no \
        --with-portaudio=no --with-udev=no --with-mdns=no --with-avahi=no \
        --with-uucp-locking=no \
    && make -j"$(nproc)" \
    && make install \
    && make install DESTDIR=/out
RUN wget -q "https://github.com/cminyard/ser2net/releases/download/v${SER2NET_VERSION}/ser2net-${SER2NET_VERSION}.tar.gz" \
    && echo "${SER2NET_SHA256}  ser2net-${SER2NET_VERSION}.tar.gz" | sha256sum -c - \
    && tar xzf "ser2net-${SER2NET_VERSION}.tar.gz" \
    && cd "ser2net-${SER2NET_VERSION}" \
    && ./configure --prefix=/usr --sysconfdir=/etc --with-pam=no \
    && make -j"$(nproc)" \
    && make install DESTDIR=/out \
    && rm -rf /out/usr/include /out/usr/share/man /out/usr/lib/*.la /out/usr/lib/pkgconfig
# Python packages as wheels here, where a compiler is: no prebuilt ones may exist for this
# Python on Alpine
COPY requirements.txt /src/requirements.txt
RUN pip3 wheel --no-cache-dir --require-hashes --wheel-dir /wheels -r /src/requirements.txt

FROM ${BUILD_FROM}
ARG BUILD_VERSION
ENV APP_VERSION=${BUILD_VERSION}

RUN apk add --no-cache yaml libssl3 libcrypto3
COPY --from=build /out/ /
RUN ser2net -v

COPY --from=build /wheels /tmp/wheels
RUN pip3 install --no-cache-dir --no-index /tmp/wheels/*.whl && rm -rf /tmp/wheels

COPY app /app
WORKDIR /app
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD ["python3", "-m", "device_proxy.health"]
# the base image starts this through s6-overlay, which leaves out the container's environment
# (SUPERVISOR_TOKEN, APP_VERSION) unless asked
CMD ["/command/with-contenv", "python3", "-m", "device_proxy"]
