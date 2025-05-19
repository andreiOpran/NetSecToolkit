FROM python:3.12

RUN pip install scapy

WORKDIR /app
# CMD ["tail", "-f", "/dev/null"] # porneste dockerul cu un entrypoint care nu face nimic (debug)
CMD ["python3", "dns_server.py"]