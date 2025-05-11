import requests
import os

# API base URL
api_url = "http://localhost:8000"
api_key = "default_api_key_change_me"  # Default key from config.py

# Path to test_doc.pdf
pdf_path = os.path.join(os.path.dirname(__file__), "test_doc.pdf")

# Check if file exists
if not os.path.exists(pdf_path):
    print(f"Error: File not found at {pdf_path}")
    exit(1)

print(f"Uploading file: {pdf_path}")

# Upload the document
try:
    files = {'file': open(pdf_path, 'rb')}
    data = {'doc_type': 'Financial Report', 'company': 'Example Corp'}
    
    response = requests.post(
        f"{api_url}/upload-document/",
        files=files,
        data=data,
        params={'api_key': api_key}
    )
    
    if response.status_code == 200:
        print("Success!")
        result = response.json()
        print(f"Response: {result}")
        
        # Get document ID to check status later
        document_id = result.get('document_id')
        
        # Query document insights after a short delay
        if document_id:
            print(f"Document ID: {document_id}")
            print("To check document insights, run:")
            print(f"requests.get('{api_url}/documents/{document_id}', params={{'api_key': '{api_key}'}}).json()")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {str(e)}")
