# Real-Time Face Verification System (Face Recognition)

A clean, high-performance OpenCV-based face detection and verification application that loads known profiles, detects faces using Haar Cascade classifiers, and checks test samples for matches.

## 🚀 Features

- **📂 Multi-Directory Profile Scanning**:
  - Automatically loads profile reference photos from a `fotograflar/` directory.
  - Automatically scans test subjects from a `yuz_tanima/` directory.
- **🔍 Cascade-Classifier Powered Detection**: Uses OpenCV's optimized `haarcascade_frontalface_default.xml` model for robust real-time face localization.
- **⚡ Spatial Feature Comparison**: Analyzes detected face bounding box aspect ratios and dimensional metrics to establish identity matching with minimal overhead.
- **🛠️ Self-Structuring Design**: Automatically creates directory architecture on first launch.

## 📁 Project Structure

- `yuz_tanima.py`: Main face scanning, detection, and feature comparison controller.
- `/fotograflar`: Source folder containing known user profiles (reference images).
- `/yuz_tanima`: Test folder containing subject images to verify.

## 🛠️ Tech Stack

- **Core Library**: `OpenCV (cv2)`
- **Platform**: Python 3.11
- **File System**: Python standard `os` library

## ⚙️ Installation & Usage

1. **Clone the repository**:
   ```bash
   git clone <your-repository-url>
   cd face-recognition-system
   ```

2. **Install dependencies**:
   ```bash
   pip install opencv-python
   ```

3. **Prepare folders**:
   - Run the script once to automatically generate folders, or manually create:
     - `fotograflar/` (Add pictures of known people with their names as filenames, e.g. `john.jpg`)
     - `yuz_tanima/` (Add mystery or test photos to check)

4. **Run the system**:
   ```bash
   python yuz_tanima.py
   ```

---

*Designed and developed with 💙 by Emirhan Kaya.*
