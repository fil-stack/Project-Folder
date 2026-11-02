import os
import pandas as pd

file_path = "Master_Contract_List.csv"


def load_data():
  if not os.path.exists(file_path):
    print("Error: Master_Contract_List.csv not found!")
    return None
  df = pd.read_csv(file_path)
  if "Status" not in df.columns:
    df["Status"] = "Unreviewed"
  return df


def main():
  while True:
    df = load_data()
    if df is None:
      break

    unreviewed_count = len(df[df["Status"] == "Unreviewed"])
    reviewed_count = len(df[df["Status"] == "Reviewed"])

    print("\n==============================")
    print(f" TOTAL CONTRACTS: {len(df)}")
    print(f" Reviewed: {reviewed_count} | Unreviewed: {unreviewed_count}")
    print("==============================")
    print("1. View next unreviewed contracts")
    print("2. Mark a Notice ID as Reviewed")
    print("3. Exit")

    choice = input("Choose an option (1-3): ").strip()

    if choice == "1":
      pending = df[df["Status"] == "Unreviewed"].head(5)
      print("\n--- NEXT UNREVIEWED CONTRACTS ---")
      for idx, row in pending.iterrows():
        print(f"ID: {row['Notice ID']}")
        print(f"Title: {row['Opportunity Title']}")
        print("-" * 40)
      input("\nPress Enter to return to menu...")

    elif choice == "2":
      nid = input("Enter the Notice ID you just reviewed: ").strip()
      if nid in df["Notice ID"].values:
        df.loc[df["Notice ID"] == nid, "Status"] = "Reviewed"
        df.to_csv(file_path, index=False)
        print(
            f"\n[SUCCESS] Notice ID {nid} marked as Reviewed! Progress saved.\n"
        )
      else:
        print(f"\n[ERROR] Notice ID '{nid}' not found in the list.\n")

    elif choice == "3":
      print("Goodbye!")
      break
    else:
      print("Invalid option. Please choose 1, 2, or 3.")


if __name__ == "__main__":
  main()