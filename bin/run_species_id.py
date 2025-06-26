#!/usr/bin/env python3.7

## Requires python 3.7 due to singularity container
import argparse
import os
import sys
import shutil
import subprocess
import logging
import re
from io import StringIO
from datetime import datetime
from typing import Tuple, Optional, List

import pandas as pd
from tabulate import tabulate

#############################
## Argument Error Messages ##
#############################

class ParserWithErrors(argparse.ArgumentParser):
    """ My own error messages """

    def error(self, message: str) -> None:
        """Override the error method to print the message and show help."""
        print(f'\n{message}\n')
        self.print_help()
        sys.exit(2)

    def is_valid_mash(self, parser: argparse.ArgumentParser, arg: str) -> str:
        """Validate that the argument is a .msh file."""
        _, ext = os.path.splitext(arg)
        if ext != '.msh':
            parser.error(f'ERROR: This is not a file ending with .msh. Did you generate the mash sketch and specify that file to be uploaded?')
        return arg

    def is_valid_fastq(self, parser: argparse.ArgumentParser, arg: str) -> str:
        """Validate that the argument is a .fastq or .fastq.gz file."""
        _, ext = os.path.splitext(arg)
        if ext not in ('.gz', '.fastq') and not arg.endswith('.fastq.gz'):
            parser.error(f'ERROR: This is not a file ending with either .fastq or .fastq.gz. This flag requires the input of a fastq file.')
        return arg

    def is_valid_distance(self, parser: argparse.ArgumentParser, arg: str) -> str:
        """Validate that the argument is a positive float."""
        try:
            value = float(arg)
            if value < 0:
                raise ValueError
        except ValueError:
            parser.error(f'ERROR: {arg} is not a positive float, aka a number with a decimal point.')
        return arg

    def is_valid_int(self, parser: argparse.ArgumentParser, arg: str) -> str:
        """Validate that the argument is a positive integer."""
        if not arg.isdigit() or int(arg) <= 0:
            parser.error(f'ERROR: You input {arg}. This is NOT a positive integer.')
        return arg

#########################
## ArgParser Arguments ##
#########################

def argparser():
    """
    Returns argument parser for the script with messages for how to use tool.
    """

    description = (
        "A script to run and parse the output from Mash into a table listing" 
        " the top five matches from the user specified pre-built Mash Database.")

    ## use class to parse the arguments with formatted error message
    parser = ParserWithErrors(description = description)

    ## Define required and optional groups; uses lambda (anonymous) function
    parser._action_groups.pop()
    required = parser.add_argument_group('Required Arguments')
    optional = parser.add_argument_group('Optional Arguments')

    required.add_argument("--database", "-b", required=True,
                        help="Pre-built Mash Sketch",
                        type=lambda x: parser.is_valid_mash(parser, x))
    
    required.add_argument("--read1", "-r1", required=True,
                        help="Input Read 1 (forward) file",
                        type=lambda x: parser.is_valid_fastq(parser, x))
    
    required.add_argument("--read2", "-r2", required=True,
                        help="Input Read 2 (reverse) file",
                        type=lambda x: parser.is_valid_fastq(parser, x))
    
    optional.add_argument("--max_dist", "-d", default=0.05,
                        help="User-specified Mash distance (default: 0.05)",
                        type=lambda x: parser.is_valid_distance(parser, x))
    
    optional.add_argument("--kmer_min", "-m", default=2,
                        help="Min. k-mer copies to pass noise filter  (default: 2)",
                        type=lambda x: parser.is_valid_int(parser, x))
    
    optional.add_argument("--num_threads", "-p", default=2,
                        help="Number of computing threads to use (default: 2)",
                        type=lambda x: parser.is_valid_int(parser, x))

    optional.add_argument("--version", "-v" )
    return parser

