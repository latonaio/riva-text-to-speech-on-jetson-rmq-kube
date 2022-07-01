FROM ubuntu:22.04
RUN apt update && apt install -y python3 git gcc python3.10-venv python3-dev pip libportaudio2
RUN mkdir -p /app/src /app/mnt
COPY ["riva_quickstart_arm64_v2.1.0/riva_api-2.1.0-py3-none-any.whl", "requirements.txt", "/app/src"]
WORKDIR /app/src
RUN pip install -r requirements.txt
RUN rm -rf /app/src
CMD bash
