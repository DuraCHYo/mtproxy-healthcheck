FROM python:3.14.3-slim-trixie

WORKDIR /app

RUN python3 -m venv ./venv
ENV PATH="/app/venv/bin:$PATH"

COPY requirements.txt requirements.txt

COPY src ./src

RUN pip install -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["python3", "src/main.py"]