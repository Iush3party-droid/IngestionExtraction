from langgraph.graph import StateGraph
import requests
from typing import TypedDict, List, Any, Dict
from utils.fetchName import fetchNameAndIds
import os
import gdown
import re

class State(TypedDict):
    files: List[str] ## contain file_names
    files_id: List[str] ## contain file_ids
    downloaded_files: List[str] ## contain local file paths
    uploaded: List[Dict[str, Any]] ## contain uploaded file JSON responses
    signed_urls: List[str] ## contain signed URLs
    ocr_texts: List[Dict[str, Any]] ## contain OCR text JSON responses

def start_node(state: State) -> State:
    file_names, file_ids = fetchNameAndIds()
    state["files"] = file_names
    state["files_id"] = file_ids
    return state


def download_file(state: Dict[str, Any]) -> Dict[str, Any]:
    """download method using gdown library"""

    file_ids = state.get("files_id", [])
    files = state.get("files", [])
    downloaded = []
    
    # Ensure "downloads" directory exists
    os.makedirs("downloads", exist_ok=True)
    
    for file_id, file_name in zip(file_ids, files):
        print(f"Downloading file : {file_name}")

        local_path = os.path.join("downloads", file_name)
        url = f"https://drive.google.com/uc?id={file_id}"
        
        gdown.download(url, local_path, quiet=False)
        
        # Verify the file was downloaded correctly
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            # For PNG files, verify it's actually a PNG
            if file_name.lower().endswith('.png'):
                with open(local_path, 'rb') as f:
                    header = f.read(8)
                    png_signature = b'\x89PNG\r\n\x1a\n'
                    if header.startswith(png_signature):
                        downloaded.append(local_path)
                        print(f"Successfully downloaded: {file_name}")
                    else:
                        print(f"Downloaded {file_name} is not a valid PNG file")
                        os.remove(local_path)
            else:
                downloaded.append(local_path)
                print(f"Successfully downloaded: {file_name}")
        else:
            print(f"Failed to download {file_name} - file not created or empty")

    state["downloaded_files"] = downloaded
    return state

def upload_to_mistral(state: State) -> State:
    """Upload each PNG file in state['downloaded_files'] to Mistral server"""
    results = []
    url = "https://api.mistral.ai/v1/files"
    headers = {
        "Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY', 'LwjDmg6zCUPfm6eFEppoZcGBo8uYkdmU')}"
    }

    downloaded_files = state.get("downloaded_files", [])
    file_names = state.get("files", [])
    
    for file_path, file_name in zip(downloaded_files, file_names):
        print(f"Uploading {file_name} to Mistral...")

        with open(file_path, "rb") as file_obj:
            files = {"file": (file_name, file_obj)}  
            data = {"purpose": "ocr"}

            resp = requests.post(url, headers=headers, files=files, data=data)
            resp_json = resp.json()
            results.append(resp_json)
            print(f"Successfully uploaded {file_name}: {resp_json}")

    state["uploaded"] = results
    return state

def retrieve_signed_url(state: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve signed URLs for uploaded files from Mistral AI API"""
    signed_urls = []
    
    # Get API key from environment or state
    api_key = state.get("mistral_api_key") or "LwjDmg6zCUPfm6eFEppoZcGBo8uYkdmU"
    
    for item in state.get("uploaded", []):
        file_id = item.get("id")
            
        # Make API call to get signed URL
        url = f"https://api.mistral.ai/v1/files/{file_id}/url"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Extract signed URL from response
        response_data = response.json()
        signed_url = response_data.get("url")
        
        if signed_url:
            signed_urls.append(signed_url)
    state["signed_urls"] = signed_urls
    return state

def ocr_results(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch OCR results from Mistral OCR API"""
    texts = []
    
    api_url = "https://api.mistral.ai/v1/ocr"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer LwjDmg6zCUPfm6eFEppoZcGBo8uYkdmU"
    }
    
    for url in state.get("signed_urls", []):
        # Prepare the request payload
        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "image_url",
                "image_url": url
            },
            "include_image_base64": True
        }
        
        # Make the API request
        response = requests.post(api_url, json=payload, headers=headers)
        
        # Parse the response
        result = response.json()
        
        # Extract the OCR text from the response
        # Mistral OCR returns text in pages[].markdown format
        if 'pages' in result and len(result['pages']) > 0:
            # Combine text from all pages
            ocr_text = ""
            for page in result['pages']:
                page_text = page.get('markdown', '')
                clean_text = re.sub(r'!\[.*?\]\(.*?\)', '', page_text)
                clean_text = re.sub(r'\|.*?\|', ' ', clean_text)
                clean_text = re.sub(r'#{1,6}\s*', '', clean_text)
                clean_text = re.sub(r'\s+', ' ', clean_text)
                ocr_text += clean_text.strip() + " "
            ocr_text = ocr_text.strip()
        else:
            ocr_text = result.get('text', '')
        
        print(ocr_text)
        texts.append(ocr_text)
    state["ocr_texts"] = texts
    return state
# -------- Graph Wiring --------
workflow = StateGraph(State)

workflow.add_node("start", start_node)
workflow.add_node("download", download_file)
workflow.add_node("upload", upload_to_mistral)
workflow.add_node("signed_url", retrieve_signed_url)
workflow.add_node("ocr", ocr_results)

workflow.set_entry_point("start")
workflow.add_edge("start", "download")
workflow.add_edge("download", "upload")
workflow.add_edge("upload", "signed_url")
workflow.add_edge("signed_url", "ocr")

app = workflow.compile()

# -------- Run Workflow --------
if __name__ == "__main__":
    print("Starting LangGraph Workflow...")
    try:
        # Initialize with empty state - the start_node will populate it
        initial_state = {}
        result = app.invoke(initial_state)
        print("Workflow completed successfully!")
        print("Final state:", result)
        print("OCR Texts:", result.get("ocr_texts"))
        print("Files found:", result.get("files"))
    except Exception as e:
        print(f"Workflow failed with error: {e}")
        import traceback
        traceback.print_exc()