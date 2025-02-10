#!/usr/bin/env python
import os
import logging
import requests
import backoff
from dotenv import load_dotenv
from msal import PublicClientApplication
from functools import lru_cache
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
load_dotenv()

# Microsoft Azure App Registration Details
CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Files.ReadWrite.All"]

app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY)


@lru_cache(maxsize=1)
def get_access_token():
    """Fetches or refreshes an access token."""
    accounts = app.get_accounts()
    result = (
        app.acquire_token_silent(SCOPES, account=accounts[0])
        if accounts
        else app.acquire_token_interactive(SCOPES)
    )

    if "access_token" in result:
        return result["access_token"]
    raise Exception(f"Failed to get access token: {result.get('error_description', 'Unknown error')}")


@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def get_files_recursive(root_folder_id ):
    """Retrieve all files from OneDrive recursively."""
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    queue = [root_folder_id]
    all_files = []

    while queue:
        folder_id = queue.pop(0)
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            for item in response.json().get("value", []):
                if "file" in item:
                    all_files.append({
                        "id": item["id"],
                        "name": item["name"],
                        "size": item.get("size", 0),
                        "hash": item.get("file", {}).get("hashes", {}).get("quickXorHash", ""),
                        "webUrl": item.get("webUrl", "")
                    })
                elif "folder" in item:
                    queue.append(item["id"])
        else:
            logging.error(f"Error fetching folder {folder_id}: {response.text}")

    return all_files


def detect_duplicates(files):
    """Find duplicate files based on size and hash."""
    duplicates = {}

    # Process files
    for file in files:
        key = (file['size'], file['hash'])  # Key based on size and hash

        # If key exists in dictionary, append file to the list
        if key in duplicates:
            duplicates[key].append(file)
        else:
            duplicates[key] = [file]  # Otherwise, create a new list for this key

    # Keep only entries with more than one file (duplicates)
    duplicates = {key: val for key, val in duplicates.items() if len(val) > 1}

    return duplicates

def delete_duplicates(duplicates):
    """Delete duplicate files, keeping only the first file in each group, and return the list of kept files."""
    access_token = get_access_token()
    if not duplicates:
        print("No duplicate files found.")
        return []

    headers = {"Authorization": f"Bearer {access_token}"}
    kept_files = []  # List to store the kept files
    delete_all = False
    
    for (size, hash_value), files in duplicates.items():
        logging.info(f"\nDuplicate group (Size: {size} bytes, Hash: {hash_value}):")

        # Keep the first file and delete the others
        original = files[0]
        duplicates_to_delete = files[1:]
        logging.info(original)
        logging.info(duplicates_to_delete)
        # Add the original file to the list of kept files
        kept_files.append(original)
        logging.info(f"Keeping: {original['name']} ({original['webUrl']})")
        
        for file in duplicates_to_delete:
            if not delete_all:
                # Ask for user confirmation
                choice = input(f"Delete '{file['name']}'? (yes/all/no): ").strip().lower()

                if choice == "no":
                    continue
                elif choice == "all":
                    delete_all = True  # Automatically delete all remaining duplicates without asking
                elif choice != "yes":
                    print(f"Invalid choice for {file['name']}. Skipping.")
                    continue

            print(f"Deleting duplicate: {file['name']} ({file['webUrl']})")

            # Perform the deletion via Microsoft Graph API
            response = requests.delete(
                f"https://graph.microsoft.com/v1.0/me/drive/items/{file['id']}",
                headers=headers,
            )

            if response.status_code == 204:
                print(f"Deleted: {file['name']}")
            else:
                print(f"Failed to delete {file['name']}: {response.text}")

    return kept_files


if __name__ == "__main__":
    all_files = get_files_recursive("root")

    duplicates = detect_duplicates(all_files)

    if duplicates:
        print("\nDuplicate Files Detected:")
        for key, files in duplicates.items():
            for file in files:
                print(f"- {file['name']} ({file['webUrl']})")

        delete_duplicates(duplicates)
    else:
        print("No duplicate files found.")
