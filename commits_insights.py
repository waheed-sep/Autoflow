import os

from pydriller import Repository

# n = 0
# for commit in Repository("./cloned_repo/PowerJoule", only_in_branch="master").traverse_commits():
#     # print("{}".format(commit.hash))
#     print("{}, {}, +{}, -{}, {}".format(commit.hash, commit.committer_date, commit.insertions, commit.deletions,
#                                         commit.files))
#     n = n + 1
# print("total: ", n)



# import pandas as pd
# from pydriller import Repository
#
# # Initialize an empty list to store commit data
# commit_data = []
#
# # Traverse through the commits and collect the data
# for commit in Repository("./cloned_repo/PowerJoule", only_in_branch="master").traverse_commits():
#     commit_data.append({
#         "Commit": commit.hash,
#         "Commit date": commit.committer_date.date(),
#         "Files modified": commit.files,
#         "Insertions": commit.insertions,
#         "Deletions": commit.deletions
#     })
#
# # Create a DataFrame from the collected data
# df = pd.DataFrame(commit_data)
#
# # Export the DataFrame to an Excel file
# output_path = "./cloned_repo/PowerJoule/commits_report.xlsx"
# df.to_excel(output_path, index=False)
#
# print(f"Data has been exported to {output_path}")




import pandas as pd
from pydriller import Repository
#
# # Initialize an empty list to store commit data
# commit_data = []
#
# # Traverse through the commits and collect the data
# for commit in Repository("./cloned_repo/PowerJoule", only_in_branch="master").traverse_commits():
#     commit_data.append({
#         "Commit": commit.hash,
#         "Date": commit.committer_date.date(),  # Keep only the date part
#         "Insertions": commit.insertions,
#         "Deletions": commit.deletions
#     })
#
# # Create a DataFrame from the collected data
# df = pd.DataFrame(commit_data)
#
# # Export the DataFrame to an Excel file with a specific worksheet name
# output_path = "./cloned_repo/PowerJoule/Insight.xlsx"
# with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
#     df.to_excel(writer, sheet_name="Commits insights", index=False)
#
# print(f"Data has been exported to {output_path} with the sheet 'Commits insights'")

print(os.getcwd())




