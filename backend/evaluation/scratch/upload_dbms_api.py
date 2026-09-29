import requests
from pathlib import Path

def sync_dev_user():
    print("\n--- Syncing Dev User ---")
    res_login = requests.post("http://localhost:8000/auth/dev-login")
    token = res_login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Check current docs
    res = requests.get("http://localhost:8000/documents", headers=headers)
    print("Current docs:", res.json())

    # 2. Delete NCERT if present
    res_del = requests.delete("http://localhost:8000/documents/NCERT-Class-11-Physics-Part-1.pdf", headers=headers)
    print("Delete NCERT response:", res_del.json())

    # 3. Check if DBMS_Full_Notes is already in documents
    current_list = res.json().get("documents", [])
    if "DBMS_Full_Notes.pdf" not in current_list:
        pdf_path = Path("backend/documents/dev@example.com/DBMS_Full_Notes.pdf")
        if not pdf_path.exists():
            pdf_path = Path("C:/Users/Sumant Kumar/Downloads/DBMS_Full_Notes.pdf")

        print(f"Uploading {pdf_path.name} ({pdf_path.stat().st_size} bytes)...")
        with open(pdf_path, "rb") as f:
            files = [("files", (pdf_path.name, f, "application/pdf"))]
            res_upload = requests.post("http://localhost:8000/documents", headers=headers, files=files)
            print("Upload result:", res_upload.json())

    res_final = requests.get("http://localhost:8000/documents", headers=headers)
    print("Final active docs for dev@example.com:", res_final.json())

if __name__ == "__main__":
    sync_dev_user()
