# mashwrapper: Output

## Introduction

The output from the running mashWrapper is a directory with 3 or 6 subdirectories, depending on whether analysis included using a database (`use_database`) or building a database (`get_database`), respectively. This directory will be named “results” unless the name of the output directory is specified in the submission script. The following files will be included:

Directory name | Description of files in the directory
----------|-------------------
combinedOutput |	Collated files of text results and log files
donwloadedGenomes |	.fna files of genomes downloaded and renamed as Genus_spcies_genbank.fna. Only generated with the `get_database` flag.
mashDatabase |	Mash database that was built. Only generated with the `get_database` flag.
mashFiles |	Mash sketch files for each genome downloaded from NCBI. Only generated with the `get_database` flag.
pipelineInfo |	Metadata created while running the pipeline. For example, all software versions used to run the tool.
resultsByIsolate |	Individual log and results files for tested isolates. Additional details are given in the next section.

**Explanation of Results in the "collated_species_id_results.txt" or individual results files**
a. Date and Time: the date the job started execution. This date may differ from the time the job was submitted.
b. Input query file 1/2: the paired-end gzipped fastq files analyzed.
c. Maximum mash distance: The maximum mash distance allowable for assigning a “Best Species Match species identification”
d. Minimum k-mer copy number: This number is calculated from the estimated depth of coverage. This is the minimum number of times a k-mer must appear in the query fastq files to be added to the mash sketch. In general, higher coverage will be reflected in a higher minimum copy number and will result in a more representative Mash sketch.
e. Mash Database Name: Gives the file name of the mash database version used for the job.
f. Mashwrapper Version: Gives the version of the mashwrapper pipeline used for the job.
g. Best species match: if an isolate sequence meets the minimum cutoffs for species identification set by maximum mash distance, the species of that isolate is reported. If no isolate meets the cutoff, the report will state “No matches found.” If multiple top results listed in the table have identical values for mash distance, %sequence similarity, p-value, and kmer output values, “This was a tie, see the top 5 results below” is listed.
h. Top 5 Results: detailed information about the five best matches reported by Mash. The top five matches will be listed, whether a successful identification was made or not. In addition to the species name of the matching isolates, the specific isolate IDs are also returned, as are the match statistics. The meaning of these metrics can be found in the Mash manual. It is important to note that the p-value reported here does not reflect a probability of a correct match, but rather the confidence in the distance value estimated by Mash. Lastly, the % Seq Sim (Sequence Similarity) is an approximate value and is calculated as 1 - Mash Dist.

