# mashwrapper Parameters

```console
Input/output options
  --input                      [string]  Path to a CSV file with the following header: sample,fastq1.gz,fastq2.gz
  --outdir                     [string]  Path to the output directory where results will be saved [default: ./results]
  --email_addy                 [string]  Primary email address to send the results summary file
  --email_cc                   [string]  Email addresses to CC when sending results, comma-separated if multiple
  --email_subject              [string]  Custom subject line for the results email [default: Results from mashwrapper to identify species]

Database options
  --get_database               [string]  Path to a plain text file listing organisms to download from NCBI; one per line, as either "Genus" or "Genus species"  
                                          
  --use_database               [string]  Path to a prebuilt Mash database (.msh)
  --assembly_level             [string]  Restrict genomes downloaded to specific assembly levels: chromosome, complete, scaffold, contig; comma-separated 
                                         list 

Optional pipeline parameters
  --size_kmer                  [integer] Length of k-mers used in Mash sketches (1–32). Only applicable when downloading genomes or inferred from prebuilt 
                                         database [default: 25] 
  --max_dist                   [number]  Maximum Mash distance to consider for species identification [default: 0.05]
  --kmer_min                   [integer] Minimum k-mer copy number. Defaults to estimated coverage/3; override with a custom value ≥ 2 [default: 2]
  --num_threads                [integer] Number of threads to use for parallel processing [default: 2]

!! Hiding 18 params, use --show_hidden_params to show them !!
```

## Samplesheet input

You will need to create a samplesheet with information about the samples you would like to analyse before running the pipeline. Use this parameter to specify its location. It has to be a comma-separated file with 3 columns, and a header row as shown in the examples below.

```console
--input '[path to samplesheet file]'
```

### Multiple runs of the same sample

The `sample` identifiers have to be the same when you have re-sequenced the same sample more than once e.g. to increase sequencing depth. The pipeline will concatenate the raw reads before performing any downstream analysis. Below is an example for the same sample sequenced across 3 lanes:

```console
sample,fastq_1,fastq_2
CONTROL_REP1,AEG588A1_S1_L002_R1_001.fastq.gz,AEG588A1_S1_L002_R2_001.fastq.gz
CONTROL_REP1,AEG588A1_S1_L003_R1_001.fastq.gz,AEG588A1_S1_L003_R2_001.fastq.gz
CONTROL_REP1,AEG588A1_S1_L004_R1_001.fastq.gz,AEG588A1_S1_L004_R2_001.fastq.gz
```
*Note: While multiple runs of the same sample should work in theory, this functionality has not been explicitly tested with mashwrapper.*

