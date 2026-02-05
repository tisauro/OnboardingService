#
FROM python:3.12-slim-bookworm AS base

RUN apt-get -y update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y \
            --no-install-recommends install python3-dev build-essential pkg-config libpq-dev && \
    apt-get -y autoremove && \
    apt-get -y clean

#
WORKDIR /project
COPY ./pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir --upgrade .

COPY ./app ./app

# use this target to run tests inside the docker container
FROM base AS tests
COPY ./pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir --upgrade  ".[dev]"
COPY ./tests ./tests

RUN --mount=type=secret,id=database,target=/project/.env pytest /project/tests --junitxml=./repos/tests.xml

# use this target to run tests inside the docker container and export output to the out folder on the host
FROM scratch AS test_reports
COPY --from=tests /project/repos/tests.xml tests.xml

FROM base AS final
# Expose the port on which the application will run
EXPOSE 8080

## Run the FastAPI application using uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]