from langgraph.graph import StateGraph
import requests
from typing import Dict, Any, TypedDict, List
from utils.fetchName import fetchName

class State(TypedDict):
    files: List[str] ## may contain file_names and file_ids

def start_node(state: State) -> State:
    file_names = fetchName()
    state["files"] = List[file_names]
    return state

def search_files(state: State) -> State:
    """Search files in Google Drive (placeholder)"""
    found_files = state.get("files")
    state["files"] = found_files
    return state

def download_file(state: State) -> State:
    """Download file from Drive"""
    files = state.get("files", [])
    downloaded = [f"local/{f}" for f in files]  # placeholder paths
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
workflow.add_node("search_files", search_files)
workflow.add_node("download", download_file)
workflow.add_node("upload", upload_to_mistral)
workflow.add_node("signed_url", retrieve_signed_url)
workflow.add_node("ocr", ocr_results)

workflow.set_entry_point("start")
workflow.add_edge("start", "search_files")
workflow.add_edge("search_files", "download")
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