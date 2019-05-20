FROM ety001/py-bts:latest
WORKDIR /app
COPY bots.py /app
CMD ["/app/bots.py"]
