FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ server/

ENV PORT=8000
ENV EXCEL_PATH=/data/Migration_INEKTO_V2_2_ENRICHI.xlsx

EXPOSE ${PORT}

CMD ["python", "-m", "server.server", "--transport", "http"]
