import shutil
import subprocess
from pydriller import Repository
import re
from collections import Counter
import pandas as pd
import json
import os
import xml.etree.ElementTree as ET

# Configuration variables
REPO = r"/home/waheed/Univaq/assigned_tasks/eclipse-collections"
RESULTS_OUTPUT = "/home/waheed/Univaq/assigned_tasks/Final-Results/ECLIPSE_COLLECTIONS-Results"  # Store all results (json, csv, jmh)
COMMIT_JARS = RESULTS_OUTPUT + "/Commit-Jars"
JMH_RESULTS = RESULTS_OUTPUT + "/JMH-Results"
JSON_OUTPUT = RESULTS_OUTPUT + "/Refactoring_results.json"
JMH_DIR = "/home/waheed/Univaq/JMH_ECollections"

os.makedirs(COMMIT_JARS, exist_ok=True)
os.makedirs(JMH_RESULTS, exist_ok=True)

def run_refactoring_miner(repo, json_output, branch_name='master'):
    """Runs RefactoringMiner with the specified switches on a repository."""

    # Find the path for RefactoringMiner from the system's environment PATH variable
    refactoring_miner_path = None
    for path in os.environ['PATH'].split(os.pathsep):
        candidate_path = os.path.join(path, "/home/waheed/RefactoringMiner/build/distributions/RefactoringMiner-3.0.10/bin/RefactoringMiner")
        if os.path.isfile(candidate_path):
            refactoring_miner_path = candidate_path
            break

    if not refactoring_miner_path:
        print("Error: RefactoringMiner not found in system PATH.")
        return

    # Construct the command for analyzing all commits in the specified branch
    command = [refactoring_miner_path, '-a', repo, branch_name, '-json', json_output]

    # Explicitly set JAVA_HOME in the environment
    env = os.environ.copy()
    env['JAVA_HOME'] = "/usr/lib/jvm/java-1.21.0-openjdk-amd64"
    env['PATH'] = f"/usr/lib/jvm/java-1.21.0-openjdk-amd64/bin:" + env['PATH']

    print("1. Running RefactoringMiner...")

    # Run the command and capture output
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

    if result.returncode == 0:
        print(f"1.1 RefactoringMiner operation successful. Results saved in {json_output}.")
    else:
        print(f"1.1 Error running RefactoringMiner: {result.stderr.decode('utf-8')}")


# Execution
run_refactoring_miner(REPO, JSON_OUTPUT, branch_name='master')


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
for commit in Repository(REPO, only_in_branch="master").traverse_commits():
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
df_commits.to_csv(RESULTS_OUTPUT + '/Commits insights.csv', index=False)
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
df_type_counts.to_csv(RESULTS_OUTPUT + '/Refs-type counts.csv', index=False)
print("3. Data has been exported to 'Refs-type counts.csv'.")


####################### maven build and success/failed status #########################

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
df = pd.read_csv(RESULTS_OUTPUT + '/Commits insights.csv')

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
        os.chdir(REPO)

        # Stash any local changes, including untracked files
        try:
            subprocess.run(["git", "stash", "-u"], check=True)
            print("Local changes (including untracked files) stashed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to stash local changes: {e}")
            continue

        # Clean untracked files if any exist
        try:
            subprocess.run(["git", "clean", "-fd"], check=True)
            print("Untracked files cleaned successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clean untracked files: {e}")
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
        pom_path1 = os.path.join(REPO, 'pom.xml')
        if os.path.exists(pom_path1):
            update_maven_compiler_options(pom_path1)

        # Compile the project
        try:
            subprocess.run(["mvn", "clean", "package", "-Dmaven.test.skip=true", "-Drat.skip=true"],
                           check=True)
            print(f"Project compiled successfully for commit {commit_hash}")
            df.loc[df['Commit'] == commit_hash, 'Status'] = 'Success'
        except subprocess.CalledProcessError as e:
            print(f"Failed to compile project at commit {commit_hash}: {e}")
            df.loc[df['Commit'] == commit_hash, ['Status', 'Error cause']] = ['Failed', str(e)]

# Save the updated DataFrame back to a CSV file
df.to_csv(RESULTS_OUTPUT + '/Commits insights.csv', index=False)
print("Builds statuses have been recorded in 'Commits insights.csv'.")

# Filter for commits with 'Refactorings found' >= 20 and 'Success' in 'Status'
filtered_commits = df[(df['Refactorings found'] >= 20) & (df['Status'] == 'Success')]['Commit'].tolist()

# Process each filtered commit
if not filtered_commits:
    print("5. No commits found with 'Refactorings found' >= 20 and 'Success' status.")
