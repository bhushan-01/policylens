# PolicyLens Gradio UI — deployable container
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt pyproject.toml README.md ./
COPY policylens ./policylens
COPY data ./data
COPY examples ./examples
COPY web ./web

RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install -e . --no-deps

EXPOSE 7860
ENV GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

CMD ["python", "-m", "policylens.ui"]
