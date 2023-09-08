# Python Base Image from https://hub.docker.com/r/arm32v7/python/
FROM arm64v8/python:3.11.2

RUN apt-get update && apt-get install -y swig python3-dev python3-setuptools sudo

WORKDIR /magisterka

# Copy the Python Script to blink LED
COPY main.py .
COPY wiringOP-Python ./wiringOP-Python

#RUN apk add swig python3-dev python3-setuptools
WORKDIR /magisterka/wiringOP-Python
# Install wiringOP-Python
RUN python3 -m pip install setuptools
RUN python3 generate-bindings.py > bindings.i
RUN python3 -v -m setup.py install

# Trigger Python script
WORKDIR /
CMD ["python3", "./main.py"]
