
import pandas as pd
import subprocess
import os
import xml.etree.ElementTree as ET


EXCEL_OUTPUT = "E:/Univaq/assigned_tasks/commons-bcel/Results/commons-bcel-Insight.xlsx"
REPO_PATH = "E:/Univaq/assigned_tasks/commons-bcel"  # Path to the already cloned repository

def update_maven_compiler_options(pom_path):
    try:
        # Parse the pom.xml file with the default namespace registered
        ET.register_namespace('', 'http://maven.apache.org/POM/4.0.0')
        tree = ET.parse(pom_path)
        root = tree.getroot()

        namespaces = {'maven': 'http://maven.apache.org/POM/4.0.0'}

        # Locate or create the build section with maven-compiler-plugin configuration
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
            version.text = '3.8.1'  # Ensure a compatible version is used

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

        # Write the updated tree to the file without adding prefixes
        tree.write(pom_path, encoding='utf-8', xml_declaration=True)
        print(f"Updated compiler options in {pom_path} to Java 8")
    except Exception as e:
        print(f"Failed to update {pom_path}: {e}")


# Read the 'Commits insights' sheet from the Excel file
df = pd.read_excel(EXCEL_OUTPUT, sheet_name="Commits insights")
filtered_commits = df[df['Refactorings found'] >= 20]['Commit'].tolist()

# Check if there are any commits to process
if not filtered_commits:
    print("No commits found with 'Refactorings found' >= 20.")
else:
    for commit_hash in filtered_commits:
        print(f"\nProcessing commit: {commit_hash}")
        os.chdir(REPO_PATH)

        # Stash any local changes to avoid issues when switching commits
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
            continue

        # Update pom.xml to use Java 8
        pom_path1 = os.path.join(REPO_PATH, 'pom.xml')
        if os.path.exists(pom_path1):
            update_maven_compiler_options(pom_path1)

        # Compile the project at the current state to a JAR file with Maven, skipping tests
        try:
            subprocess.run(["C:/apache-maven-3.9.9/bin/mvn.cmd", "clean", "package", "-DskipTests", "-Drat.skip=true"], check=True)
            print(f"Project compiled successfully for commit {commit_hash}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to compile project at commit {commit_hash}: {e}")

# # Read the 'Commits insights' sheet from the Excel file
# df = pd.read_excel("E:/Univaq/assigned_tasks/commons-bcel/Results/commons-bcel-Insight.xlsx", sheet_name="Commits insights")
#
# # Filter the DataFrame where "Refactorings found" are greater than or equal to 20
# filtered_commits = df[df['Refactorings found'] >= 20]['Commit']
#
# # Iterate over each commit, stash changes, checkout, and compile the project
# for commit_hash in filtered_commits:
#     print(f"\nProcessing commit: {commit_hash}")
#
#     # Change directory to the repository path
#     os.chdir("E:/Univaq/assigned_tasks/commons-bcel")
#
#     # Stash any local changes to avoid issues when switching commits
#     try:
#         subprocess.run(["git", "stash"], check=True)
#         print("Local changes stashed successfully.")
#     except subprocess.CalledProcessError as e:
#         print(f"Failed to stash local changes: {e}")
#         continue
#
#     # Checkout to the specific commit
#     try:
#         subprocess.run(["git", "checkout", commit_hash], check=True)
#         print(f"Checked out to commit {commit_hash}")
#     except subprocess.CalledProcessError as e:
#         print(f"Failed to checkout to commit {commit_hash}: {e}")
#         continue
#
#     # Compile the project at the current state to a JAR file with Maven, skipping tests
#     try:
#         subprocess.run(["C:/apache-maven-3.9.9/bin/mvn.cmd", "clean", "package", "-DskipTests"], check=True)
#         print(f"Project compiled successfully for commit {commit_hash}")
#     except subprocess.CalledProcessError as e:
#         print(f"Failed to compile project at commit {commit_hash}: {e}")