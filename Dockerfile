FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --gid 10001 sanom \
    && useradd --uid 10001 --gid sanom --create-home --shell /usr/sbin/nologin sanom

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
RUN mkdir -p /app/_runtime /app/_review /app/_support \
    && chown -R sanom:sanom /app

USER sanom

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=5 \
  CMD python dashboard_server.py --check-only || exit 1

CMD ["python", "run_private_server.py", "--host", "0.0.0.0", "--port", "8080"]
