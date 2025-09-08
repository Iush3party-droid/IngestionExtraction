from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

folder_name = "Medical Records"

def fetchName():
    """Entry point: trigger workflow execution"""
    # Google Drive API setup
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    # Authenticate
    flow = InstalledAppFlow.from_client_secrets_file('creds_drive.json', SCOPES)
    creds = flow.run_local_server(port=8080)
    
    # Build Drive service
    service = build('drive', 'v3', credentials=creds)
    
    # Step 1: Get folder ID
    folder_results = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()

    folders = folder_results.get('files', [])
    items = []  # Initialize items list
    
    if not folders:
        print(f"No folder found with name: {folder_name}")
        return []  # Return empty list if no folder found
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

    file_names = [file['name'] for file in items]
    print(file_names)

    return file_names