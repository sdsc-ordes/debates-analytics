<p align="center">
  <img src="./components/docs/assets/political_debates_logo.svg" alt="debates logo" width="250">
</p>

<h1 align="center">
  Debates Analytics
</h1>
<p align="center">
</p>
<p align="center">
  <a href="https://github.com/sdsc-ordes/debates-analytics/releases/latest">
    <img src="https://img.shields.io/github/release/sdsc-ordes/debates-analytics.svg?style=for-the-badge" alt="Current Release label" /></a>
  <a href="http://www.apache.org/licenses/LICENSE-2.0.html">
    <img src="https://img.shields.io/badge/LICENSE-Apache2.0-ff69b4.svg?style=for-the-badge" alt="License label" /></a>
</p>

## About

This repository provides an app that is able to transcribe and translate
debates, where speakers take turns. Any such video or audio file in the format
`mp4` or `wav` can be uploaded via a dashboard for analysis.

- The analysis is performed with the hugging face component
  [odtp-pyannote-whisper](https://github.com/sdsc-ordes/odtp-pyannote-whisper),
  that was developed in the context of this project and can be accessed directly
  via
  [hugging face](https://huggingface.co/spaces/katospiegel/odtp-pyannote-whisper).

- The results of that analysis are loaded into an S3 compatible object store
  (garage).

- From there it will be indexed into the Search Engine Solr. A Mongo db database
  is used to manage the media processing results and status

- A dashboard is provided to make all processing and results available via a
  common interface: it consists of a frontend, a backend and a redis queue for a
  decoupled processing of the long running media analysis jobs on hugging face.

## Authors

- [Sabine Maennel](mailto:sabine.maennel@sdsc.ethz.ch)
- [Carlos Vivar Rios](mailto:carlos.vivarrios@epfl.ch)
- [Hannah Casey](mailto:hannah.casey@sdsc.ethz.ch)

## Installation

Installation and options for the installations are described in the
[documentation](https://sdsc-ordes.github.io/debates-analytics/install/options.html)

## Usage

Usage is described in the
[documentation](https://sdsc-ordes.github.io/debates-analytics/ui/ui.html)

## Development

See [documentation](https://sdsc-ordes.github.io/debates-analytics/index.html)

## Acknowledgement

This work was originally funded by the SNSF Spark Grant number 221139 “Debating
Human Rights”
[SNSF Data Portal . Documentation: Political Debates](https://data.snf.ch/grants/grant/221139).

The goal of that project was to create specialized components for the analysis
of videos from United Nations Human Rights Council (UNHRC) debates.

- Sophisticated Transcription: Integrating and optimizing cutting-edge
  transcription models (e.g., Whisper 3.0) to ensure accurate, multilingual
  transcription of UNHRC debates.
- Multimodal Data Handling: Developing components tailored to video/audio
  processing, scene extraction, and diarization.
- Specialized Database Integration: Designing and deploying a database structure
  to effectively store debate transcripts, relevant metadata, and extracted
  features.

This repo was created as a wrapup of that project, to make the processings and
results available in a more general form.

## Copyright

Copyright © 2025-2028 Swiss Data Science Center (SDSC),
[www.datascience.ch](http://www.datascience.ch/). All rights reserved. The SDSC
is jointly established and legally represented by the École Polytechnique
Fédérale de Lausanne (EPFL) and the Eidgenössische Technische Hochschule Zürich
(ETH Zürich). This copyright encompasses all materials, software, documentation,
and other content created and developed by the SDSC.
