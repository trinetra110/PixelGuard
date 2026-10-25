import os
import io
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image
from forensics import (
    compute_file_hash,
    extract_metadata_from_image,
    generate_tamper_diff,
    image_to_base64
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max image upload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_IMAGES_DIR = os.path.join(BASE_DIR, 'test_images')
IMAGES_DIR = os.path.join(BASE_DIR, 'images')

os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sample/<path:filename>')
def serve_sample(filename):
    return send_from_directory(TEST_IMAGES_DIR, filename)

@app.route('/api/samples', methods=['GET'])
def get_samples():
    """Return available sample images for immediate testing."""
    samples = []
    if os.path.exists(TEST_IMAGES_DIR):
        for f in os.listdir(TEST_IMAGES_DIR):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
                file_path = os.path.join(TEST_IMAGES_DIR, f)
                try:
                    with Image.open(file_path) as img:
                        samples.append({
                            "filename": f,
                            "url": f"/sample/{f}",
                            "format": img.format,
                            "dimensions": f"{img.width}x{img.height}",
                            "size": os.path.getsize(file_path)
                        })
                except Exception:
                    continue
    return jsonify({"samples": samples})

@app.route('/api/hash', methods=['POST'])
def api_hash():
    """Option 1: Generate SHA-256 hash & metadata for an image."""
    file = request.files.get('image')
    sample_name = request.form.get('sample_name')

    if not file and not sample_name:
        return jsonify({"error": "No image file provided"}), 400

    try:
        if file:
            img_bytes = file.read()
            filename = file.filename
        else:
            sample_path = os.path.join(TEST_IMAGES_DIR, sample_name)
            with open(sample_path, "rb") as sf:
                img_bytes = sf.read()
            filename = sample_name

        file_size = len(img_bytes)
        sha256_hash = compute_file_hash(img_bytes)

        with Image.open(io.BytesIO(img_bytes)) as img:
            metadata = extract_metadata_from_image(img, file_size=file_size)
            # Create a thumbnail preview
            img_copy = img.copy()
            img_copy.thumbnail((400, 400))
            preview_b64 = f"data:image/png;base64,{image_to_base64(img_copy, 'PNG')}"

        return jsonify({
            "success": True,
            "filename": filename,
            "sha256": sha256_hash,
            "metadata": metadata,
            "preview": preview_b64
        })

    except Exception as e:
        return jsonify({"error": f"Failed to process image: {str(e)}"}), 500

@app.route('/api/verify', methods=['POST'])
def api_verify():
    """Option 2: Compare a suspect image against a stored hash."""
    file = request.files.get('image')
    sample_name = request.form.get('sample_name')
    stored_hash = request.form.get('stored_hash', '').strip().lower()

    if (not file and not sample_name) or not stored_hash:
        return jsonify({"error": "Suspect image and stored hash are required"}), 400

    try:
        if file:
            img_bytes = file.read()
            filename = file.filename
        else:
            sample_path = os.path.join(TEST_IMAGES_DIR, sample_name)
            with open(sample_path, "rb") as sf:
                img_bytes = sf.read()
            filename = sample_name

        calculated_hash = compute_file_hash(img_bytes).lower()
        is_match = (calculated_hash == stored_hash)

        with Image.open(io.BytesIO(img_bytes)) as img:
            metadata = extract_metadata_from_image(img, file_size=len(img_bytes))
            img_copy = img.copy()
            img_copy.thumbnail((400, 400))
            preview_b64 = f"data:image/png;base64,{image_to_base64(img_copy, 'PNG')}"

        return jsonify({
            "success": True,
            "filename": filename,
            "is_authentic": is_match,
            "calculated_hash": calculated_hash,
            "stored_hash": stored_hash,
            "metadata": metadata,
            "preview": preview_b64,
            "status_text": "Authentic / Tamper-Free" if is_match else "Tampering Detected / Hash Mismatch"
        })

    except Exception as e:
        return jsonify({"error": f"Verification failed: {str(e)}"}), 500

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """Option 3: Deep forensic comparison between original and suspect images."""
    orig_file = request.files.get('original_image')
    orig_sample = request.form.get('original_sample')

    susp_file = request.files.get('suspect_image')
    susp_sample = request.form.get('suspect_sample')

    if (not orig_file and not orig_sample) or (not susp_file and not susp_sample):
        return jsonify({"error": "Both original and suspect images are required"}), 400

    try:
        # Load Original
        if orig_file:
            orig_bytes = orig_file.read()
            orig_name = orig_file.filename
        else:
            orig_path = os.path.join(TEST_IMAGES_DIR, orig_sample)
            with open(orig_path, "rb") as sf:
                orig_bytes = sf.read()
            orig_name = orig_sample

        # Load Suspect
        if susp_file:
            susp_bytes = susp_file.read()
            susp_name = susp_file.filename
        else:
            susp_path = os.path.join(TEST_IMAGES_DIR, susp_sample)
            with open(susp_path, "rb") as sf:
                susp_bytes = sf.read()
            susp_name = susp_sample

        # Compute Hashes
        orig_hash = compute_file_hash(orig_bytes)
        susp_hash = compute_file_hash(susp_bytes)
        hash_match = (orig_hash == susp_hash)

        # Open Images with PIL
        with Image.open(io.BytesIO(orig_bytes)) as img_orig, Image.open(io.BytesIO(susp_bytes)) as img_susp:
            orig_meta = extract_metadata_from_image(img_orig, len(orig_bytes))
            susp_meta = extract_metadata_from_image(img_susp, len(susp_bytes))

            # Compare metadata
            metadata_diff = {}
            for key in ["format", "dimensions", "file_size_formatted"]:
                if orig_meta.get(key) != susp_meta.get(key):
                    metadata_diff[key] = {
                        "original": orig_meta.get(key),
                        "suspect": susp_meta.get(key)
                    }

            metadata_matches = len(metadata_diff) == 0

            # Generate previews
            orig_preview = f"data:image/png;base64,{image_to_base64(img_orig.copy(), 'PNG')}"
            susp_preview = f"data:image/png;base64,{image_to_base64(img_susp.copy(), 'PNG')}"

            # Pixel comparison
            pixel_report = generate_tamper_diff(img_orig, img_susp)

        # Overall verdict
        if hash_match and metadata_matches and not pixel_report.get("has_tampering", False):
            verdict = "AUTHENTIC"
            verdict_desc = "Images are bit-for-bit identical. No tampering detected."
            verdict_badge = "success"
        elif not metadata_matches and hash_match:
            verdict = "SUSPICIOUS"
            verdict_desc = "Metadata differences detected despite matching file hash."
            verdict_badge = "warning"
        elif not pixel_report.get("has_tampering", False) and not hash_match:
            verdict = "METADATA_ALTERED"
            verdict_desc = "Visual content appears identical, but file hash differs (metadata/header alteration)."
            verdict_badge = "warning"
        else:
            verdict = "TAMPERED"
            verdict_desc = f"Visual tampering detected! {pixel_report.get('modified_pixel_count', 0)} pixel(s) altered."
            verdict_badge = "danger"

        return jsonify({
            "success": True,
            "verdict": verdict,
            "verdict_desc": verdict_desc,
            "verdict_badge": verdict_badge,
            "original": {
                "filename": orig_name,
                "sha256": orig_hash,
                "metadata": orig_meta,
                "preview": orig_preview
            },
            "suspect": {
                "filename": susp_name,
                "sha256": susp_hash,
                "metadata": susp_meta,
                "preview": susp_preview
            },
            "metadata_matches": metadata_matches,
            "metadata_diff": metadata_diff,
            "hash_matches": hash_match,
            "pixel_report": pixel_report
        })

    except Exception as e:
        return jsonify({"error": f"Comparison failed: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🛡️ PixelGuard Web running on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=True)
