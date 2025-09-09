from langgraph.graph import StateGraph
import requests
from typing import TypedDict, List, Any, Dict
from utils.fetchName import fetchNameAndIds
import os

class State(TypedDict):
    files: List[str] ## contain file_names
    files_id: List[str] ## contain file_ids
    downloaded_files: List[str] ## contain local file paths

def start_node(state: State) -> State:
    file_names, file_ids = fetchNameAndIds()
    state["files"] = file_names
    state["files_id"] = file_ids
    return state


def download_file(state: Dict[str, Any]) -> Dict[str, Any]:
    """Download file from Drive"""
    file_ids = state.get("files_id", [])
    files = state.get("files", [])
    downloaded = []
    
    for file_id, file_name in zip(file_ids, files):
        # Download file from Google Drive using file_id
        print(f"Downloading file: {file_name}")
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        local_path = os.path.join("downloads", file_name)
        
        # Ensure "downloads" directory exists
        os.makedirs("downloads", exist_ok=True)
        
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        downloaded.append(local_path)
        print(f"Successfully downloaded: {file_name}")

    state["downloaded_files"] = downloaded
    return state

def upload_to_mistral(state: State) -> State:
    """Upload each file to Mistral server"""
    results = []
    for f in state.get("downloaded_files", []):
        # Example API request (commented out to avoid actual API calls)
        # resp = requests.post(
        #     "https://api.mistral.ai/v1/upload",
        #     files={"file": open(f, "rb")}
        # )
        # results.append(resp.json())
        
        # Mock response for testing
        results.append({"file_id": f"mock_id_{f}", "signed_url": f"mock_url_{f}"})
    
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