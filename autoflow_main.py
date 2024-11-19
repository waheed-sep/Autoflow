import shutil
import subprocess
from pydriller import Repository
import re
from collections import Counter
import pandas as pd
import json
import os
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

# # Configuration variables
REPO_PATH = "E:/Univaq/assigned_tasks/xstream"  # Path to the already cloned repository
JSON_OUTPUT = "E:/Univaq/assigned_tasks/xstream/Results/final_results.json"
CSV_OUTPUT = "E:/Univaq/assigned_tasks/xstream/Results/"


def run_refactoring_miner(repo, json_output, branch_name='master'):
    """Runs RefactoringMiner with the specified switches on a repository."""

    # Find the path for RefactoringMiner from the system's environment PATH variable
    refactoring_miner_path = None
    for path in os.environ['PATH'].split(os.pathsep):
        candidate_path = os.path.join(path, "RefactoringMiner.bat")
        if os.path.isfile(candidate_path):
            refactoring_miner_path = candidate_path
            break

    if not refactoring_miner_path:
        print("Error: RefactoringMiner.bat not found in system PATH.")
        return

    # Construct the command for analyzing all commits in the specified branch
    command = [refactoring_miner_path, '-a', repo, branch_name, '-json', json_output]

    # print("Running RefactoringMiner with command:", " ".join(command))
    print("1. Running RefactoringMiner ...")

    # Run the command and capture output
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0:
        print(f"1.1 RefactoringMiner operation successful. Results saved in {json_output}.")
    else:
        print(f"1.1 Error running RefactoringMiner: {result.stderr.decode('utf-8')}")


# Execution
run_refactoring_miner(REPO_PATH, JSON_OUTPUT, branch_name='master')


######################## commits_insights #########################

# Function to count types between sha1s and return a dictionary of counts
def count_types_between_sha1s(data):
    sha1_counts = {}
    current_sha1 = None
    type_count = 0

    def recursive_search(item):
        nonlocal current_sha1, type_count

        if isinstance(item, dict):
            for key, value in item.items():
                if key == "sha1":
                    # If a sha1 is already being counted, save it and start a new count
                    if current_sha1 is not None:
                        sha1_counts[current_sha1] = type_count

                    # Update the current sha1 and reset the type count
                    current_sha1 = value
                    type_count = 0
                elif key == "type":
                    # Increment type count if a "type" key is found
                    type_count += 1

                # Recursively search in the value
                recursive_search(value)

        elif isinstance(item, list):
            for element in item:
                # Recursively search each element in the list
                recursive_search(element)

    # Start recursive search from the root of the JSON data
    recursive_search(data)

    # If the last sha1 is found, add it to the result
    if current_sha1 is not None:
        sha1_counts[current_sha1] = type_count

    return sha1_counts


# Load the JSON data and count the refactorings
with open(JSON_OUTPUT, 'r') as file:
    data1 = json.load(file)
    refactoring_counts = count_types_between_sha1s(data1)

# Initialize a list to store commit data
commit_data = []

# Collect commit data from the repository
for commit in Repository(REPO_PATH, only_in_branch="master").traverse_commits():
    commit_data.append({
        "Commit": commit.hash,
        "Date": commit.committer_date.date(),  # Ensure only the date part is exported
        "Files modified": commit.files,
        "Insertions": commit.insertions,
        "Deletions": commit.deletions,
        "Refactorings found": refactoring_counts.get(commit.hash, 0)  # Get the refactoring count or 0 if not found
    })

# Create a DataFrame from the collected data
df_commits = pd.DataFrame(commit_data)

# Sort the DataFrame by "Refactorings found" in descending order
df_commits.sort_values(by="Refactorings found", ascending=False, inplace=True)

# Export the DataFrame to a CSV file
df_commits.to_csv(CSV_OUTPUT + 'Commits insights.csv', index=False)
print("2. Data has been exported to 'Commits insights.csv'.")


######################## ref.type_counts #########################

# Function to extract and count occurrences of "type" values from a JSON file
def extract_type_counts(file_path):
    # Read the JSON file content as a string
    with open(file_path, 'r') as jsonfile:
        json_content = jsonfile.read()

    # Regex pattern to find all "type" attribute values
    pattern = r'"type"\s*:\s*"([^"]+)"'
    matches = re.findall(pattern, json_content)

    # Use Counter to count occurrences of each "type" value
    type_counts_inner = Counter(matches)

    # Sort the dictionary by the values (occurrences) in descending order
    sorted_type_counts = dict(sorted(type_counts_inner.items(), key=lambda item: item[1], reverse=True))

    return sorted_type_counts


# Example usage of the type counts function
type_counts_outer = extract_type_counts(JSON_OUTPUT)

