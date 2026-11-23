# syntax=docker/dockerfile:1

# Family Campus: Python server (standard library only) serves www/, handles
# login and stores progress in SQLite under /data (Docker volume).
# Build context (tools/campus-image.sh): server/server.py and VERSION of Family Campus, the site built
# from Family Campus and my-family in www/ (its build.json holds the date of the content, ADR-0018).
FROM python:3.13-alpine
LABEL org.opencontainers.image.title="Family Campus"
RUN adduser -D -H -u 10001 campus && mkdir -p /data && chown campus:campus /data
COPY server/server.py VERSION /app/
COPY www/ /srv/www/
USER campus
# URL path of the site (my-family's "prefix", e.g. /campus); what the image was built from
ARG FC_PREFIX=""
ARG APP_VERSION=""
ARG CONTENT_DATE=""
ARG COMMIT=""
LABEL family-campus.app-version=$APP_VERSION family-campus.content-date=$CONTENT_DATE family-campus.commit=$COMMIT
ENV CAMPUS_WWW=/srv/www CAMPUS_DATA=/data PORT=8080 PYTHONUNBUFFERED=1 FC_PREFIX=$FC_PREFIX
VOLUME /data
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO /dev/null http://127.0.0.1:8080/healthz || exit 1
CMD ["python3", "/app/server.py"]
