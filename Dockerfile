FROM python:3.9.1-alpine

ENV volumio_base_uri "http://localhost:3000"


LABEL org.label-schema.schema-version="1.0" \
      org.label-schema.name="Volumio" \
      org.label-schema.description="Web connected volumio" \
      org.label-schema.url="https://github.com/grro/volumio_webthing" \
      org.label-schema.docker.cmd="docker run -p 8080:8080 -p 9090:9090 -e volumio_base_uri='http://localhost:3000' grro/volumio"

ADD . /tmp/
WORKDIR /tmp/
RUN  python /tmp/setup.py install
WORKDIR /
RUN rm -r /tmp/

CMD volumio_webthing --command listen --port 8080 --volumio_base_uri $volumio_base_uri --event_listener_port 9090
