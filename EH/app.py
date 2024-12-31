from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # For flash messages

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
KEY_FILE = "secret.key"

# Ensure necessary folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Generate Key
def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)

# Load Key
def load_key():
    if not os.path.exists(KEY_FILE):
        generate_key()
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()

# Encrypt File
def encrypt_file(file_path, output_path):
    key = load_key()
    fernet = Fernet(key)
    with open(file_path, "rb") as file:
        file_data = file.read()
    encrypted_data = fernet.encrypt(file_data)
    with open(output_path, "wb") as file:
        file.write(encrypted_data)

# Decrypt File
def decrypt_file(file_path, output_path):
    key = load_key()
    fernet = Fernet(key)
    with open(file_path, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    with open(output_path, "wb") as file:
        file.write(decrypted_data)

@app.route("/")
def home():
    files = os.listdir(OUTPUT_FOLDER)  # List files in the output folder
    return render_template("index.html", files=files)

@app.route("/upload", methods=["POST"])
def upload_files():
    if "files" not in request.files:
        flash("No files selected")
        return redirect(request.url)

    files = request.files.getlist("files")
    operation = request.form.get("operation")

    for file in files:
        if file.filename == "":
            continue

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Prepare output filename
        base_name, ext = os.path.splitext(filename)
        if operation == "encrypt":
            output_filename = f"{base_name}_encrypted{ext}"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            encrypt_file(file_path, output_path)
        elif operation == "decrypt":
            output_filename = f"{base_name}_decrypted{ext}"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            decrypt_file(file_path, output_path)
        else:
            flash("Invalid operation")
            return redirect(request.url)

        # Redirect to download the file after processing
        return redirect(url_for("download_file", filename=output_filename))

    flash("No valid files processed.")
    return redirect(url_for("home"))

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

@app.route("/view/<filename>")
def view_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    try:
        with open(file_path, "r") as file:
            content = file.read()
        return render_template("view.html", content=content, filename=filename)
    except Exception:
        flash("Unable to display the file.")
        return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
