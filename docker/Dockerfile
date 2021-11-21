FROM alpine:3.9

ENV CONTAINER_USER=nobody \
    CONTAINER_GROUP=nobody

COPY app/app.py /src/app.py
COPY app/queryfilter.py /src/queryfilter.py
COPY docker/entrypoint.sh /entrypoint.sh

RUN apk add --no-cache \
        bash \
        python3 \
        curl \
        gcc \
        build-base \
        python3-dev \
        linux-headers

RUN python3 -m ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /usr/lib/python*/ensurepip /root/.cache && \
    pip install json2html requests watchdog psutil && \
    chown -R ${CONTAINER_USER}:${CONTAINER_GROUP} /src/ /entrypoint.sh && \
    chmod +x /entrypoint.sh

WORKDIR /src

USER ${CONTAINER_USER}:${CONTAINER_GROUP}

ENTRYPOINT ["/entrypoint.sh"]

CMD ["publisher"]