###############
## FUNCTIONS ##
###############
def make_output_log(log: str) -> None:
    """
    Creates the log file which can be appended to.
    Logs operating system (OS) information where the script is being run.
    Requires the logging package and uses traditional '%' -style formating as 
    is standard with logging module. 

    Parameters
    ----------
    log : str
        Name of the log file.

    Returns
    -------
    None
        Logs an error message if unable to get system information.
    """
    # Configure logging
    logging.basicConfig(filename=log,
                        filemode="a",
                        level=logging.DEBUG,
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt="%m/%d/%Y %I:%M:%S %p")

    # Log file creation message
    logging.info("New log file created in output directory - %s" % log)
    logging.info("Starting the tool...")

    # Log system information
    try:
        sys_info = os.uname()
        logging.info("System Information:")
        logging.info("   System: %s" % sys_info.sysname)
        logging.info("   Node Name: %s" % sys_info.nodename)
        logging.info("   Release: %s" % sys_info.release)
        logging.info("   Version: %s" % sys_info.version)
        logging.info("   Machine: %s\n" % sys_info.machine)
    except AttributeError:
        # Handle cases where `os.uname` is not available 
        logging.warning("System information is not available on this platform")

def extract_base_name(filename: str) -> str:
    """
    Extract the base name from a sequencing read filename by removing 
    common file extensions and read pair identifiers.

    This function strips the following from the filename (if present):
      - `.gz` compression extension
      - `.fq` or `.fastq` sequencing file extensions
      - Common read suffixes like `_R1`, `_R2`, `_R1_001`, `_R2_001`

    Parameters
    ----------
    filename : str
        The full path or name of the file to process.

    Returns
    -------
    str
        The cleaned base name, suitable for use in downstream processing.
    """
    
    basename = os.path.basename(filename)
    basename = re.sub(r'\.gz$', '', basename)
    basename = re.sub(r'\.f(ast)?q$', '', basename)
    return re.sub(r'(_R?[12]_001|_R?[12])$', '', basename)

def fastq_name(read1: str, read2: str) -> str:
    """
    Gets stripped read name for appending to output files.

    Parameters
    ----------
    read1 : str
        Filename for the first read.
    read2 : str
        Filename for the second read.

    Returns
    -------
    str
        Base name of the file with the suffixes stripped.

    Raises
    ------
    ValueError
        If the base names from read1 and read2 do not match.
    """

    name1 = extract_base_name(read1)
    name2 = extract_base_name(read2)
    
    if name1 != name2:
        raise ValueError(f"Read1 base name ({name1}) and Read2 base name ({name2}) do not match.")
    return name1

def log_inputs(required: dict, optional: dict) -> None:
    """
    Log required and optional input parameters to the logger.

    This function logs all key-value pairs from the `required` and `optional`
    dictionaries using the INFO logging level. The parameters are formatted
    for readability, with each entry on a new line prefixed by a bullet.

    Parameters
    ----------
    required : dict
        A dictionary of required input parameters and their values.

    optional : dict
        A dictionary of optional input parameters and their values.

    Returns
    -------
    None
    """

    logging.info("Required Parameters:\n" + "\n".join(f" * {k}: {v}" for k, v in required.items()))
    logging.info("Optional Parameters:\n" + "\n".join(f" * {k}: {v}" for k, v in optional.items()))

def check_files(read1: str, read2: str, mash_db: str) -> None:
    """
    Checks if all the input files exist; raises an exception if file not found or if file is
    a directory.

    Parameters
    ----------
    read1 : str
        Path to input file 1.
    read2 : str
        Path to input file 2.
    mash_db : str
        Path to database file.

    Raises
    ------
    FileNotFoundError
        If any file doesn't exist or is a directory.
    ValueError
        If read1 and read2 are the same file.
    """
    
    def check_file(path: Optional[str], description: str):
        cleaned_path = path.strip() if path else path
        if path and not os.path.isfile(path):
                raise FileNotFoundError(f"{description} doesn't exist or is not a file: {path}")
    
    check_file(mash_db, "The database file")
    check_file(read1, "Read file 1")
    check_file(read2, "Read file 2")

    # Check if read1 and read2 are the same file
    if read1 == read2:
        raise ValueError(f"Read1 ({read1}) and Read2 ({read2}) are the same file.")

