# 🚀 BlockShareCloud  
### Blockchain-Based Decentralized Cloud Storage System

BlockShareCloud is a decentralized cloud file-sharing platform built using **Flask, IPFS, and Blockchain Technology**.  
The system allows users to securely upload, store, and retrieve files using IPFS while maintaining metadata integrity through blockchain-based tracking.

---

## ✨ Features

- 📂 Secure File Upload System
- 🌐 Decentralized Storage using IPFS
- ⛓️ Blockchain-based Metadata Tracking
- 📥 File Download with Original Filename
- 🖥️ Simple and User-Friendly Web Interface
- 🔒 Enhanced Traceability & Integrity

---

## 🛠️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Flask (Python)
- **Storage:** IPFS
- **Blockchain:** Custom Lightweight Blockchain
- **Environment:** Python Virtual Environment

---

# ⚙️ Installation & Setup

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/BlockShareCloud.git
cd BlockShareCloud
```

---

## 2️⃣ Create Virtual Environment

### For macOS/Linux
```bash
python -m venv venv
source venv/bin/activate
```

### For Windows
```bash
python -m venv venv
venv\Scripts\activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Create Required Directories

```bash
mkdir uploads downloads
```

---

## 5️⃣ Start IPFS Daemon

Make sure IPFS is installed and running.

```bash
ipfs daemon
```

---

## 6️⃣ Run the Application

```bash
python app.py
```

---

## 7️⃣ Open in Browser

```bash
http://127.0.0.1:5000/
```

---

# 🔄 How It Works

## 📤 File Upload Process

1. User uploads a file through the web interface.
2. File gets temporarily stored in the `uploads` folder.
3. File is uploaded to IPFS.
4. IPFS generates a unique hash.
5. File metadata and hash are stored on the blockchain.

---

## ⛓️ Blockchain Functionality

- Stores:
  - File Name
  - IPFS Hash
- Ensures:
  - Data Integrity
  - Traceability
  - Verification

---

## 📥 File Download Process

1. User enters the IPFS hash.
2. File is fetched from IPFS.
3. Metadata is verified using blockchain records.
4. Original file is downloaded with correct extension and filename.

---

# 📸 Example Workflow

## Uploading Files

- Open the web application
- Upload a file
- Receive generated IPFS hash

## Downloading Files

- Enter IPFS hash
- Retrieve original file securely

---

# 📌 Important Notes

- Ensure IPFS daemon is running locally on port `5001`
- Blockchain implementation is currently in-memory
- Blockchain data resets after server restart

---

# 🔮 Future Improvements

- User Authentication System
- Persistent Blockchain Database
- File Encryption
- Cloud Deployment
- Smart Contract Integration
- Multi-user Access Control

---

# 👨‍💻 Author

### Kapil Ugale

---

# 📜 License

This project is licensed under the MIT License.

---

# ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.