# Convert the dictionary to a DataFrame
df_type_counts = pd.DataFrame(type_counts_outer.items(), columns=["Refactorings found", "Occurrences"])

# Export the DataFrame to a CSV file
df_type_counts.to_csv(CSV_OUTPUT + 'Refs-type counts.csv', index=False)
print("3. Data has been exported to 'Refs-type counts.csv'.")

######################## maven build and success/failed status #########################

# Directory to store renamed JARs
OUTPUT_DIR = os.path.join(REPO_PATH, 'commit-jars')
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Function to update the Maven compiler options in pom.xml
def update_maven_compiler_options(pom_path):
    try:
        ET.register_namespace('', 'http://maven.apache.org/POM/4.0.0')
        tree = ET.parse(pom_path)
        root = tree.getroot()
        namespaces = {'maven': 'http://maven.apache.org/POM/4.0.0'}

        build = root.find('maven:build', namespaces)
        if build is None:
            build = ET.SubElement(root, 'build')

        plugins = build.find('maven:plugins', namespaces)
        if plugins is None:
            plugins = ET.SubElement(build, 'plugins')

        compiler_plugin = None
        for plugin in plugins.findall('maven:plugin', namespaces):
            artifact_id = plugin.find('maven:artifactId', namespaces)
            if artifact_id is not None and artifact_id.text == 'maven-compiler-plugin':
                compiler_plugin = plugin
                break

        if compiler_plugin is None:
            compiler_plugin = ET.SubElement(plugins, 'plugin')
            group_id = ET.SubElement(compiler_plugin, 'groupId')
            group_id.text = 'org.apache.maven.plugins'
            artifact_id = ET.SubElement(compiler_plugin, 'artifactId')
            artifact_id.text = 'maven-compiler-plugin'
            version = ET.SubElement(compiler_plugin, 'version')
            version.text = '3.8.1'

        configuration = compiler_plugin.find('maven:configuration', namespaces)
        if configuration is None:
            configuration = ET.SubElement(compiler_plugin, 'configuration')

        source = configuration.find('maven:source', namespaces)
        if source is None:
            source = ET.SubElement(configuration, 'source')
        source.text = '8'

        target = configuration.find('maven:target', namespaces)
        if target is None:
            target = ET.SubElement(configuration, 'target')
        target.text = '8'

        tree.write(pom_path, encoding='utf-8', xml_declaration=True)
        print(f"Updated compiler options in {pom_path} to Java 8")
    except Exception as e:
        print(f"Failed to update {pom_path}: {e}")


# Load the CSV into a DataFrame
df = pd.read_csv(CSV_OUTPUT + 'Commits insights.csv')

# Ensure the "Status" and "Error cause" columns exist
if 'Status' not in df.columns:
    df['Status'] = ""
if 'Error cause' not in df.columns:
    df['Error cause'] = ""

# Filter commits with 'Refactorings found' >= 20
filtered_commits = df[df['Refactorings found'] >= 20]['Commit'].tolist()

# Process each commit
if not filtered_commits:
    print("No commits found with 'Refactorings found' >= 20.")
else:
    for commit_hash in filtered_commits:
        print(f"\nProcessing commit: {commit_hash}")
        os.chdir(REPO_PATH)

        # Stash any local changes
        try:
            subprocess.run(["git", "stash"], check=True)
            print("Local changes stashed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to stash local changes: {e}")
            continue

        # Checkout to the specific commit
        try:
            subprocess.run(["git", "checkout", commit_hash], check=True)
            print(f"Checked out to commit {commit_hash}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to checkout to commit {commit_hash}: {e}")
            df.loc[df['Commit'] == commit_hash, ['Status', 'Error cause']] = ['Failed', str(e)]
            continue

        # Update pom.xml if present
        pom_path1 = os.path.join(REPO_PATH, 'pom.xml')
        if os.path.exists(pom_path1):
            update_maven_compiler_options(pom_path1)

        # Compile the project
        try:
            subprocess.run(["mvn.cmd", "clean", "package", "-DskipTests", "-Drat.skip=true"],
                           check=True)
            print(f"Project compiled successfully for commit {commit_hash}")
            df.loc[df['Commit'] == commit_hash, 'Status'] = 'Success'
        except subprocess.CalledProcessError as e:
            print(f"Failed to compile project at commit {commit_hash}: {e}")
            df.loc[df['Commit'] == commit_hash, ['Status', 'Error cause']] = ['Failed', str(e)]

# Save the updated DataFrame back to a CSV file
df.to_csv(CSV_OUTPUT + 'Commits insights.csv', index=False)
print("Status and error causes have been recorded in 'Commits insights.csv'.")