def is_file_empty(path: str) -> bool:
    """
    Check if a file is missing or empty.

    This function returns True if the specified file does not exist 
    or exists but has a size of zero bytes, indicating that it is empty.
    If the file exists but is empty, a warning is logged.

    Parameters
    ----------
    path : str
        The path to the file to be checked.

    Returns
    -------
    bool
        True if the file is missing or empty, False otherwise.
    """
    if not os.path.isfile(path):
        return True
    if os.path.getsize(path) == 0:
        logging.warning(f"File exists but is empty: {path}")
        return True
    return False

def get_k_size(mash_db: str) -> Optional[str]:
    """
    Retrieves the k-size from the Mash database information.

    Parameters
    ----------
    mash_db : str
        Path to the Mash database.

    Returns
    -------
    Optional[str]
        The k-size value extracted from the Mash info output.
        Returns None if an error occurs or the output format is unexpected.
    """
    try:
        # Run the mash info command and capture its output
        result = subprocess.run(
            ['mash', 'info', mash_db],
            capture_output=True,
            text=True,
            check=True
        )

        # Use regex to find and extract the k-mer size
        for line in result.stdout.splitlines():
            match = re.search(r'K-?mer size:\s+(\d+)', line, re.IGNORECASE)
            if match:
                return match.group(1)

        logging.error("k-size not found in mash info output.")
        return None

    except subprocess.CalledProcessError as e:
        logging.error("Failed to run mash info: %s", e)
        return None

def check_program(program_name: str) -> None:
    """
    Check if a required external program is available in the system PATH.

    This function verifies whether the specified program is accessible via 
    the system PATH using `shutil.which()`. If the program is not found, 
    the script logs a critical error and exits with status code 1.

    Additionally, if the program being checked is 'python', it ensures that 
    the running Python version is at least 3.7. If not, it logs a critical 
    error and exits.

    Parameters
    ----------
    program_name : str
        The name of the program to check for (e.g., 'mash', 'python').

    Returns
    -------
    None

    Exits
    -----
    Exits the script with status code 1 if the program is not found 
    or if the Python version is insufficient.
    """
    logging.info(f"Checking for program {program_name}...")

    path = shutil.which(program_name)
    if path is None:
        logging.critical(f"Program {program_name} not found. Exiting.")
        sys.exit(1)

    if program_name == 'python' and sys.version_info < (3, 7):
        logging.critical("Python >= 3.7 is required. Exiting.")
        sys.exit(1)

    logging.info(f"Program {program_name} is available.")

def check_mash() -> None:
    """
    Checks that Mash is running as expected.

    Returns
    -------
    None
        Exits the program if the results do not match the expected values.
    """
    # Define paths
    dirpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test-data'))
    file_path1 = os.path.join(dirpath, 'myCatFile')
    file_path2 = os.path.join(dirpath, 'myMashDatabase.msh')

    # Define Mash command
    mash_check = ['mash', 'dist', '-k', '25', '-s', '100000', file_path1, file_path2]

    # Run the Mash command
    result = subprocess.run(mash_check, capture_output=True, check=True, text=True)
    
    # Read and process the output
    df = pd.read_csv(StringIO(result.stdout), sep='\t', names=['Ref ID', 'Query ID', 'Mash Dist', 'P-value', 'Kmer'])
    df_dropped = df.drop(columns=['Ref ID', 'P-value', 'Kmer'])
    
    # Extract relevant information
    df_check_species = df['Query ID'].str.split('/').str[0].iloc[0]
    df_check_dist = df_dropped['Mash Dist'].iloc[0]
    
    EXPECTED_SPECIES  = 'Legionella_fallonii_LLAP-10_GCA_000953135.1.fna'
    EXPECTED_DISTANCE = 0.0185
    
    # Log and validate the results
    if df_check_species == EXPECTED_SPECIES and round(df_check_dist, 4) == EXPECTED_DISTANCE:
        rounded_distance = round(df_check_dist, 4)
        logging.info(
            "Great, the test confirms Mash is running properly.\n"
            "* Expected species: %s\n"
            "* Returned species: %s\n"
            "* Expected distance: %s\n"
            "* Returned distance: %s\n",
            EXPECTED_SPECIES,
            df_check_species,
            EXPECTED_DISTANCE,
            rounded_distance)
    else:
        logging.critical("Mash test failed. Exiting.")
        sys.exit(1)

