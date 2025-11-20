# Neoadjuvant Immuno-ChEmotherapy predictor based on Body Composition (NICE-BC)
## Clinical Demand
Existing tumor-intrinsic biomarkers incompletely predict pathological complete response (pCR) following neoadjuvant immunochemotherapy (NICT) in patients with non–small-cell lung cancer (NSCLC). Although body composition may influence immunometabolic status, whether three-dimensional CT–derived body composition metrics can serve as complementary and potentially feasible predictors of pCR remains unclear. To evaluate association of three-dimensional CT–derived body composition quantification with pCR in patients receiving NICT for NSCLC. Automated, three-dimensional CT–derived dynamic body composition quantification, particularly baseline skeletal muscle and subcutaneous adipose tissue volumes and their longitudinal changes during NICT, are independently associated with pCR in NSCLC. Incorporating these modifiable imaging-based body composition biomarkers into predictive models significantly improves performance beyond that achieved with clinical variables alone.

This repository is for the research study *"AI-Based 3D Body Composition Biomarkers Improve Pathologic Response Prediction in NSCLC Treated with Neoadjuvant Immunochemotherapy".* The research artcile is under submission for now.

### Key Features

We summarize the key contributions of this work in three-fold: 1) volumetric body composition segmentation, 2) body composition quantification, and 3) treatment response prediction model. 

✔ **Volumetric body composition segmentation** 
- We used our previously developed deep learning model (AutoPanoM v1.0.0.0, MediaLab) to automatically locate vertebrae and pre-segment five body composition components, including vertebrae, skeletal muscle (SM), subcutaneous adipose tissue (SAT), visceral adipose tissue (VAT), and intermuscular fat tissue (IMAT). This model was developed using the nnUNet framework with three-dimensional (3D) full-resolution adaptive segmentation, trained on a cohort of more than 3000 CT cases.
  
✔ **Body composition quantification**
- We quantified the volume of each tissue component from the first slice of first thoracic vertebra through the last slice of twelfth thoracic vertebra, as determined by the automated model. To adjust for individual body size, these volumes were indexed to height squared (cm³/m²), producing four volumetric metrics: skeletal muscle volume index (SMVI), intermuscular adipose volume index (IMVI), subcutaneous adipose volume index (SAVI), and visceral adipose volume index (VAVI).
  
✔ **Treatment response prediction model**
- The AI-based prediction model incorporates Sex, Smoking status, Histological types, TPS, SMVI group, %∆SMVI and %∆SAVI.

For research reproducibility and clinical utility, we provided a software named Neoadjuvant Immuno-ChEmotherapy predictor based on Body Composition (NICE-BC), which integrates the above functionalities together.

<p align="center">
  <img src="https://github.com/user-attachments/assets/dbcc1e5f-7ea3-4638-9a65-d593d95d4515" width="1000" height="500">
</p>

# Usage Guide

This repository provides a complete workflow for body composition analysis and treatment response prediction. Follow the guides below based on your needs:

## 📱 For End Users: Using the NICE-BC Application

If you want to use the NICE-BC software for body composition analysis and treatment response prediction:

👉 **See [app/README.md](app/README.md)** for detailed instructions on:
- Installation methods (source code or binary release)
- Demo data download
- Output management
- Model access information

## 🔬 For Researchers: Training Custom Models

If you want to train your own body composition segmentation models using nnU-Net:

👉 **See [seg_tools/README.md](seg_tools/README.md)** for detailed instructions on:
- Dataset preparation and structure
- Model architecture configurations
- Training commands for spine localization and body composition segmentation
- Inference commands with different step sizes


## Workflow Overview

```
1. Data Input (CT scans)
   ↓
2. Spine Localization (3d_lowres, step_size=1)
   ↓
3. Body Composition Segmentation (3d_fullres, step_size=0.5)
   ↓
4. Volume Quantification (SMVI, SAVI, VAVI, IMVI)
   ↓
5. Treatment Response Prediction
   ↓
6. Results Output (Segmentation masks, metrics, reports)
```

## Important Note: AutoPanoM Model Access

⚠️ **The AutoPanoM deep learning models used in this software are not publicly available.** 

To obtain access to the AutoPanoM v1.0.0.0 model for body composition segmentation, please contact:

📧 **Prof. Zhenwei Shi**: [shizhenwei@gdph.org.cn](mailto:shizhenwei@gdph.org.cn)

In your request, please include:
- Your name and institutional affiliation
- Intended research purpose
- Brief description of your project

The model access is provided for research purposes only and requires approval from the development team.

## Main Developers

 - [Prof. Zhenwei Shi](https://github.com/zhenweishi) <sup/>1, 2
 - MD. Yilong Huang <sup/>3
 - [MSc. Zhitao Wei](https://github.com/kissablemt) <sup/>1, 2
 - MD. Changhong Liang <sup/>1, 2
 - MD. Zaiyi Liu <sup/>1, 2
 
<sup>1</sup> Department of Radiology, Guangdong Provincial People's Hospital (Guangdong Academy of Medical Sciences), Southern Medical University, China <br/>
<sup>2</sup> Guangdong Provincial Key Laboratory of Artificial Intelligence in Medical Image Analysis and Application, China <br/>
<sup>3</sup> Department of Medical Imaging, the First Affiliated Hospital of Kunming Medical University, Kunming, Yunnan, China <br/>

## Contact

📧 For collaboration inquiries, please contact Prof. Zhenwei Shi [Contact Email](shizhenwei@gdph.org.cn)







