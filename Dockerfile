FROM ety001/py-bts:latest
WORKDIR /app
COPY bots.py /app
CMD ["python3", "-u", "/app/bots.py"]
