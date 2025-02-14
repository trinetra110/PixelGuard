# **PixelGuard: Image Tampering Detection Tool** 🛡️🔍  

<img src="https://readme-typing-svg.herokuapp.com?color=45ffaa&size=40&width=900&height=80&lines=Welcome-to-PixelGuard"/>

**PixelGuard** is a powerful Python-based tool designed to detect image tampering using **SHA-256 hashing, metadata analysis, and pixel-level comparison**. It helps verify the authenticity of images and identify unauthorized modifications, making it useful for **digital forensics, cybersecurity, and content verification**.  

🔹 **Verifies image integrity using cryptographic hashing**  
🔹 **Detects changes in metadata and file properties**  
🔹 **Performs pixel-level comparison to identify modifications**  

## 🚀 Features  

✅ **SHA-256 Hashing**: Generates unique hashes to verify image integrity.  
✅ **Metadata Analysis**: Extracts format, dimensions, and file size for validation.  
✅ **Pixel-Level Comparison**: Detects subtle changes in image content.  
✅ **User-Friendly CLI**: Simple interactive command-line interface.  
✅ **Supports Multiple Formats**: Works with **JPG, PNG, BMP, and WEBP** images.  

## 🛠️ Tech Stack  

| **Technology**  | **Description**              |
|---------------|--------------------------|
| **🐍 Python**  | Programming Language       |
| **📷 Pillow**  | Image Processing Library   |
| **🔑 hashlib** | Cryptographic Hashing      |
| **📂 OS**      | File Handling Utilities    |

## 📌 Prerequisites  

- **Python 3.x** (Download: [Python.org](https://www.python.org/downloads/))  

## ⚡ Installation & Usage  

### **1️⃣ Clone the Repository**  
```bash
git clone https://github.com/yourusername/PixelGuard.git
cd PixelGuard
```

### **2️⃣ Install Dependencies**  
```bash
pip install -r requirements.txt
```

### **3️⃣ Run the Application**  
```bash
python main.py
```

## 🎯 How to Use  

When you run **PixelGuard**, you will see the following menu:  

```
📌 Select an option:
1️⃣  Generate a hash for an original image
2️⃣  Compare a suspect image with a stored hash
3️⃣  Compare two images (original and suspect)
0️⃣  Exit
```

### **1️⃣ Generate a Hash for an Original Image**  
- Select option `1`.  
- Enter the filename (ensure the image is in the `images/` directory).  
- The tool will compute a **SHA-256 hash** and display it.  
- **Save this hash** securely for future verification.  

### **2️⃣ Compare a Suspect Image with a Stored Hash**  
- Select option `2`.  
- Enter the suspect image filename (ensure the image is in the `images/` directory).  
- Provide the stored hash of the original image.  
- The tool will compare the hashes and detect any tampering.  

### **3️⃣ Compare Two Images (Original vs. Suspect)**  
- Select option `3`.  
- Enter both filenames (original and suspect) (ensure the images are in the `images/` directory).  
- The tool performs:  
  ✅ **Metadata Analysis** (format, dimensions, file size)  
  ✅ **Hash Comparison** (SHA-256 integrity check)  
  ✅ **Pixel-Level Analysis** (detects modified pixels)  

## 🔄 Supported File Formats  
PixelGuard supports the following image formats:  

- **JPG** (`.jpg`, `.jpeg`)  
- **PNG** (`.png`)  
- **BMP** (`.bmp`)  
- **WEBP** (`.webp`)  

## 🏆 Why Use PixelGuard?  

🔹 **Ensure Image Authenticity**: Detect unauthorized modifications in digital images.  
🔹 **Ideal for Digital Forensics**: Helps cybersecurity professionals verify media integrity.  
🔹 **Fast & Lightweight**: Works efficiently on local machines.  

## 📜 License  

This project is licensed under the **MIT License**.  