| Column    | Description                                                                                                                                                                            |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sample`  | Custom sample name. This entry will be identical for multiple sequencing libraries/runs from the same sample. Spaces in sample names are automatically converted to underscores (`_`). |
| `fastq_1` | Full path to FastQ file for Illumina short reads 1. File has to be gzipped and have the extension ".fastq.gz" or ".fq.gz".                                                             |
| `fastq_2` | Full path to FastQ file for Illumina short reads 2. File has to be gzipped and have the extension ".fastq.gz" or ".fq.gz".                                                             |

An [example samplesheet](https://github.com/CDCgov/mashwrapper/blob/main/test-data/inputReads.csv) has been provided with the pipeline.

## Running the pipeline

The typical command for running the pipeline is as follows:

```console
nextflow run mashwrapper --input inputReads.csv --get_database inputDB.txt -profile Singularity
```

This will launch the pipeline with the `Singularity` configuration profile. See below for more information about profiles.

Note that the pipeline will create the following files in your working directory:

```console
work            # Directory containing the nextflow working files
results         # Finished results (configurable, see below)
.nextflow_log   # Log file from Nextflow
# Other nextflow hidden files, eg. history of pipeline runs and old logs.
```

### Reproducibility

It is a good idea to specify a pipeline version when running the pipeline on your data. This ensures that a specific version of the pipeline code and software are used when you run your pipeline. If you keep using the same tag, you'll be running the same version of the pipeline, even if there have been changes to the code since.

First, go to the [mashwrapper releases page](https://github.com/CDCgov/mashwrapper/releases) and find the latest version number - numeric only (eg. `3.2.2`). Then specify this when running the pipeline with `-r` (one hyphen) - eg. `-r 3.2.2`.

This version number will be logged in reports when you run the pipeline, so that you'll know what you used when you look back in the future.

## Core Nextflow arguments

> **NB:** These options are part of Nextflow and use a _single_ hyphen (pipeline parameters use a double-hyphen).

### `-profile`

Use this parameter to choose a configuration profile. Profiles can give configuration presets for different compute environments.

Several generic profiles are bundled with the pipeline which instruct the pipeline to use software packaged using different methods (Docker, Singularity, Conda) - see below. When using Biocontainers, most of these software packaging methods pull Docker containers from quay.io e.g [FastQC](https://quay.io/repository/biocontainers/fastqc) except for Singularity which directly downloads Singularity images via https hosted by the [Galaxy project](https://depot.galaxyproject.org/singularity/) and Conda which downloads and installs software locally from [Bioconda](https://bioconda.github.io/).

> We highly recommend the use of Docker or Singularity containers for full pipeline reproducibility, however when this is not possible, Conda is also supported.

Note that multiple profiles can be loaded, for example: `-profile test,docker` - the order of arguments is important!
They are loaded in sequence, so later profiles can overwrite earlier profiles.

If `-profile` is not specified, the pipeline will run locally and expect all software to be installed and available on the `PATH`. This is _not_ recommended.

- `docker`
  - A generic configuration profile to be used with [Docker](https://docker.com/)
- `singularity`
  - A generic configuration profile to be used with [Singularity](https://sylabs.io/docs/)
- `conda`
  - A generic configuration profile to be used with [Conda](https://conda.io/docs/). Please only use Conda as a last resort i.e. when it's not possible to run the pipeline with Docker, Singularity, Podman, Shifter or Charliecloud.
- `test`
  - A profile with a complete configuration for automated testing
  - Includes links to test data so needs no other parameters

### `-resume`

Specify this when restarting a pipeline. Nextflow will used cached results from any pipeline steps where the inputs are the same, continuing from where it got to previously.

You can also supply a run name to resume a specific run: `-resume [run-name]`. Use the `nextflow log` command to show previous run names.

### `-c`

Specify the path to a specific config file (this is a core Nextflow command). See the [nf-core website documentation](https://nf-co.re/usage/configuration) for more information.

## Custom configuration

### Resource requests
While the default resource requirements in the pipeline should work for most users and input data, you may need to customize the compute resources requested. Each step in the pipeline has default values for CPUs, memory, and time. For most steps, if a job exits with [certain error codes](https://github.com/CDCgov/mashwrapper/blob/8832c347c2805237655f2d8ba6ff0f0961c08098/conf/base.config#L18), it will automatically be resubmitted with increased resources (2× the original, then 3×). If it still fails after the third attempt, the pipeline execution will stop. 

To resolve these errors, you’ll need to identify which specific resources need adjustment. All module files in DSL2 pipelines are located in the modules/ directory. These contain a [Nextflow `label`](https://www.nextflow.io/docs/latest/process.html#label) directive near the top—set to [process_low, process_medium, or process_high](https://github.com/CDCgov/mashwrapper/blob/8832c347c2805237655f2d8ba6ff0f0961c08098/modules/local/combined_output.nf#L3). This directive allows processes to be grouped and referenced in a configuration file for resource customization.

Default values for the process_* labels are defined in [`base.config`](https://github.com/CDCgov/mashwrapper/blob/8832c347c2805237655f2d8ba6ff0f0961c08098/conf/base.config#L29). As long as you haven’t set other nf-core parameters that limit [maximum resource usage](https://nf-co.re/usage/configuration#max-resources), you can bypass failures by creating or updating a custom config file with adjusted memory settings. This config file can be supplied to the pipeline using the  [`-c`](#-c) parameter, as described in earlier sections.


 The default values for the `process_*` labels are set in the pipeline's [`base.config`](https://github.com/CDCgov/mashwrapper/blob/8832c347c2805237655f2d8ba6ff0f0961c08098/conf/base.config#L29). Providing you haven't set any other standard nf-core parameters to **cap** the [maximum resources](https://nf-co.re/usage/configuration#max-resources) used by the pipeline then we can try and bypass failures by creating or updating a custom config file with altered memory. The custom config below can then be provided to the pipeline via the [`-c`](#-c) parameter as highlighted in previous sections.

```nextflow
process {
    withName: STAR_ALIGN {
        memory = 100.GB
    }
}
```

> **NB:** We specify just the process name i.e. `STAR_ALIGN` in the config file and not the full task name string that is printed to screen in the error message or on the terminal whilst the pipeline is running i.e. `RNASEQ:ALIGN_STAR:STAR_ALIGN`. You may get a warning suggesting that the process selector isn't recognised but you can ignore that if the process name has been specified correctly. This is something that needs to be fixed upstream in core Nextflow.

### Updating containers

The [Nextflow DSL2](https://www.nextflow.io/docs/latest/dsl2.html) implementation of this pipeline uses one container per process which makes it much easier to maintain and update software dependencies. If for some reason you need to use a different version of a particular tool with the pipeline then you just need to identify the `process` name and override the Nextflow `container` definition for that process using the `withName` declaration. For example, in the [nf-core/viralrecon](https://nf-co.re/viralrecon) pipeline a tool called [Pangolin](https://github.com/cov-lineages/pangolin) has been used during the COVID-19 pandemic to assign lineages to SARS-CoV-2 genome sequenced samples. Given that the lineage assignments change quite frequently it doesn't make sense to re-release the nf-core/viralrecon everytime a new version of Pangolin has been released. However, you can override the default container used by the pipeline by creating a custom config file and passing it as a command-line argument via `-c custom.config`.

1. Check the default version used by the pipeline in the module file for [Pangolin](https://github.com/nf-core/viralrecon/blob/a85d5969f9025409e3618d6c280ef15ce417df65/modules/nf-core/software/pangolin/main.nf#L14-L19)
2. Find the latest version of the Biocontainer available on [Quay.io](https://quay.io/repository/biocontainers/pangolin?tag=latest&tab=tags)
3. Create the custom config accordingly:

   - For Docker:

     ```nextflow
     process {
         withName: PANGOLIN {
             container = 'quay.io/biocontainers/pangolin:3.0.5--pyhdfd78af_0'
         }
     }
     ```

   - For Singularity:

     ```nextflow
     process {
         withName: PANGOLIN {
             container = 'https://depot.galaxyproject.org/singularity/pangolin:3.0.5--pyhdfd78af_0'
         }
     }
     ```

   - For Conda:

     ```nextflow
     process {
         withName: PANGOLIN {
             conda = 'bioconda::pangolin=3.0.5'
         }
     }
     ```

> **NB:** If you wish to periodically update individual tool-specific results (e.g. Pangolin) generated by the pipeline then you must ensure to keep the `work/` directory otherwise the `-resume` ability of the pipeline will be compromised and it will restart from scratch.

### nf-core/configs

In most cases, you will only need to create a custom config as a one-off but if you and others within your organisation are likely to be running nf-core pipelines regularly and need to use the same settings regularly it may be a good idea to request that your custom config file is uploaded to the `nf-core/configs` git repository. Before you do this please can you test that the config file works with your pipeline of choice using the `-c` parameter. You can then create a pull request to the `nf-core/configs` repository with the addition of your config file, associated documentation file (see examples in [`nf-core/configs/docs`](https://github.com/nf-core/configs/tree/master/docs)), and amending [`nfcore_custom.config`](https://github.com/nf-core/configs/blob/master/nfcore_custom.config) to include your custom profile.

See the main [Nextflow documentation](https://www.nextflow.io/docs/latest/config.html) for more information about creating your own configuration files.

If you have any questions or issues please send us a message on [Slack](https://nf-co.re/join/slack) on the [`#configs` channel](https://nfcore.slack.com/channels/configs).

## Running in the background

Nextflow handles job submissions and supervises the running jobs. The Nextflow process must run until the pipeline is finished.

The Nextflow `-bg` flag launches Nextflow in the background, detached from your terminal so that the workflow does not stop if you log out of your session. The logs are saved to a file.

Alternatively, you can use `screen` / `tmux` or similar tool to create a detached session which you can log back into at a later time.
Some HPC setups also allow you to run nextflow within a cluster job submitted your job scheduler (from where it submits more jobs).

## Nextflow memory requirements

In some cases, the Nextflow Java virtual machines can start to request a large amount of memory.
We recommend adding the following line to your environment to limit this (typically in `~/.bashrc` or `~./bash_profile`):

```console
NXF_OPTS='-Xms1g -Xmx4g'
```
