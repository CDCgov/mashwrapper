## mashwrapper: Output

### Introduction

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

* **Date and Time:** The date the job started execution. This date may differ from the time the job was submitted.  
* **Input query file 1/2:** The paired-end gzipped fastq files analyzed.  
* **Maximum mash distance:** The maximum Mash distance allowable for assigning a “Best Species Match" identification.     
* **Minimum k-mer copy number:** This value is calculated from the estimated depth of coverage. It represents the minimum number of times a k-mer must appear in the query fastq files to be added to the Mash sketch. Generally, higher coverage will be reflected in a higher minimum copy number, leading to a more representative Mash sketch.  
* **Mash Database Name:** The file name of the Mash database version used for the job.
* **Mashwrapper Version:** The version of the Mashwrapper pipeline used for the job.
* **Best species match:** If an isolate sequence meets the minimum criteria for species identification based on the maximum Mash distance, the species of that isolate will be reported. If no isolate meets the cutoff, the report will state, "No matches found." If multiple top results have identical values for Mash distance, sequence similarity, p-value, and k-mer output values, the report will state, "This was a tie. See the top 5 results below."    
* **Top 5 Results:** Detailed information about the five best matches reported by Mash. These results will be shown, whether or not a successful identification was made. In addition to the species names of the matching isolates, the specific isolate IDs and match statistics will also be provided. The meaning of these metrics can be found in the Mash manual. It's important to note that the p-value reported here reflects the confidence in the estimated distance value, not the probability of a correct match. Additionally, the % Seq Sim (Sequence Similarity) is an approximate value, calculated as 1 - Mash Distance.

