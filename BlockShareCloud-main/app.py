
from blockchain import Blockchain
from flask import Flask, request, render_template, send_file, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
from ipfs import IPFSClient
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import bcrypt
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key
ipfs_client = IPFSClient()
blockchain = Blockchain()
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'

# MySQL Config (update to your values)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # your MySQL password
app.config['MYSQL_DB'] = 'projecct'

mysql = MySQL(app)

# Ensure upload and download directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('aboutUs.html')

@app.route('/signup', methods=['POST'])
def signup():
    if 'loggedin' in session:
        return jsonify({'status': 'success'})

    data = request.get_json() or {}
    fullname = data.get('fullname')
    email = data.get('email')
    password = data.get('password')

    if not fullname or not email or not password:
        return jsonify({'status': 'error', 'message': 'Full name, email, and password are required'})

    username = email.split('@')[0]
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'status': 'error', 'message': 'Email already registered'})

    cursor.execute(
        'INSERT INTO users (fullname, email, username, password) VALUES (%s, %s, %s, %s)',
        (fullname, email, username, hashed_pw)
    )
    mysql.connection.commit()
    user_id = cursor.lastrowid

    session['loggedin'] = True
    session['id'] = user_id
    session['username'] = username

    cursor.close()
    return jsonify({'status': 'success'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'loggedin' in session:
            return jsonify({'status': 'success'})

        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'status': 'error', 'message': 'Username and password are required'})

        password = password.encode('utf-8')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            cursor.close()
            return jsonify({'status': 'success'})

        cursor.close()
        return jsonify({'status': 'error', 'message': 'Invalid credentials'})

    if 'loggedin' in session:
        return redirect('/dashboard')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'loggedin' not in session:
        return redirect('/login')

    user_id = session['id']
    
    # Retrieve storage info
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT used_storage, storage_limit FROM user_storage WHERE user_id = %s
    """, (user_id,))
    storage_info = cursor.fetchone()

    used_storage = storage_info['used_storage'] if storage_info else 0
    storage_limit = storage_info['storage_limit'] if storage_info else 1073741824  # 1 GB


    # Get number of uploaded files
    cursor.execute("""
        SELECT COUNT(*) as file_count FROM userfiles WHERE user_id = %s
    """, (user_id,))
    file_count = cursor.fetchone()['file_count']

    cursor.close()

    return render_template('dashboard.html', 
                           username=session['username'], 
                           used_storage=used_storage, 
                           storage_limit=storage_limit,
                           file_count=file_count)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'loggedin' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'Invalid file'}), 400

    user_id = session['id']
    user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))
    os.makedirs(user_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = os.path.join(user_folder, filename)
    file.save(file_path)

    file_size = os.path.getsize(file_path)

    # Calculate current usage
    total_size = 0
    for root, dirs, files in os.walk(user_folder):
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))

    # Check storage limit
    if total_size > 1073741824:  # 1 GB

        os.remove(file_path)
        return jsonify({'error': 'Storage limit exceeded (1GB)'}), 403

    # Upload to IPFS
    ipfs_hash = ipfs_client.upload_file(file_path)

    # Store in Blockchain
    blockchain.create_block(len(blockchain.chain), {
        'file_name': filename,
        'ipfs_hash': ipfs_hash,
        'user_id': user_id
    })

    # Save metadata to DB
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO userfiles (user_id, filename, file_hash, file_size)
        VALUES (%s, %s, %s, %s)
    """, (user_id, filename, ipfs_hash, file_size))
    mysql.connection.commit()

    # Update storage usage in user_storage table
    cursor.execute("""
        SELECT used_storage FROM user_storage WHERE user_id = %s
    """, (user_id,))
    result = cursor.fetchone()

    if result:
        new_used_storage = result['used_storage'] + file_size
        cursor.execute("""
            UPDATE user_storage SET used_storage = %s WHERE user_id = %s
        """, (new_used_storage, user_id))
    else:
        cursor.execute("""
            INSERT INTO user_storage (user_id, used_storage)
            VALUES (%s, %s)
        """, (user_id, file_size))

    mysql.connection.commit()
    cursor.close()

    return jsonify({'message': 'Uploaded successfully', 'hash': ipfs_hash})

