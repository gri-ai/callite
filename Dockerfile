FROM python:3.10.13-slim

LABEL authors="handy.codes"


WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

ENV POETRY_VERSION=1.1.12
ENV POETRY_VENV=/opt/poetry-venv

# Install poetry separated from system interpreter
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install --upgrade pip \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}



# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

RUN poetry add pydevd-pycharm~=233.14475.28
RUN poetry install

ENTRYPOINT ["poetry", "run"]
