FROM python:3.14.4-alpine

WORKDIR app/

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./src/ ./src/
COPY pyproject.toml .

# 8000 = app (public via Gateway), 9000 = metrics (scraped internally). Docs only.
EXPOSE 8000 9000

CMD ["fastapi", "run"]