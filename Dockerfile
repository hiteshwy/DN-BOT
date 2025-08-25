FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y openssh-client tmate bash curl iproute2 procps && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Keep container alive
CMD ["sleep", "infinity"]
