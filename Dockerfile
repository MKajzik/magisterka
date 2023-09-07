# Python Base Image from https://hub.docker.com/r/arm32v7/python/
FROM arm64v8/python:3.11.2-alpine

# Copy the Python Script to blink LED
ADD . /usr/local/

#RUN apk add swig python3-dev python3-setuptools

# Install wiringOP-Python
WORKDIR /usr/local/wiringOP-Python
RUN python3 generate-bindings.py > bindings.i
RUN sudo python3 setup.py install

# Trigger Python script
WORKDIR /
CMD ["python3", "./main.py"]