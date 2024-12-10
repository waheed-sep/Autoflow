import os
import subprocess
import shutil

# Paths
REPO = r"/home/waheed/Univaq/assigned_tasks/xstream"
COMMIT_JARS = r"/home/waheed/Univaq/assigned_tasks/Final-Results/XSTREAM-Results/commit-jars"
JMH_DIR = r"/home/waheed/Univaq/JMH_test"
JMH_RESULTS = "/home/waheed/Univaq/assigned_tasks/Final-Results/XSTREAM-Results/JMH-Results"
RESULTS_DIR = "/home/waheed/Univaq/assigned_tasks/Final-Results/XSTREAM-Results/"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Maven install command
MAVEN_INSTALL_CMD = [
    "mvn", "install:install-file",
    "-DgroupId=com.thoughtworks.xstream",
    "-DartifactId=xstream",
    "-Dversion=waheed",
    "-Dpackaging=jar",
]


def process_jars():
    # Get the list of JAR files in commit-jars directory
    jar_files = [
        f for f in os.listdir(COMMIT_JARS)
        if f.endswith(".jar") and "javadoc" not in f.lower()
    ]

    print(f"6.1 Found {len(jar_files)} JAR files to process (excluding 'javadoc' jars).")

    if not jar_files:
        print("6.2 No valid JAR files found to process.")
        return

    for jar_file in jar_files:
        try:
            # Extract the first 8 characters of the JAR name
            jar_name_prefix = jar_file[:8]
            jar_path = os.path.join(COMMIT_JARS, jar_file)

            print(f"\n6.3 Processing JAR: {jar_file} (prefix: {jar_name_prefix})")

            # Install the JAR with Maven
            subprocess.run(MAVEN_INSTALL_CMD + [f"-Dfile={jar_path}"], check=True)
            print(f"6.4 Installed {jar_file} successfully.")

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
                    ["java", "--add-opens", "java.base/java.util=ALL-UNNAMED", "-jar", benchmark_jar_path], cwd=JMH_DIR, stdout=output, stderr=subprocess.PIPE)
                print(f"6.6 Saved benchmark output to {output_file}")

                # Rename and move the generated res.csv file
                res_csv_path = os.path.join(RESULTS_DIR, "result.csv")
                if os.path.exists(res_csv_path):
                    summary_csv_path = os.path.join(JMH_RESULTS, f"{jar_name_prefix}-summary.csv")
                    shutil.move(res_csv_path, summary_csv_path)
                    print(f"6.7 Renamed and moved CSV to {summary_csv_path}")
                else:
                    print(f"6.7 No res.csv file found for JAR: {jar_file}")

        except subprocess.CalledProcessError as e:
            print(f"6.8 Error processing {jar_file}: {e}")
        except Exception as e:
            print(f"6.8 Unexpected error for {jar_file}: {e}")

    print("\n6.9 Processing completed.")


if __name__ == "__main__":
    process_jars()
