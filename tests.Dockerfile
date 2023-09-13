# syntax=docker/dockerfile:1.4
FROM python:3.11-bullseye

ENV POETRY_VERSION=1.6.1 \
  # make poetry install to this location so we can add it to PATH
  POETRY_HOME="/opt/.poetry" \
  # set cache folder
  XDG_CACHE_HOME="/opt/.cache" \
  # don't show message for pip updates
  PIP_DISABLE_PIP_VERSION_CHECK=1

# install poetry in a vendorised way so its dependencies are isolated and don't clash with our project
RUN --mount=type=cache,target=${XDG_CACHE_HOME}/pip \
  curl -sSL https://install.python-poetry.org | python -

# set PATH so we can run poetry commands
ENV PATH="$POETRY_HOME/bin:$PATH"

# set poetry config to install to system instead of virtualenv
ENV POETRY_VIRTUALENVS_CREATE=false

# store sentence_transformers in mounted path to avoid-redownloading
RUN mkdir -p /app/.sentence_transformers
ENV SENTENCE_TRANSFORMERS_HOME=/app/.sentence_transformers
RUN mkdir -p /app/.tiktoken
ENV TIKTOKEN_CACHE_DIR=/app/.tiktoken

# Install dependencies
RUN --mount=type=cache,target=${XDG_CACHE_HOME}/pip \
  pip install -U pip setuptools wheel

COPY --link ./pyproject.toml ./poetry.lock ./
RUN --mount=type=cache,target=${XDG_CACHE_HOME}/pypoetry/cache \
  --mount=type=cache,target=${XDG_CACHE_HOME}/pypoetry/artifacts \
  poetry install --no-root

WORKDIR /app
COPY --link . .

ENV MODULE_NAME="vectorapi.main"
CMD ["pytest", "-m", "Integration"]
