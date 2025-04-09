# mashwrapper

[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A521.10.3-23aa62.svg?labelColor=000000)](https://www.nextflow.io/)
[![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/)
[![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/)
[![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)

## Introduction

**mashwrapper** is a wrapper around the program [Mash](https://mash.readthedocs.io/en/latest/) and the [NCBI Datasets command line tools](https://www.ncbi.nlm.nih.gov/datasets/docs/v1/download-and-install/). It identifies the most likely species from a pair of gzipped FASTQ reads using a Mash database. 

You can provide the database for comparison in two ways:
1. Generate it from a text file using the `--get_database` option.
2. Supplying an already built database using the `--use_database` option.

The tool outputs a text file containing the top five matches from the Mash database for the input reads. This output includes standard Mash results, and the best species match is determined by a cutoff based on the Mash distance score. For Legionella, this cutoff is conservatively set to a Mash distance of < 0.05. If you're using the tool for a different species, you should adjust this cutoff value based on what is most appropriate for your organism.

The pipeline is built using [Nextflow](https://www.nextflow.io), a workflow tool to run tasks across multiple compute infrastructures in a very portable manner. It uses Docker/Singularity containers making installation trivial and results highly reproducible. The [Nextflow DSL2](https://www.nextflow.io/docs/latest/dsl2.html) implementation of this pipeline uses one container per process which makes it much easier to maintain and update software dependencies. 

## Pipeline summary

1. Confirm input sample sheet: Use `--get_database` or `--use_database`
2. Confirm input organism sheet: `--get_database` (OPTIONAL)
3. Download genomes from NCBI using [NCBI datasets command line tool](https://www.ncbi.nlm.nih.gov/datasets/): `--get_database` (OPTIONAL)
4. Format downloaded genomes to be Genus_Species_GenebankIdentifier.fna using [NCBI dataformat command line tool](https://www.ncbi.nlm.nih.gov/datasets/docs/v1/quickstarts/command-line-tools/#install-using-curl): `--get_database` (OPTIONAL)
5. Build individual [Mash sketches](https://mash.readthedocs.io/en/latest/) for all genomes downloaded: `--get_database` (OPTIONAL)
6. Build [Mash database](https://mash.readthedocs.io/en/latest/) for all Mash sketches: `--get_database` (OPTIONAL)
7. Test fastq.gz reads against either an optionally built Mash database or one provided by the user: `--get_database` or `--use_database`
8. Collate results from each isolate of interest tested against the Mash database: `--get_database` or `--use_database`

## Quick Start

1. Install [`Nextflow`](https://www.nextflow.io/docs/latest/getstarted.html#installation) (`>=21.10.3`)

2. Install any of [`Docker`](https://docs.docker.com/engine/installation/), [`Singularity`](https://www.sylabs.io/guides/3.0/user-guide/), [`Podman`](https://podman.io/), [`Shifter`](https://nersc.gitlab.io/development/shifter/how-to-use/) or [`Charliecloud`](https://hpc.github.io/charliecloud/) for full pipeline reproducibility _(please only use [`Conda`](https://conda.io/miniconda.html) as a last resort; see [docs](https://nf-co.re/usage/configuration#basic-configuration-profiles))_

3. Clone the pipeline and test it on a minimal dataset:

 >  A test dataset is available once you git clone this repo and includes the following [files](https://github.com/jennahamlin/mashwrapper/tree/main/test-data):
 > - inputDB.txt - text file of species to download when using the test profile (-profile testGet). The file does  not include a header
 > - inputReads.csv - CSV file listing pairs of reads and includes the following header: sample,fastq_1,fastq_2
 > - myMashDatabase.msh - prebuilt Mash database using the same isolates listed in the inputDB.txt file. This file will be used if testUse option is indicated (-profile testUse)
 > - subERR125190_(1,2).fastq.gz - subset reads of *Legionella fallonii* to only 45000 reads
 > - subERR351242_(1,2).fastq.gz - subset reads of *Legionella pneumophila* to only 45000 reads
 > - subSRR10019387_(1,2).fastq.gz - subset reads of *Legionella longbeachae* to only 45000 reads

*You will likely need to adjust the [nfcore_custom.config](https://github.com/CDCgov/mashwrapper/blob/main/conf/nfcore_custom.config) file to work on your compute infrastructure. You can specify its use by pointing to the directory where that file is located with the `--custom_config_base` flag, which should point to the "conf" directory (i.e., ~/mashwrapper/conf).*

   ```console
    ## Use git to donwload/clone the repository 
    git clone https://github.com/CDCgov/mashwrapper.git

    ## Test out download of database, where YOURPROFILE could be singularity/docker/conda
    nextflow run mashwrapper -profile testGet,YOURPROFILE
    
    ## Test out using pre-built database, where YOURPROFILE could be singularity/docker/conda
    nextflow run mashwrapper -profile testUse,YOURPROFILE 
   ```
   
4. Start running your analysis!

  ```console
   ## Download and build your database for organism(s) of interest
   nextflow run nf-core/mashwrapper -profile <docker/singularity/conda> --input samplesheet.csv --get_database organismsheet.txt --custom_config_base ~/mashwrapper/conf

  ## Use your already built database
   nextflow run nf-core/mashwrapper -profile <docker/singularity/conda> --input samplesheet.csv --use_database myMashDatabase.msh --custom_config_base ~/mashwrapper/conf
  ```

## Documentation

The nf-core/mashwrapper pipeline comes with documentation about the pipeline [usage and parameters](https://github.com/CDCgov/mashwrapper/blob/main/docs/usage.md) and [output](https://github.com/CDCgov/mashwrapper/blob/main/docs/output.md).

## Credits

mashwrapper was originally written by Jenna Hamlin and is based heavily on previous work developed by Jason Caravas.

We thank the following people for their extensive assistance in the development of this pipeline:

- Sateeshe Peri
- Micheal Cipriano

## Contributions and Support

If you would like to contribute to this pipeline, please file an [Issue](https://github.com/CDCgov/mashwrapper/issues)