@app.route('/download', methods=['POST'])
def download_file():
    ipfs_hash = request.form['ipfs_hash']
    
    # Search for the block with the given IPFS hash to retrieve the original filename
    original_filename = None
    for block in blockchain.chain:
        if block.data.get('ipfs_hash') == ipfs_hash:
            original_filename = block.data.get('file_name')
            break
    
    if original_filename is None:
        return 'Error: IPFS hash not found in the blockchain.'

    # Download the file from IPFS and save it locally in the 'downloads' folder
    file_obj = ipfs_client.download_file(ipfs_hash, DOWNLOAD_FOLDER)
    file_path = os.path.join(DOWNLOAD_FOLDER, ipfs_hash)  # Path where the file was saved

    if not os.path.exists(file_path):
        return f'Error: File {ipfs_hash} not found in local storage!'

    # Rename the downloaded file to its original filename with extension
    final_file_path = os.path.join(DOWNLOAD_FOLDER, original_filename)
    os.rename(file_path, final_file_path)

    # Serve the file for download with the original filename and extension
    return send_file(final_file_path, as_attachment=True, download_name=original_filename)

@app.route('/get-ipfs-url/<file_hash>')
def get_ipfs_url(file_hash):
    # Public IPFS gateway URL for the requested file
    return jsonify({'url': f'https://ipfs.io/ipfs/{file_hash}'})

@app.route('/my-files')
def my_files():
    if 'loggedin' not in session:
        return jsonify([])

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT id, filename, file_hash, upload_date, file_size
        FROM userfiles WHERE user_id = %s
        ORDER BY upload_date DESC
    """, (user_id,))
    files = cursor.fetchall()
    cursor.close()

    return jsonify(files)

@app.route('/stats')
def stats():
    if 'loggedin' not in session:
        return jsonify({'file_count': 0, 'total_used': 0, 'storage_limit': 1073741824, 'remaining': 1073741824})

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT used_storage, storage_limit FROM user_storage WHERE user_id = %s
    """, (user_id,))
    storage_info = cursor.fetchone()

    used_storage = storage_info['used_storage'] if storage_info else 0
    storage_limit = storage_info['storage_limit'] if storage_info else 1073741824
    remaining = max(storage_limit - used_storage, 0)

    cursor.execute("""
        SELECT COUNT(*) AS file_count FROM userfiles WHERE user_id = %s
    """, (user_id,))
    file_count = cursor.fetchone()['file_count']
    cursor.close()

    return jsonify({
        'file_count': file_count,
        'total_used': used_storage,
        'storage_limit': storage_limit,
        'remaining': remaining
    })

@app.route('/delete-file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    if 'loggedin' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT filename, file_size FROM userfiles
        WHERE id = %s AND user_id = %s
    """, (file_id, user_id))
    file_record = cursor.fetchone()

    if not file_record:
        cursor.close()
        return jsonify({'success': False, 'error': 'File not found'}), 404

    filename = file_record['filename']
    file_size = file_record['file_size']
    file_path = os.path.join(UPLOAD_FOLDER, str(user_id), filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    cursor.execute("""
        DELETE FROM userfiles
        WHERE id = %s AND user_id = %s
    """, (file_id, user_id))

    cursor.execute("""
        SELECT used_storage FROM user_storage WHERE user_id = %s
    """, (user_id,))
    storage_info = cursor.fetchone()

    if storage_info:
        new_used_storage = max(storage_info['used_storage'] - file_size, 0)
        cursor.execute("""
            UPDATE user_storage SET used_storage = %s WHERE user_id = %s
        """, (new_used_storage, user_id))

    mysql.connection.commit()
    cursor.close()
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    
    # Redirect to login page (or homepage)
    return redirect(url_for('login'))  # change 'login' to your login route function name
if __name__ == '__main__':
    app.run(debug=True)