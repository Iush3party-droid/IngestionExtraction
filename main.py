from langgraph.graph import StateGraph
import requests
from nodes.state import State
from nodes.start_node import start_node

def search_files(state: State) -> State:
    """Search files in Google Drive (placeholder)"""
    # TODO: integrate Google Drive API
    found_files = ["fileA.pdf", "fileB.pdf"]
    return {"files": found_files}

def download_file(state: State) -> State:
    """Download file from Drive"""
    files = state.get("files", [])
    downloaded = [f"local/{f}" for f in files]  # placeholder paths
    return {"downloaded_files": downloaded}

def upload_to_mistral(state: State) -> State:
    """Upload each file to Mistral server"""
    results = []
    for f in state.get("downloaded_files", []):
        # Example API request
        resp = requests.post(
            "https://api.mistral.ai/v1/upload",
            files={"file": open(f, "rb")}
        )
        results.append(resp.json())
    return {"uploaded": results}

def retrieve_signed_url(state: State) -> State:
    """Retrieve signed URLs for uploaded files"""
    signed_urls = []
    for item in state.get("uploaded", []):
        # Example follow-up API call
        url = item.get("signed_url", "mock_url")
        signed_urls.append(url)
    return {"signed_urls": signed_urls}

def ocr_results(state: State) -> State:
    """Fetch OCR results from Mistral"""
    texts = []
    for url in state.get("signed_urls", []):
        resp = requests.get(url)
        texts.append(resp.text)
    return {"ocr_texts": texts}

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
        result = app.invoke({})
        print("Workflow completed successfully!")
        print("OCR Texts:", result.get("ocr_texts"))
        print("Files found:", result.get("files"))
    except Exception as e:
        print(f"Workflow failed with error: {e}")
        import traceback
        traceback.print_exc()
