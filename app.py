import os
import json
import subprocess
import sys
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

UPLOAD_FOLDER = os.path.abspath("./input_files")
RESULTS_FOLDER = os.path.abspath("./AnalysisResults")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/<analysis_type>-analysis", methods=["GET", "POST"])
def analysis_route(analysis_type):
    valid_types = ["image", "audio", "video", "combined"]
    if analysis_type not in valid_types:
        return jsonify({"error": "Invalid analysis type."}), 400

    return handle_file_upload(analysis_type) if request.method == "POST" else render_template(f"{analysis_type}_analysis.html")

@app.route("/get_analysis_result/<filename>", methods=["GET"])
def get_analysis_result(filename):
    result_path = os.path.join(RESULTS_FOLDER, f"{filename}_analysis.json")
    print(f"🔍 Looking for result at: {result_path}")

    if os.path.exists(result_path):
        with open(result_path, "r") as result_file:
            data = json.load(result_file)
            print(" Result found and loaded.")
            return jsonify(data)
    print("❌ Analysis result not found.")
    return jsonify({"error": "Analysis result not found."}), 404

def handle_file_upload(analysis_type):
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        filename = file.filename.strip()
        if not filename:
            return jsonify({"error": "Invalid file name."}), 400

        valid_extensions = {
            "image": [".png", ".jpg", ".jpeg"],
            "audio": [".wav", ".mp3"],
            "video": [".mp4"],
            "combined": [".mp4"]
        }

        if not any(filename.lower().endswith(ext) for ext in valid_extensions[analysis_type]):
            return jsonify({"error": f"Invalid file type for {analysis_type} analysis."}), 400

        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        flag_map = {"image": "-IA", "audio": "-AA", "video": "-VA", "combined": "-CA"}

        # ✅ Updated subprocess with proper environment and working directory
        process = subprocess.run(
            [sys.executable, "run.py", flag_map[analysis_type], filename],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )       

        if process.returncode != 0:
            return jsonify({"error": "Analysis failed.", "details": process.stderr}), 500

        result_filename = f"{os.path.splitext(filename)[0]}_analysis.json"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)

        if not os.path.exists(result_path):
            return jsonify({"error": "Analysis result not found."}), 404

        with open(result_path, "r") as result_file:
            data = json.load(result_file)


            return jsonify(data)

    except Exception as e:
        # 🪲 Detailed error logging
        print(f"Server error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)