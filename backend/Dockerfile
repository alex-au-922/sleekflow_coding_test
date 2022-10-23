FROM python:3.10.6-bullseye

ENV HOME=/app
WORKDIR ${HOME}

RUN mkdir -p utils config data_models routes

COPY requirements.txt .
COPY main.py .
COPY routes ./routes
COPY data_models ./data_models
COPY util ./util
COPY config ./config

ARG BACKEND_HOST
ENV BACKEND_HOST=$BACKEND_HOST

ARG BACKEND_PORT
ENV BACKEND_PORT=$BACKEND_PORT

ARG ROJECT_MODE
ENV PROJECT_MODE=$PROJECT_MODE

RUN pip install -r requirements.txt

EXPOSE ${BACKEND_PORT}

CMD ["python", "main.py"]