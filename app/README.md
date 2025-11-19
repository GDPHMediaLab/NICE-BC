# NICE-BC Application Usage Guide

## Installation Methods

### Method 1: Running from Source Code

After cloning the repository (see main README), run NICE-BC with:

```bash
cd NICE-BC/app
conda create -n nice_bc python=3.12
conda activate nice_bc
pip install -r requirements.txt
python main.py
```

### Method 2: Binary Release

For convenience, we provide pre-compiled binary packages for different operating systems. You can download the appropriate binary for your system from the [Releases](https://github.com/GDPHMediaLab/NICE-BC/releases) page:

- **Windows**: Download `NICE-BC_windows_amd64.zip`
- **Linux**: Download `NICE-BC_linux_amd64.tar.gz`
<!-- - **macOS**: Download `NICE-BC_macos_arm64.dmg` -->

After downloading, simply run the executable file directly without any additional installation steps.

## Demo Data

📁 **Sample data for testing NICE-BC is available for download:**

You can access demo CT scan data from our Google Drive repository:
- **Demo Data**: [Download from Google Drive](https://drive.google.com/drive/folders/12DTHqoDiSDCMGts-JZBuBqF69wbH21YC?usp=sharing)

The demo data includes sample DICOM files that you can use to test the body composition analysis functionality.

## Output Folders and Results Management

When you run NICE-BC, the software automatically creates two folders in the same directory as the executable:

### 📂 Generated Folders:
- **`cache/`**: Stores temporary processing files and intermediate results
- **`results/`**: Contains the final analysis outputs, segmentation masks, and reports

### 📍 Platform-specific Locations:

**Windows:**
```
# If executable file is C:\Users\YourName\Downloads\NICE-BC_windows_amd64\NICE-BC.exe
# Generated folders will be at:
C:\Users\YourName\Downloads\NICE-BC_windows_amd64\cache\
C:\Users\YourName\Downloads\NICE-BC_windows_amd64\results\
```

**Linux:**
```bash
# If executable file is /home/username/NICE-BC_linux_amd64/NICE-BC
# Generated folders will be at:
/home/username/NICE-BC_linux_amd64/cache/
/home/username/NICE-BC_linux_amd64/results/
```

<!-- **macOS:**
```bash
# If executable file is /Users/username/Applications/NICE-BC.app
# Generated folders will be at:
/Users/username/Applications/cache/
/Users/username/Applications/results/
``` -->

### 📋 Viewing Results:
- **Segmentation outputs**: Check the `results/` folder for DICOM files with segmented body composition masks
- **Analysis reports**: Look for CSV files and summary reports in the `results/` folder
- **Volume measurements**: Body composition metrics (SMVI, SAVI, VAVI, IMVI) will be saved as spreadsheet files

### 🗑️ Cleaning Up Results:
To remove all generated files and start fresh:

**Windows (Command Prompt):**
```cmd
rmdir /s cache
rmdir /s results
```

**Linux/macOS (Terminal):**
```bash
rm -rf cache/
rm -rf results/
```

Or simply delete the `cache` and `results` folders manually through your file manager.

---

**Note**: For information about AutoPanoM model access, please refer to the main [README.md](../README.md).