else:
    for commit_hash in filtered_commits:
        print(f"\nProcessing commit: {commit_hash}")
        os.chdir(REPO)

        # Stash any local changes
        try:
            subprocess.run(["git", "stash"], check=True)
            print("5.1 Local changes stashed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"5.1 Failed to stash local changes: {e}")
            continue

        # Checkout to the specific commit
        try:
            subprocess.run(["git", "checkout", commit_hash], check=True)
            print(f"5.2 Checked out to commit {commit_hash}")
        except subprocess.CalledProcessError as e:
            print(f"5.2 Failed to checkout to commit {commit_hash}: {e}")
            continue

        # Clean previous build artifacts
        subprocess.run(["mvn", "clean"], check=True)

        # Update pom.xml if present
        pom_path1 = os.path.join(REPO, 'pom.xml')
        if os.path.exists(pom_path1):
            update_maven_compiler_options(pom_path1)

        # Compile the project
        try:
            subprocess.run(["mvn", "package", "-Dmaven.test.skip=true", "-Drat.skip=true", "-Dmaven.javadoc.skip=true"],
                           check=True)
            print(f"5.3 Project compiled successfully for commit {commit_hash}")

            # Copy and rename only the main JAR file to avoid duplications
            target_dir = os.path.join(REPO, "eclipse-collections/target")
            if os.path.exists(target_dir):
                jar_files = [f for f in os.listdir(target_dir) if f.endswith(".jar")]
                for jar_file in jar_files:
                    if "tests" not in jar_file and "sources" not in jar_file and "test-sources" not in jar_file:
                        old_jar_path = os.path.join(target_dir, jar_file)
                        new_jar_name = f"{commit_hash[:8]}-{jar_file}"
                        new_jar_path = os.path.join(COMMIT_JARS, new_jar_name)
                        shutil.copy2(old_jar_path, new_jar_path)
                        print(f"Copied and renamed {jar_file} to {new_jar_name}")
        except subprocess.CalledProcessError as e:
            print(f"5.3 Failed to compile project at commit {commit_hash}: {e}")

print("5.4 Process completed.")

###################### Calling commits_jmh.py #######################

# Maven install command
MAVEN_INSTALL_CMD = [
    "mvn", "install:install-file",
    "-DgroupId=org.eclipse.collections",
    "-DartifactId=collections",
    "-Dversion=waheed",
    "-Dpackaging=jar",
]


def process_jars():
    # Get the list of JAR files in Commit-jars directory
    jar_files2 = [
        f for f in os.listdir(COMMIT_JARS)
        if f.endswith(".jar") and "javadoc" not in f.lower()
    ]

    print(f"6.1 Found {len(jar_files2)} JAR files to process (excluding 'javadoc' jars).")

    if not jar_files2:
        print("6.2 No valid JAR files found to process.")
        return

    for jar_file2 in jar_files2:
        try:
            # Extract the first 8 characters of the JAR name
            jar_name_prefix = jar_file2[:8]
            jar_path = os.path.join(COMMIT_JARS, jar_file2)

            print(f"\n6.3 Processing JAR: {jar_file2} (prefix: {jar_name_prefix})")

            # Install the JAR with Maven
            subprocess.run(MAVEN_INSTALL_CMD + [f"-Dfile={jar_path}"], check=True)
            print(f"6.4 Installed {jar_file2} successfully.")

            # Build the Uber JAR for JMH_test
            os.chdir(JMH_DIR)
            subprocess.run(["mvn", "clean", "package"], check=True)
            print("6.5 Created Uber JAR: JMH-Benchmark-MWK.jar")

            # Path to the JMH benchmark JAR
            benchmark_jar_path = os.path.join(JMH_DIR, "target", "JMH-Benchmark-MWK.jar")

            if not os.path.exists(benchmark_jar_path):
                print(f"6.5 Benchmark JAR not found: {benchmark_jar_path}")
                continue

            # Run the benchmark JAR and capture its output
            output_file = os.path.join(JMH_RESULTS, f"{jar_name_prefix}-jmh-output.txt")
            with open(output_file, "w") as output:
                subprocess.run(
                    ["java", "--add-opens", "java.base/java.util=ALL-UNNAMED", "-jar", benchmark_jar_path], cwd=JMH_DIR,
                    stdout=output, stderr=subprocess.PIPE)
                print(f"6.6 Saved benchmark output to {output_file}")

                # Rename and move the generated res.csv file
                result_csv = os.path.join(RESULTS_OUTPUT, "result.csv")
                if os.path.exists(result_csv):
                    summary_csv = os.path.join(JMH_RESULTS, f"{jar_name_prefix}-summary.csv")
                    shutil.move(result_csv, summary_csv)
                    print(f"6.7 Saved CSV to {summary_csv}.")
                else:
                    print(f"6.7 No result.csv file found for JAR: {jar_file2}")

        except subprocess.CalledProcessError as e:
            print(f"Error processing {jar_file2}: {e}")
        except Exception as e:
            print(f"Unexpected error for {jar_file2}: {e}")

    print("\nProcessing completed.")

0
if __name__ == "__main__":
    process_jars()