def cat_files(read1: str, read2: str, output_path: str = 'myCatFile') -> None:
    """
    Concatenates the contents of two plain-text (non-gzipped) FASTQ files.

    Parameters
    ----------
    read1 : str
        Path to the first input file.
    read2 : str
        Path to the second input file.
    output_path : str, optional
        Output file path. Default is 'myCatFile'.

    Raises
    ------
    ValueError
        If either input file is gzipped.
    FileNotFoundError
        If either file doesn't exist.
    """
    if read1.endswith('.gz') or read2.endswith('.gz'):
        raise ValueError("One or both input files are gzipped. Cannot concatenate gzipped files.")

    logging.info("Concatenating %s and %s into %s...", read1, read2, output_path)

    try:
        with open(output_path, 'w') as out_f:
            for path in [read1, read2]:
                with open(path, 'r') as in_f:
                    shutil.copyfileobj(in_f, out_f)

        logging.info("Files concatenated into '%s'.", output_path)

    except FileNotFoundError as e:
        logging.critical("File not found during concatenation: %s", e)
        raise

def update_min_kmer(calculatedKmer: int, min_kmer: int = 2) -> int:
    """
    Determine the minimum kmer value. If user-specified min_kmer < 2, set to 2.
    Return the greater of calculatedKmer or user-specified min_kmer.

    Parameters
    ----------
    calculatedKmer : int
        Value calculated based on genomeCoverage/3 in cal_kmer function.
    min_kmer : int, optional, default is 2
        Input K-mer value specified by the user; used if greater than 2.

    Returns
    -------
    int
        Integer value used for min_kmer with paired-end reads.
    """
    min_kmer = max(int(min_kmer), 2)
    if min_kmer > 2:
        logging.info("User-specified a value for minimum K-mer: %s", min_kmer)
    else:
        logging.info("Min. K-mer = genome coverage divided by 3. Calculated K-mer = %s", calculatedKmer)
    return max(calculatedKmer, min_kmer)

def run_cmd(command: List[str]) -> subprocess.CompletedProcess:
    """
    Executes a shell command and logs output.

    Parameters
    ----------
    command : list of str
        Shell command as a list.

    Returns
    -------
    subprocess.CompletedProcess
        Result of command.

    Raises
    ------
    subprocess.CalledProcessError
    """
    logging.info("Running command: %s", ' '.join(command))

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result

    except subprocess.CalledProcessError as e:
        logging.critical("Command failed: %s", ' '.join(command))
        logging.critical("Return code: %s\nSTDOUT: %s\nSTDERR: %s", e.returncode, e.stdout, e.stderr)
        return None

def cal_kmer(mash_db: str, threads: int, min_kmer: int) -> Tuple[int, str, str]:
    """
    Estimate genome coverage and determine appropriate min_kmer (-m flag).

    Returns
    -------
    Tuple[int, str, str] :
        (min_kmer used, estimated genome size, genome coverage)
    """
    fastq_cmd = ['mash', 'dist', mash_db, '-r', 'myCatFile', '-p', str(threads), '-S', '42']
    result = run_cmd(fastq_cmd)
    if result is None:
        raise RuntimeError("Command failed, aborting.")

    stderr_lines = result.stderr.splitlines()

    if len(stderr_lines) < 2 or not stderr_lines[0].startswith("Estimated") or not stderr_lines[1].startswith("Estimated"):
        raise ValueError("Unexpected stderr format from mash dist.")

    try:
        gSize = stderr_lines[0].split(":", 1)[1].strip()
        gCoverage = stderr_lines[1][23:].strip()
        logging.info("Genome size (approx.): %s", gSize)
        logging.info("Genome coverage: %s", gCoverage)
    except Exception as e:
        raise ValueError("Failed to parse genome size or coverage: " + str(e))

    calc_kmer = int(float(gCoverage) / 3)
    mFlag = update_min_kmer(calc_kmer, min_kmer)

    return mFlag, gSize, gCoverage

