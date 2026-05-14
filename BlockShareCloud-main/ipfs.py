import requests
import os

class IPFSClient:
    def __init__(self, api_url="http://127.0.0.1:5001/api/v0"):
        self.api_url = api_url  # IPFS API endpoint

    def upload_file(self, file_path):
        """Uploads a file to IPFS and returns its hash."""
        with open(file_path, "rb") as file:
            files = {"file": file}
            response = requests.post(f"{self.api_url}/add", files=files)
            if response.status_code == 200:
                return response.json()["Hash"]
            else:
                raise Exception(f"Error uploading file: {response.text}")

    def download_file(self, ipfs_hash, download_folder):
        """Downloads a file from IPFS and saves it in the specified folder."""
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

        file_path = os.path.join(download_folder, ipfs_hash)
        response = requests.get(f"https://ipfs.io/ipfs/{ipfs_hash}", stream=True)

        if response.status_code == 200:
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            return file_path
        else:
            raise Exception(f"Error downloading file: {response.text}")
