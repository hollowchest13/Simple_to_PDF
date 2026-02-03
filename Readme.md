# Simple_to_PDF 📄🚀

<<<<<<< HEAD
## ⬇️ Download

- 🪟 **Windows**: [Download .exe](https://github.com/hollowchest13/Simple_to_PDF/releases/download/v1.0.1/SimpleToPDF.exe)

- 🐧 **Linux**: [Download AppImage](https://github.com/hollowchest13/Simple_to_PDF/releases/download/v1.0.1/SimpleToPDF)

👉 No Python required. Just download & run.

## 📄 License
=======
## License
>>>>>>> b5ff0f1 (Toml setup)
MIT License

## Screenshots

<p align="center">
  <img src="screenshots/main.png" alt="Main Window" width="600">
  <br>
  <em>Main application window interface</em>
</p>

<p align="center">
  <img src="screenshots/extract.png" alt="PDF Extraction" width="600">
  <br>
  <em>Process of extracting pages from PDF</em>
</p>

**Simple_to_PDF** is a lightweight, local multi-format converter that allows you to merge various file types into a single PDF or extract pages with just one click.

The project is built for **Linux (Mint, Ubuntu)** and **Windows** users, providing an intuitive Graphical User Interface (GUI) for complex file processing.

## Known Limitations
- Does not support spreadsheet files with chart sheets.
- Password-protected PDFs are not supported
- Very large files (>500MB) may require additional memory
- MS Office automation works only on Windows

## Requirements

1. **Microsoft Office** (Windows only) — detected automatically via COM interface.
2. **LibreOffice** (Windows or Linux) — Used as a fallback or primary engine.

**Note for Windows users:** If you prefer LibreOffice, please ensure it is installed in one of the default locations:

 - `C:\Program Files\LibreOffice`
 - `C:\Program Files (x86)\LibreOffice`

The application dynamically adapts to the software installed on your system. For full office document support, **MS Office** or **LibreOffice** is required.

### 1. MS Office Mode (Windows)
* **Documents:** .doc, .docx, .docm, .rtf, .txt
* **Tables:** .xls, .xlsx, .xlsm, .xlsb
* **Presentations:** .ppt, .pptx, .pptm, .pps, .ppsx

### 2. LibreOffice Mode (Linux / Windows)
* **Documents:** .doc, .docx, .odt, .rtf, .txt
* **Tables:** .xls, .xlsx, .xlsm, .xltx, .xltm, .xlsb, .ods, .csv
* **Presentations:** .ppt, .pptx, .odp

### 3. Standalone Mode (No Office Required)
If no office suite is detected, the app functions as a robust image-to-PDF converter and PDF editor:
* **PDF:** .pdf (merging and page extraction)
* **Images:** .jpg, .jpeg, .png, .bmp, .gif, .tiff, .tif, .webp, .ppm, .icns, .ico, .jfif, .jpe, .tga

## How to use:

Download the version compatible with your operating system using the link provided.

**Windows**: [Download Simple_to_PDF.exe](https://github.com/hollowchest13/Simple_to_PDF/releases/download/v1.0.1/SimpleToPDF.exe)

 **Linux**: [Download Simple_to_PDF](https://github.com/hollowchest13/Simple_to_PDF/releases/download/v1.0.1/SimpleToPDF)

Once downloaded, run the program.

**To merge files**: First, click the plus (+) button on the right side of the window, select the files you need, and press "Open." Then, go to the File menu and click "Merge to PDF."

**To extract pages**: Go to the File menu and choose "Extract Pages." Select the PDF file you want to process and click "Open." Enter the page numbers you wish to extract, click "OK," and then select the destination folder where you want to save the result.

If you want to run the script yourself, check the [Installation section](#installation).

## Installation

### Clone the Repository
```bash
git clone [https://github.com/hollowchest13/Simple_to_PDF.git](https://github.com/hollowchest13/Simple_to_PDF.git)
cd Simple_to_PDF
```
## Environment Setup

### For Linux (Ubuntu / Mint):
1. **Install system dependencies:**

```bash
sudo apt update
sudo apt install python3-venv python3-tk
```
2. **Create and activate environment:**

```bash
python3 -m venv venv
source venv/bin/activate
```
3. **Install requirements:**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```
### For Windows:
1. Create virtual environment in **PowerShell** or **CMD**:

```bash
python -m venv venv
```
In **CMD**:

```bash
venv\Scripts\activate
```
3. Install requirements:

```bash
pip install -r requirements.txt
```
---
4. Getting Started:

```bash
python -m src.simple_to_pdf.cli
```

## Support
If you encounter any issues or the program behaves unexpectedly:

1. Go to the **Help** menu in the top bar.
2. Choose **Show Logs**.
3. A window will open showing the real-time application history. 

Send the logs along with a short description of what happened to:

📧 **hollowchest13@gmail.com**