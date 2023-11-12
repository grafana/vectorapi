# syntax=docker/dockerfile:1.4
### Runtime base image ###
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime AS runtime-base

# add htop for monitoring
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt \
  apt update \
  && apt install --no-install-recommends -y htop \ 
  && rm -rf /var/lib/apt/lists/*

# pin the version of poetry we install
ENV POETRY_VERSION=1.6.1 \
  # make poetry install to this location so we can add it to PATH
  POETRY_HOME="/opt/.poetry" \
  # set cache folder
  XDG_CACHE_HOME="/opt/.cache" \
  # don't show message for pip updates
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  # install poetry deps in the .venv folder so we can easily copy it in multi-stage build
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  # set cache directory to a fixed directory
  XDG_CACHE_HOME="/opt/.cache" \
  # this is where our requirements + virtual environment will live
  APP_PATH="/app" \
  VENV_PATH="/app/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
WORKDIR $APP_PATH

#### Builder image with poetry and build dependencies ####
FROM runtime-base as builder

# we need curl to get the poetry install script
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt \
  apt update \
  && apt install --no-install-recommends -y curl build-essential

# install poetry in a vendorised way so its dependencies are isolated and don't clash with our project
# pin install-poetry script to specific commit instead of master branch for security + reproducibility (script can't change under our feet)
RUN --mount=type=cache,target=$XDG_CACHE_HOME/pip \
  curl -sSL https://raw.githubusercontent.com/python-poetry/install.python-poetry.org/fcd759d6feb9142736a19f8a753be975a120be87/install-poetry.py | python

#### Install dependencies ####
FROM builder AS builder-with-deps
COPY --link ./pyproject.toml ./poetry.lock ./
RUN --mount=type=cache,target=${XDG_CACHE_HOME}/pypoetry/cache \
  --mount=type=cache,target=${XDG_CACHE_HOME}/pypoetry/artifacts \
  poetry install --no-root --only main

FROM builder-with-deps AS builder-with-dev-deps
# install dev-dependencies
RUN --mount=type=cache,target=${XDG_CACHE_HOME}/pypoetry/cache \
  --mount=type=cache,target=${XDG_CACHE_HOME}/pypoetry/artifacts \
  poetry install --no-root

#### Final runtime images ####
FROM runtime-base AS runtime

# store sentence_transformers in mounted path to avoid-redownloading
RUN mkdir -p ${APP_PATH}/.sentence_transformers
ENV SENTENCE_TRANSFORMERS_HOME=${APP_PATH}/.sentence_transformers
RUN mkdir -p ${APP_PATH}/.tiktoken
ENV TIKTOKEN_CACHE_DIR=${APP_PATH}/.tiktoken

ENV MODULE_NAME="vectorapi.main"

FROM runtime AS development
COPY --link --from=builder-with-dev-deps $POETRY_HOME $POETRY_HOME
COPY --link --from=builder-with-dev-deps $VENV_PATH $VENV_PATH

# copy code in final step (unfortunately duplicated between prod/dev) for improved caching
COPY --link . .
CMD ["/bin/bash", "-c", "uvicorn ${MODULE_NAME}:app --host ${HOST:-0.0.0.0} --port ${PORT:-80} --reload --log-level ${LOGLEVEL:-trace}"]

FROM runtime AS production
COPY --link --from=builder-with-deps $VENV_PATH $VENV_PATH

COPY --link . .
CMD ["/bin/bash", "-c", "uvicorn ${MODULE_NAME}:app --host ${HOST:-0.0.0.0} --port ${PORT:-80} --log-level ${LOGLEVEL:-debug}"]
