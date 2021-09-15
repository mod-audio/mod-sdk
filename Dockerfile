FROM debian:stable

RUN apt-get update -qq && \
    apt-get install -y build-essential liblilv-dev phantomjs && \
    apt-get install -y python3-pil python3-pystache python3-tornado python3-pyinotify python3-setuptools

ENV LV2_PATH="/lv2"

RUN mkdir /modsdk

COPY ./ /modsdk/

WORKDIR /modsdk

RUN python3 setup.py build

EXPOSE 9000

VOLUME ["/lv2"]

CMD ./development_server.py
