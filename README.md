# Code Functionality Overview
## 1. Running RefactoringMiner
Identifies the RefactoringMiner executable (RefactoringMiner.bat) in the system's `PATH`.
Executes `RefactoringMiner` to analyze all commits in the specified repository and branch (master by default).
Saves the results as a JSON file in the specified location.
Outputs success or error messages depending on the execution result.
## 2. Extracting Commit Insights
Analyzes the JSON output from `RefactoringMiner` to count the number of refactorings (types) associated with each commit SHA1.
Collects commit metadata (hash, date, modified files, insertions, deletions) from the specified repository using PyDriller.
Merges the metadata with refactoring counts to create a detailed DataFrame of commit insights.
Sorts the commits by the number of refactorings found, in descending order.
Exports the data to a CSV file named Commits insights.csv.
## 3. Counting Refactoring Types
Reads the JSON output from `RefactoringMiner`.
Extracts and counts occurrences of the `type` attribute (representing different refactoring types) using a regex pattern.
Creates a sorted dictionary of refactoring types and their occurrences.
Converts the dictionary to a DataFrame.
Exports the data to a CSV file named `Refs-type counts.csv`.
## 4. Building Maven Projects and Commit-Level Analysis
Filters commits with `Refactorings found >= 20` from the `Commits insights.csv` file.
Iterates through each filtered commit and performs the following:
Stashes any local changes in the repository.
Checks out the specific commit.
Updates the pom.xml file to set the Maven compiler to `Java 8`, if required.
Compiles the project using Maven with clean package and skips tests.
Updates the commit's status (Success or Failed) and records any error causes in the `Commits insights.csv` file.
## 5. Managing Output and Error Logging

The results of each operation, including success or failure details, are recorded in the CSV files.
The outputs (`Commits insights.csv` and `Refs-type counts.csv`) are saved in the specified output directory.

**Notes for Users**
Ensure that the `RefactoringMiner` executable is available in the system's PATH.
Update the configuration variables `(REPO_PATH, JSON_OUTPUT, CSV_OUTPUT)` as per your system's setup.
Python packages such as `pandas`, `pydriller`, and `xml.etree.ElementTree` are required to run this script. Install them using pip if not already installed.
The script assumes that the repository is already cloned and accessible in the specified `REPO_PATH`.