# nf-core/mashwrapper: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v3.2.3

Altered mechanism to excluded uncultured Legionella species genomes

## v3.2.2
Added information as internally required by the [ShareIT-Act](https://github.com/CDCgov/ShareIT-Act)

## v3.2.1
NCBI command line tools version change from 15.2.0 -> 18.2.0
* Had to change assminfo-paired-assmaccession to assminfo-paired-assm-accession

## v3.1.0
NCBI command line tools version change from 15.2.0 -> 18.2.0
* After attempting to download genomes for Lp, could not successfully download all. Issues on NCBI datasets suggested newer versions dealt with larger download easier.

## v3.0.0
downloadGenome.sh
* uses dataformat function for better parsing rather than awk

run_species_id.py:
* better error out if there are no reads associated with a pair of reads
* additionally refactoring to remove redundancy

## v2.0.0  - 11/19/2024

Fixed the print on K-mer size in the result file.

## v2.0 - 11/12/2024

General refactoring of code. 

## v1.0dev - [date]

Initial release of mashwrapper, created with the [nf-core](https://nf-co.re/) template.

