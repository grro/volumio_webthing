FROM python:3.10.1-alpine3.15

ENV port 8080
ENV mailserver_port 2525
ENV to_pattern ".*@.*"


LABEL org.label-schema.schema-version="1.0" \
      org.label-schema.name="Volumio" \
      org.label-schema.description="Web connected volumio" \
      org.label-schema.url="https://github.com/grro/volumio_webthing" \
      org.label-schema.docker.cmd="docker run -p 8080:8080 -p 2525:2525 grro/volumio"

ADD . /tmp/
WORKDIR /tmp/
RUN  python /tmp/setup.py install
WORKDIR /
RUN rm -r /tmp/

CMD volumio --command listen --port $port --volumio_port $volumio_port
