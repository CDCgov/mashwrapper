# mashwrapper

[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A521.10.3-23aa62.svg?labelColor=000000)](https://www.nextflow.io/)
[![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/)
[![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/)
[![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)

Org: CDC/NCIRD/DBB/RDB/PSLB  
Contact Email: jhamlin@cdc.gov  
Exemption: None  
Status: Maintenance  


## Introduction

**mashwrapper** is a wrapper around the program [Mash](https://mash.readthedocs.io/en/latest/) and the [NCBI Datasets command line tools (CLI)](https://www.ncbi.nlm.nih.gov/datasets/docs/v1/download-and-install/). It identifies the most likely species from paired gzipped FASTQ reads using a Mash database. 

You can provide the database for comparison in two ways:
1. `--get_database`: Used when downloading and building a new Mash database from genomes
2. `--use_database`: Used when you're skipping the build step and instead providing a prebuilt Mash database

The tool outputs a text file containing the top five matches from the Mash database for the input reads. This output includes standard Mash results, and the best species match is determined by a cutoff based on the Mash distance score. For Legionella, this cutoff is conservatively set to a Mash distance of < 0.05. If you're using the tool for a different species, you should adjust this cutoff value based on what is most appropriate for your organism.

The pipeline is built using [Nextflow](https://www.nextflow.io), a workflow tool to run tasks across multiple compute infrastructures in a very portable manner. It uses Docker/Singularity containers, making installation trivial and results highly reproducible. 

## Pipeline summary

1. Confirm input sample sheet (`--get_database` or `--use_database`)
2. Confirm input organism sheet [optional] (`--get_database`)
3. Download genomes from NCBI using [NCBI datasets CLI](https://www.ncbi.nlm.nih.gov/datasets/) [optional] (`--get_database`)
4. Format downloaded genomes to be Genus_Species_GenebankIdentifier.fna using [NCBI dataformat CLI](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/command-line/dataformat/) [optional] (`--get_database`)
5. Build individual [Mash sketches](https://mash.readthedocs.io/en/latest/sketches.html) for all genomes [optional] (`--get_database`)
6. Build [Mash database](https://mash.readthedocs.io/en/latest/tutorials.html#pairwise-comparisons-with-compound-sketch-files) from all Mash sketches [optional] (`--get_database`)
7. Test FASTQ reads against a Mash database either built or provided (`--get_database` or `--use_database`)
8. Collate results from each isolate of interest tested against the Mash database (`--get_database` or `--use_database`)

## Quick Start

1. Install [`Nextflow`](https://www.nextflow.io/docs/latest/getstarted.html#installation) (`>=21.10.3`)

2. Install either [`Docker`](https://docs.docker.com/engine/installation/) or [`Singularity`](https://sylabs.io/docs/) to ensure full pipeline reproducibility with Nextflow. _[`Conda`](https://conda.io/miniconda.html) may be used as a last resort; see [docs](https://nf-co.re/usage/configuration#basic-configuration-profiles))_

3. Clone or download the pipeline and test it on a minimal dataset:

 >  This repository includes a test dataset with the following [files](https://github.com/jennahamlin/mashwrapper/tree/main/test-data):
 > - **inputDB.txt** - A plain text file of species to download when using the `-profile testGet` option. File does not include a header.
 > - **inputReads.csv** - A CSV file listing paired-end read files. It has the following header: sample,fastq_1,fastq_2
 > - **myMashDatabase.msh** - A prebuilt Mash database from isolates listed in inputDB.txt file and used with the `-profile testUse` option. 
 > - **subERR125190_(1,2).fastq.gz** - Subsampled reads (45,000 reads) from *Legionella fallonii* 
 > - **subERR351242_(1,2).fastq.gz** - Subsampled reads (45,000 reads) from *Legionella pneumophila*
 > - **subSRR10019387_(1,2).fastq.gz** - Subsampled reads (45,000 reads) from *Legionella longbeachae*

**Step-by-step example commands**

   ```console
    ## Step 1: Clone the repository
    git clone https://github.com/CDCgov/mashwrapper.git

    ## Step 2: Test downloading and building the databse
    ## "YOURPROFILE" is your preferred execution environment (Docker, Singularity or Conda)
    nextflow run mashwrapper -profile testGet,YOURPROFILE
    
    ## Step 3: Test using a prebuilt database
    ## "YOURPROFILE" is your preferred execution environment (Docker, Singularity or Conda)
    nextflow run mashwrapper -profile testUse,YOURPROFILE 
   ```
*You will likely need to adjust the [nfcore_custom.config](https://github.com/CDCgov/mashwrapper/blob/main/conf/nfcore_custom.config) file to work on your compute environment. To use it, specify the path to its directory using the `--custom_config_base` flag. This should point to the "conf" directory (i.e., ~/mashwrapper/conf).*

   
4. Start running your analysis!

  ```console
   ## Build a Mash database for organism(s) of interest
   nextflow run nf-core/mashwrapper -profile <Docker/Singularity/Conda> --input samplesheet.csv --get_database organismsheet.txt --custom_config_base ~/mashwrapper/conf

  ## Use a prebuilt Mash database
   nextflow run nf-core/mashwrapper -profile <Docker/Singularity/Conda> --input samplesheet.csv --use_database myMashDatabase.msh --custom_config_base ~/mashwrapper/conf
  ```

## Documentation

The nf-core/mashwrapper pipeline comes with documentation about the pipeline [usage and parameters](https://github.com/CDCgov/mashwrapper/blob/main/docs/usage.md) and [output](https://github.com/CDCgov/mashwrapper/blob/main/docs/output.md).

## Credits

mashwrapper is based heavily on previous work by [Jason Caravas](https://github.com/jacaravas) with the current version written by [Jenna Hamlin](https://github.com/jennahamlin). 

We thank the following people for their extensive assistance in the development of this pipeline:

- [Sateeshe Peri](https://github.com/sateeshperi)
- [Michael Cipriano](https://github.com/mciprianoCDC)

## Contributions and Support

If you would like to contribute to this pipeline, please file an [Issue](https://github.com/CDCgov/mashwrapper/issues)

## Repository Usage and Legal Notices
Please see the [notices page](https://github.com/CDCgov/mashwrapper/blob/main/docs/notices.md) for detailed information
