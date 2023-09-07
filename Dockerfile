# Python Base Image from https://hub.docker.com/r/arm32v7/python/
FROM arm32v7/python:3.11.2-alpine

# Copy the Python Script to blink LED
COPY main.py ./
COPY wiringOP-Python ./

# Install wiringOP-Python
RUN python3 wiringOP-Python/generate-bindings.py > wiringOP-Python/bindings.i
RUN sudo python3 wiringOP-Python/setup.py install

# Trigger Python script
CMD ["python", "./main.py"]