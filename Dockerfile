FROM python:3

RUN apt-get update && apt-get install -y protobuf-compiler

RUN git clone https://github.com/NoMore201/googleplay-api.git

RUN cd googleplay-api && python3 setup.py install

ADD download_apks.py /src/
ADD run.sh /src/
ADD get_creds.sh /src/


