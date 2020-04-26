# MSPT Backup Migration - Docker
## Purpose
Provide a documented environment that provides consistency in running the migration utility across unknown heterogeneous systems.

## Assumptions
Reference [`Assumptions` in README.md](README.md#Assumptions)

Additionally, familiarity with Docker and the permissions to create an image and run a container on the host system.

## Requirements
Reference [`Requirements` in README.md](README.md#Requirements)

## Running
This can be run as an ephemeral container, or interactively from within the container. For simplicity and visibility to logging, these instructions will __only__ include the steps needed to run interactively.

## Invocation
1. Follow steps 1-2 from [`Invocation` in README.md](README.md#Invocation)

2. Create the Docker image
```bash
$ > docker build -t mspt-backup-migration:v1.1.0 .
```
3. Run the container
The container can be run with simply by
```bash
$ > docker run --rm \
    -it mspt-backup-migration:v1.1.0 \
    /bin/bash
```
For simplicity, the operator may choose to mount the an ssh key and/or a volume for writing logs to - at the users discretion. Following this method
```bash
$ > docker run --rm \
    -v ~/.ssh/id_rsa:/root/.ssh/id_rsa \
    -v /tmp/hsdp_logs:/usr/src/app/log/ \
    -v /tmp/hsdp_runtime:/usr/src/app/runtime/ \
    -it mspt-backup-migration:v1.1.0 \
    /bin/bash
```

4. Follow steps 4-5 from [`Invocation` in README.md](README.md#Invocation)
