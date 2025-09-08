from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate
flow = InstalledAppFlow.from_client_secrets_file('creds_drive.json', SCOPES)
creds = flow.run_local_server(port=8080)

service = build('drive', 'v3', credentials=creds)

folder_name = "Medical Records"

# Step 1: Get folder ID
folder_results = service.files().list(
    q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields="files(id, name)"
).execute()

folders = folder_results.get('files', [])
if not folders:
    print(f"No folder found with name: {folder_name}")
else:
    folder_id = folders[0]['id']
    print(f"Folder ID for '{folder_name}': {folder_id}")

    # Step 2: List files inside folder
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        pageSize=10,
        fields="files(id, name)"
    ).execute()

    items = results.get('files', [])
    if not items:
        print(f"No files found in '{folder_name}'")
    else:
        for item in items:
            print(f"{item['name']} ({item['id']})")