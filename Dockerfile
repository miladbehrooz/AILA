FROM apache/airflow:2.10.3

USER airflow

# install poetry
RUN pip install poetry

# set poetry to install into system environment
RUN poetry config virtualenvs.create false

# copy entire project
WORKDIR /opt/airflow
COPY . .

# install dependencies
RUN poetry install --no-root --no-interaction --no-ansi

USER root

# install git
RUN apt-get update && apt-get install -y git