import os
import time

def purge_old_files():
    # Folders to clean
    folders = ['uploads', 'processed']
    now = time.time()
    
    # 24 hours in seconds (change to 3600 for 1 hour if preferred)
    max_age = 24 * 60 * 60 

    for folder in folders:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                # Ensure it's a file, not a nested folder
                if os.path.isfile(file_path):
                    # Check if file modification time is older than max_age
                    if now - os.path.getmtime(file_path) > max_age:
                        try:
                            os.remove(file_path)
                            print(f"Purged old file: {file_path}")
                        except Exception as e:
                            print(f"Could not delete {file_path}: {e}")

if __name__ == "__main__":
    purge_old_files()