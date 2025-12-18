import os
import io
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from datetime import datetime

# --- CONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json' # GitHub creates this for us
FOLDER_ID = '1OJvqhuLYvD0O4Ts54IgHSNceU_fvQk1Q' # <--- UPDATE THIS!

def authenticate():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def main():
    service = authenticate()
    print("Successfully connected to Google Drive.")

    # 1. List CSV files in the folder
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents and mimeType='text/csv' and trashed=false",
        fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No CSV files found in the folder.')
        return

    for item in items:
        print(f"Found file: {item['name']} (ID: {item['id']})")
        
        # 2. Download the file
        request = service.files().get_media(fileId=item['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        fh.seek(0)
        df = pd.read_csv(fh)
        
        # 3. CLEANING LOGIC (Add your rules here)
        print("Cleaning data...")
        df.drop_duplicates(inplace=True)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # 4. Save Cleaned File
        timestamp = datetime.now().strftime("%Y%m%d")
        clean_filename = f"Clean_{timestamp}_{item['name']}"
        df.to_csv(clean_filename, index=False)
        
        # 5. Upload Clean File back to Drive
        file_metadata = {'name': clean_filename, 'parents': [FOLDER_ID]}
        media = MediaFileUpload(clean_filename, mimetype='text/csv')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Uploaded clean file: {clean_filename}")

if __name__ == '__main__':
    main()
