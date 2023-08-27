FROM python:3.9.12-slim-bullseye as base

FROM base as builder
COPY requirements.txt .
RUN pip install --prefix="/install" -r requirements.txt

FROM base
COPY --from=builder /install /usr/local
WORKDIR /app
COPY run.sh .
COPY locustfile.py .
RUN chmod 755 run.sh

EXPOSE 5557 5558 8089

# Start Locust using LOCUS_OPTS environment variable
ENTRYPOINT ["/app/run.sh"]
