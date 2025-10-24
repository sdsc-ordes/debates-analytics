# debates-dataloader

## About

The dataloader serves as backend for the [debates-app](https://github.com/sdsc-ordes/debates-app). See there for a more detailed documentation.

Dataloader for media transcriptions

## Install

The package management is done with [rye](https://rye.astral.sh/)

```
git clone git@github.com:sdsc-ordes/debates-dataloader.git
cd debates-dataloader
rye install
rye sync
source .venv/bin/activate
```

## Environment Variables

See `env.dist` for a description of the environment variables

## Use

The dataloader includes the following parts:

- cli commands to manage S3, Solr and MongoDB
- fastapi route to serve media urls from S3


### Start Fast API Server

```
python src/debates.py serve
```

### CLI Commands

```
python src/debates.py --help
```
