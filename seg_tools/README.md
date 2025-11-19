# Training Instructions

## Installation

First, you need to install the nnU-Net library. Follow the official installation instructions:
https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/installation_instructions.md

## Dataset Structure

The training dataset should be organized according to nnU-Net requirements. For detailed structure specifications, please refer to:
https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/dataset_format.md

For concrete examples, see the `dataset.json` files in the `train` folder:
- `Dataset001_BodyComposition/dataset.json` - Body composition segmentation dataset
- `Dataset002_SpineSeg/dataset.json` - Spine segmentation dataset

## Model Architecture and Configuration

### 1. Spine Localization
- **Purpose**: Spine localization only (not detailed segmentation)
- **Architecture**: nnUNetv2 `3d_lowres`
- **Inference settings**: 
  - `step_size=1` (no overlap in sliding window)
  - Reduces prediction time and GPU memory usage
  - Meets clinical requirements
- **Resampling**: No prediction-based resampling (same as published results)

### 2. Body Composition Segmentation
- **Purpose**: Precise segmentation of body composition components
- **Architecture**: nnUNetv2 `3d_fullres`
- **Inference settings**:
  - `step_size=0.5` (50% overlap in sliding window)
  - Provides more accurate results

## Training Commands

### For Spine Localization (Dataset001_SpineSeg):
```bash
python nnunetv2/run/run_training.py \
    --dataset_name_or_id Dataset001_SpineSeg \
    --configuration 3d_lowres \
    --fold 0
```

### For Body Composition Segmentation (Dataset002_BodyComposition):
```bash
python nnunetv2/run/run_training.py \
    --dataset_name_or_id Dataset002_BodyComposition \
    --configuration 3d_fullres \
    --fold 0
```

**Note**: The `--fold` parameter specifies which fold of the 5-fold cross-validation to train (0-4). You can train all folds by running the command with `--fold 0`, `--fold 1`, etc.

## Inference Commands

### For Spine Localization (Dataset001_SpineSeg):
```bash
python nnunetv2/inference/predict_from_raw_data.py \
    -i INPUT_FOLDER \
    -o OUTPUT_FOLDER \
    -d Dataset001_SpineSeg \
    -c 3d_lowres \
    -f 0 \
    --step_size 1
```

### For Body Composition Segmentation (Dataset002_BodyComposition):
```bash
python nnunetv2/inference/predict_from_raw_data.py \
    -i INPUT_FOLDER \
    -o OUTPUT_FOLDER \
    -d Dataset002_BodyComposition \
    -c 3d_fullres \
    -f 0 \
    --step_size 0.5
```

**Parameters**:
- `-i INPUT_FOLDER`: Path to folder containing input images
- `-o OUTPUT_FOLDER`: Path to folder where predictions will be saved
- `-d`: Dataset name
- `-c`: Configuration (3d_lowres or 3d_fullres)
- `-f`: Fold number (0-4)
- `--step_size`: Sliding window step size
  - `1.0` = no overlap (faster, lower memory, for spine localization)
  - `0.5` = 50% overlap (more accurate, for body composition)

For detailed usage instructions, please refer to:
https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/how_to_use_nnunet.md

## Notes

- The source code model architecture has not been modified from the original nnU-Net
- After obtaining labels, localization follows the standard format (spine_seg, etc.)
- Training data structure is fully consistent with nnU-Net requirements