def get_results(mFlag: int, threads: int, mash_db: str) -> subprocess.CompletedProcess:
    """
    Runs the mash distance command using value from cal_kmer and extracts genome size 
    and coverage from the command output.
    
    Parameters
    ----------
    mFlag : int
        The -m flag value for the mash command.
    threads : int
        Number of threads to use with the mash command.
    mash_db : str
        Path to the mash database.
    
    Returns
    -------
    subprocess.CompletedProcess
        The result of the mash command.
    """
    fastq_cmd2 = [
        'mash', 'dist', '-r', '-m', str(mFlag),
        str(mash_db), 'myCatFile', '-p', str(threads), '-S', '123456'
    ]
    
    output = run_cmd(fastq_cmd2)
    stderr_lines = output.stderr.splitlines()
    
    if len(stderr_lines) >= 2:
        try:
            gsize = stderr_lines[0].split(":", 1)[1].strip()
            gcover = stderr_lines[1].split(":", 1)[1].strip()
            logging.info("Estimated genome size: %s", gsize)
            logging.info("Estimated genome coverage: %s", gcover)
        except IndexError:
            logging.warning("Unexpected stderr line format from Mash.")

    return output

def parse_results(cmd: subprocess.CompletedProcess, in_max_dis: float) -> Tuple[str, str, pd.DataFrame]:
    """
    Run the initial command and parse the results from mash.
    
    Parameters
    ----------
    cmd : subprocess.CompletedProcess
        The completed process object from running the mash command.
    in_max_dis : float
        User-specified maximum mash distance for filtering results.
    
    Returns
    -------
    tuple
        - best_genus: str
            The most likely genus of the isolate tested.
        - best_species: str
            The most likely species of the isolate tested.
        - df_top: pandas.DataFrame
            The top five results from sorting Mash output.
    """
    
    if cmd is None:
        raise ValueError("No command result provided (cmd is None). Cannot parse results.")
    if not hasattr(cmd, 'stdout') or not cmd.stdout:
        raise ValueError("Command output (stdout) is empty or missing. Cannot parse results.")
    
    df = pd.read_csv(StringIO(cmd.stdout), sep='\t', names=['Ref ID', 'Query ID', 'Mash Dist', 'P-value', 'Kmer'])
    
    if df.empty:
        raise ValueError("Parsed DataFrame is empty. No results to process.")
    
    # Extract Genus and Species from 'Ref ID'
    df[['Genus', 'Species']] = df['Ref ID'].str.split('_', 1, expand=True)
    df[['Species', 'GeneBank Identifier']] = df['Species'].str.split('_', 1, expand=True)
    df['GeneBank Identifier'] = df['Ref ID'].str.extract(r'(GCA_\d+\.\d+)')
    
    # Split the 'Kmer' column into counts
    df[['KmersCount', 'sketchSize']] = df['Kmer'].str.split("/", expand=True)
    df['KmersCount'] = df['KmersCount'].astype(int)
    
    # Calculate sequence similarity percentage
    df['% Seq Sim'] = (1 - df['Mash Dist']) * 100
    
    # Sort and cleanup
    df_sorted = df.sort_values('KmersCount', ascending=False).drop(['Ref ID', 'Query ID', 'KmersCount', 'sketchSize'], axis=1)
    
    # These functions need to be defined in your codebase:
    best_genus_sort, best_species_sort = is_tie(df)
    best_genus, best_species = validate_best_match_within_distance(df_sorted, in_max_dis, best_genus_sort, best_species_sort)
    
    df_top = df_sorted[['Genus', 'Species', 'GeneBank Identifier', 'Mash Dist', '% Seq Sim', 'P-value', 'Kmer']].head(5)
    df_top.reset_index(drop=True, inplace=True)
    
    return best_genus, best_species, df_top

