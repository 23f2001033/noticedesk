FROM node:24-slim AS webapp-build

WORKDIR /webapp
COPY webapp/package.json webapp/package-lock.json ./
RUN npm ci
COPY webapp ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /srv

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir .

COPY --from=webapp-build /webapp/dist ./webapp/dist

# Cloud Run injects PORT; default matches app/config.py for local `docker run`.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
