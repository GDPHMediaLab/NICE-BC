# Preprocessing Pipeline

This directory contains the preprocessing pipeline for preparing CT images for body composition analysis and treatment response prediction in the NICE-BC workflow.

## Overview

The preprocessing pipeline converts raw DICOM CT scans into standardized, normalized NIfTI images and performs automated body composition segmentation using deep learning models. The pipeline consists of five sequential steps that transform data from its raw format to analysis-ready images with segmentation masks.

## Pipeline Workflow

```
DICOM Files (0_DICOM/)
    ↓
[Step 1] DICOM → NIfTI Conversion
    ↓
NIfTI Images (1_NII/)
    ↓
[Step 2] Resampling & Spatial Standardization
    ↓
Resampled Images (2_Res/)
    ↓
[Step 3] HU Windowing
    ↓
HU Windowed Images (3_HU/)
    ↓
[Step 4] Intensity Normalization
    ↓
Normalized Images (4_Norm/)
    ↓
[Step 5] Body Composition Segmentation
    ↓
Segmentation Masks (5_BC/, 6_Bone/)
```

## Quick Start

1. **Organize your DICOM data**: Place patient DICOM files in subdirectories under `0_DICOM/`
   ```
   0_DICOM/
   ├── patient_001/
   │   ├── slice_001.dcm
   │   ├── slice_002.dcm
   │   └── ...
   ├── patient_002/
   └── ...
   ```

2. **Open the Jupyter notebook**: `pipeline.ipynb`

3. **Run cells sequentially**: Execute each cell in order to process all patients

4. **Check outputs**: Results will be saved in the corresponding output directories

## Detailed Steps
👉 **See [pipeline.ipynb](pipeline.ipynb)** for detailed steps.