def is_tie(df: pd.DataFrame) -> Tuple[str, str]:
    """
    Determine if the k-mers count value is a tie with the second top isolate.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing k-mers count, genus, and species information.

    Returns
    -------
    tuple of str
        - A string indicating the best genus, either a specific genus or a tie message.
        - A string indicating the best species, either a specific species or a blank string if tied.
    """
    if len(df) == 1:
        return df.iloc[0]['Genus'], df.iloc[0]['Species']

    top_two = df.nlargest(2, 'KmersCount')
    if top_two.iloc[0]['KmersCount'] == top_two.iloc[1]['KmersCount']:
        return "This was a tie, see the top 5 results below", ""
    else:
        # Return actual top hit when there's no tie
        return top_two.iloc[0]['Genus'], top_two.iloc[0]['Species']
    
def validate_best_match_within_distance(in_file: pd.DataFrame, in_max_dis: float, best_g: str,
                                        best_s: str) -> Tuple[str, str]:
    """
    Determine if the top hit mash distances are >= user-specified mash distance.
    
    Parameters
    ----------
    in_file : pandas.DataFrame
        DataFrame containing the mash results with a column 'Mash Dist' representing the mash distances.
    in_max_dis : float
        User-specified maximum mash distance as a cut-off.
    best_g : str
        Current best species message.
    best_s : str
        Current best species placeholder.
    
    Returns
    -------
     Tuple[str, str]
        A tuple containing:
        - The updated best species message.
        - The updated best species placeholder.
    """
    logging.info("Confirming that best match is less than user-specified distance...")
    
    if in_file['Mash Dist'].iloc[0] < float(in_max_dis):
        logging.info("A best species match was found with mash distance less than %s", in_max_dis)
    else:
        best_g = f"No matches found with mash distances < {in_max_dis}..."
        best_s = " "
        logging.info("No matches found with mash distances < %s", in_max_dis)
    
    return best_g, best_s

def create_dummy_table(date_time: str, name: str, read1: str, read2: str,
                       max_dist: float, k_size: str, m_flag: int,
                       mash_db: str, mw_version: str) -> None:
    """
    Create a dummy results table with placeholder values when input FASTQ files are empty.

    This function generates a single-row DataFrame with 'NA' and NaN values to indicate 
    that no valid Mash results could be produced (e.g., due to empty input files). It then 
    passes this dummy data to `make_table()` to maintain consistent output structure 
    and logging.

    Parameters
    ----------
    date_time : str
        Timestamp of the analysis run.

    name : str
        Sample or run identifier.

    read1 : str
        File path to the first read (R1) FASTQ file.

    read2 : str
        File path to the second read (R2) FASTQ file.

    max_dist : float
        Maximum Mash distance threshold for reporting hits.

    k_size : str
        K-mer size used during Mash sketching.

    m_flag : int
        Mash k-mer match statistics, typically number of shared hashes.

    mash_db : str
        Path to the Mash reference database used in the analysis.

    mw_version : str
        Version of the MashWrapper tool used for this run.

    Returns
    -------
    None

    Logs
    ----
    Logs a warning when dummy results are created due to one or both input FASTQ files being empty.
    """
    dummy_row = {
        "Genus": "NA",
        "Species": "NA",
        "GeneBank Identifier": "NA",
        "Mash Dist": float('nan'),
        "% Seq Sim": float('nan'),
        "P-value": float('nan'),
        "Kmer": "NA"
    }

    dummy_df = pd.DataFrame([dummy_row])
    results = ("NA", "NA", dummy_df)
    make_table(date_time, name, read1, read2, max_dist, k_size, results, m_flag, mash_db, mw_version)
    logging.warning("One or both read files are empty. Created dummy results table.")

