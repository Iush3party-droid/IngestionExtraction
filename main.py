from langgraph.graph import StateGraph
import requests
from typing import TypedDict, List, Any, Dict
from utils.fetchName import fetchNameAndIds
import os
import gdown

class State(TypedDict):
    files: List[str] ## contain file_names
    files_id: List[str] ## contain file_ids
    downloaded_files: List[str] ## contain local file paths
    uploaded: List[Dict[str, Any]] ## contain uploaded file JSON responses

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

        print(f"\n\n{file_path}\n\n")

        with open(file_path, "rb") as file_obj:
            files = {"file": (file_name, file_obj)}  
            data = {"purpose": "ocr"}

            resp = requests.post(url, headers=headers, files=files, data=data)
            
            if resp.status_code != 200:
                print(f"Upload failed for {file_name}: {resp.status_code} {resp.text}")
                resp.raise_for_status()

            resp_json = resp.json()
            results.append(resp_json)
            print(f"Successfully uploaded {file_name}: {resp_json}")

    state["uploaded"] = results
    return state

def retrieve_signed_url(state: State) -> State:
    """Retrieve signed URLs for uploaded files"""
    signed_urls = []
    for item in state.get("uploaded", []):
        # Example follow-up API call
        url = item.get("signed_url", "mock_url")
        signed_urls.append(url)
    
    state["signed_urls"] = signed_urls
    return state

def ocr_results(state: State) -> State:
    """Fetch OCR results from Mistral"""
    texts = []
    for url in state.get("signed_urls", []):
        # Mock OCR response instead of actual API call
        # resp = requests.get(url)
        # texts.append(resp.text)
        texts.append(f"OCR text from {url}")
    
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