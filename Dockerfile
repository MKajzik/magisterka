# Python Base Image from https://hub.docker.com/r/arm32v7/python/
FROM arm64v8/python:3.11.2-alpine

WORKDIR /magisterka

# Copy the Python Script to blink LED
COPY main.py .
COPY ./wiringOP-Python ./wiringOP-Python

#RUN apk add swig python3-dev python3-setuptools

# Install wiringOP-Python
RUN python3 generate-bindings.py > bindings.i
RUN sudo python3 setup.py install

# Trigger Python script
WORKDIR /
CMD ["python3", "./main.py"]