def make_table(date_time: str, name: str, read1: str, read2: str, max_dist: float, k_size: str,
               results: Tuple[str, str, pd.DataFrame], m_flag: int,
               mash_db: str, mw_version: str) -> None:
    """
    Parse results into a text output file including relevant variables.
    
    Parameters
    ----------
    date_time : str
        Current date and time for when analysis is run.
    name : str
        Base name for the output file.
    read1 : str
        Path to the first query file.
    read2 : str
        Path to the second query file.
    max_dist : float
        User-specified maximum mash distance.
    k_size : str
        Size of the K-mer.
    results : tuple
        Output from running and parsing mash commands, where:
        - results[0] is the best genus.
        - results[1] is the best species.
        - results[2] is a pandas DataFrame of the top results.
    m_flag : int
        Contains the minimum k-mer copy number.
    
    Returns
    -------
    None
        Writes the results to a text file.
    """
    file_name = f"{name}_results_{date_time}.txt"
    
    with open(file_name, 'a+') as f:
        f.write(f"\nLegionella Species ID Tool using Mash\n")
        f.write(f"Date and Time = {date_time}\n")
        f.write(f"Input query file 1: {read1}\n")
        f.write(f"Input query file 2: {read2}\n")
        f.write(f"Maximum Mash distance (-d): {max_dist}\n")
        f.write(f"Minimum K-mer copy number (-m) to be included in the sketch: {m_flag[0]}\n")
        f.write(f"K-mer size used for sketching: {k_size}\n")
        f.write(f"Mash Database name: {mash_db}\n")
        f.write(f"mashwrapper version: {mw_version}\n\n")
        if results[0] == "NA" and results[1] == "NA":
            f.write("Best species match: No results (input files may be empty)\n\n")
        else:
            f.write(f"Best species match: {results[0]} {results[1]}\n\n")
        f.write("Top 5 results:\n")
        f.write(u'\u2500' * 100 + "\n")
        f.write(tabulate(results[2], headers='keys', tablefmt='pqsl', numalign="center",
                         stralign="center", floatfmt=(None, None, None, ".5f", ".3f", ".8e"),
                         showindex=False) + "\n")

if __name__ == '__main__':
    # Argument parsing
    parser = argparser()
    args = parser.parse_args()

    mash_db = args.database
    max_dist = args.max_dist
    min_kmer = args.kmer_min
    threads = args.num_threads
    read1 = args.read1
    read2 = args.read2
    mw_version = args.version

    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d")

    name = fastq_name(read1, read2)
    log = f"{name}_run.log"

    req_programs = ['mash', 'python']

    make_output_log(log)
    
    log_inputs(
    required={'Read1': read1, 'Read2': read2, 'Mash Database': mash_db},
    optional={'Max Distance': max_dist, 'Min K-mer Count': min_kmer, 'K-mer Size': get_k_size(mash_db), 'Threads': threads})
    
    logging.info("Base name for the files: %s", name)

    check_files(read1, read2, mash_db)
    logging.info("Input files are present...")
    if  is_file_empty(read1) or is_file_empty(read2):
        logging.warning("One or both read files are empty. Creating dummy results...")
        create_dummy_table(date_time, name, read1, read2, max_dist, get_k_size(mash_db), (min_kmer), mash_db, mw_version)
        sys.exit(0)  # Exit early since no further processing needed

    for program in req_programs:
        check_program(program)
    logging.info("All prerequisite programs are accessible...\n")

    check_mash()
    logging.info("Internal system checks passed...")

    is_file_empty(mash_db)
    logging.info("Mash database is not empty...")

    cat_files(read1, read2)
    logging.info("File concatenated successfully...")

    mFlag = cal_kmer(mash_db, threads, min_kmer)
    logging.info("Minimum copies of each K-mer identified...") 

    outputFastq2 = get_results(mFlag[0], threads, mash_db)
    logging.info("Mash dist command completed...")

    results = parse_results(outputFastq2, max_dist)
    logging.info("Results parsed successfully...")

    make_table(date_time, name, read1, read2, max_dist, get_k_size(mash_db), results, mFlag, mash_db, mw_version)
    logging.info("Analysis completed for sample: %s", name)
    logging.info("EXITING!")
