import time
import os 
import sys
import tempfile

from pathlib import Path

import hashlib

import nibabel as nib
import numpy as np
import logging
from typing import Dict

import spine_utils
import metrics
import pickle
import time

def get_file_md5(file_path):
    """
    Calculate MD5 hash value of file
    
    Args:
        file_path: File path
        
    Returns:
        str: MD5 hash value
    """
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        # Read in chunks, suitable for large files
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def get_cache_dir():
    """获取缓存目录，在可执行文件同一目录下"""
    if getattr(sys, 'frozen', False):
        # 如果是PyInstaller打包的程序，在可执行文件同一目录下创建cache
        exe_dir = Path(sys.executable).parent
        cache_dir = exe_dir / "cache"
    else:
        # 开发环境
        cache_dir = Path("./cache")
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def get_results_dir():
    """获取结果目录，在可执行文件同一目录下"""
    if getattr(sys, 'frozen', False):
        # 如果是PyInstaller打包的程序，在可执行文件同一目录下创建results
        exe_dir = Path(sys.executable).parent
        results_dir = exe_dir / "results"
    else:
        # 开发环境
        results_dir = Path("./results")
    
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

CACHE_DIR = get_cache_dir()
RESULTS_DIR = get_results_dir()

def test(pre_path, post_path, callback=None):
    """
    Processing function
    
    Args:
        pre_path: Pre image file path
        post_path: Post image file path
        callback: Optional callback function for real-time output
    """
    if callback:
        callback(f"Start processing Pre: {pre_path}")
        callback(f"Start processing Post: {post_path}")
    
    for i in range(10):
        if callback:
            callback(f"Processing step {i}")
        else:
            print(i, flush=True)
        time.sleep(1)
    
    if callback:
        callback("Processing complete")

def calc_phase(image_path, bone_path, bc_path, task_name):
    start_level = 'T1'
    end_level = 'T12'
    choose_middle_level = ['L1']

    # 初始化字典和值
    spine_name_list = ['S', 'L5', 'L4', 'L3', 'L2', 'L1', 'T12', 'T11', 'T10', 'T9', 'T8', 'T7', 'T6', 'T5',
                    'T4', 'T3', 'T2', 'T1', 'C7', 'C6', 'C5', 'C4', 'C3', 'C2', 'C1']    # 注意：数据里有些可能没有
    spine_label_list = [i for i in range(1, 26)]    # 1-25 对应26个标签
    spine_dict = {}
    for i, name in enumerate(spine_name_list):
        spine_dict[name] = spine_label_list[i]

    body_composition_list = ['Muscle', 'IMAT', 'VAT', 'SAT', 'Bone']
    body_composition_label = [i for i in range(1, 6)]   # 1-5
    composition_dict = {}
    for i, name in enumerate(body_composition_list):
        composition_dict[name] = body_composition_label[i]

    img = nib.load(image_path)
    spine_seg = nib.load(bone_path)
    composition_seg = nib.load(bc_path)

    # 重置一下轴
    img, img_spacing = spine_utils.ToCanonical(img)
    spine_seg, spine_spacing = spine_utils.ToCanonical(spine_seg)
    composition_seg, composition_spacing = spine_utils.ToCanonical(composition_seg)

    try:
        # 计算ROI的位置
        (spine_hus, rois, centroids_3d, updown_positions) = spine_utils.compute_rois(
            spine_seg,  # 脊柱分割结果 (nib)
            img,  # 原始图像 (nib)
            spine_dict,  # 传入一个categories的dict: 表示每个椎骨对应的值
            connectivity=4
        )
    except Exception:
        import traceback
        traceback.print_exc()

    # 3d 结果
    try:
        start_slice = updown_positions[start_level][-1]  # 上边界
        end_slice = updown_positions[end_level][0]  # 下边界
        

        assert start_slice > end_slice, 'start and end position may be reversed!'  # 判断一下起始层和最终层有没有相反

        img_one = img.get_fdata()[:, :, end_slice: start_slice + 1]
        seg_one = composition_seg.get_fdata()[:, :, end_slice: start_slice + 1]

        seg_one_whole = np.zeros(
            shape=(img_one.shape[0], img_one.shape[1], img_one.shape[2], len(composition_dict)))

        for key, value in composition_dict.items():
            # print(key)
            seg_one_whole[:, :, :, value - 1][seg_one == value] = 1

        results_3d = metrics.compute_metrics_3d(img_one, seg_one_whole, img_spacing, composition_dict)
        this_output_metric_dir = RESULTS_DIR

        filename = task_name + "_" + Path(image_path).name.replace(".nii.gz", "")
        metrics.save_results_3d(composition_dict, results_3d, start_level, end_level, this_output_metric_dir, filename)
        return {
            "SM": results_3d["Muscle"]["Volume"],
            "SA": results_3d["SAT"]["Volume"],
        }

    except Exception:
        import traceback
        traceback.print_exc()

def calc(sex, smoking_status, type_, tps, height, pre_results_3d, post_results_3d, task_name):
    print("Sex: ", sex, flush=True)
    print("Smoking Status: ", smoking_status, flush=True)
    print("Type: ", type_, flush=True)
    print("TPS: ", tps, flush=True)
    print("Height: ", height, flush=True)
    # print("Pre Results: ", pre_results_3d)
    # print("Post Results: ", post_results_3d)
    h2 = height * height + 1e-6
    pre_smvi = pre_results_3d["SM"] / h2
    pre_savi = pre_results_3d["SA"] / h2
    post_smvi = post_results_3d["SM"] / h2
    post_savi = post_results_3d["SA"] / h2
    delta_smvi = (post_smvi - pre_smvi) / (pre_smvi + 1e-6) * 100
    delta_savi = (post_savi - pre_savi) / (pre_savi + 1e-6)* 100
    pre_smvi_group = 0 if pre_smvi < 1179 else 1
    print("Pre SMVI Group: ", pre_smvi_group, flush=True)
    
    # print("Pre SMVI: ", pre_smvi)
    # print("Pre SAVI: ", pre_savi)
    # print("Post SMVI: ", post_smvi)
    # print("Post SAVI: ", post_savi)
    print("Delta SMVI: ", delta_smvi, flush=True)
    print("Delta SAVI: ", delta_savi, flush=True)

    smoking_status1 = 0 if smoking_status == 1 else 1
    smoking_status2 = 0 if smoking_status == 2 else 1
    type2 = 0 if type_ == 2 else 1
    type3 = 0 if type_ == 3 else 1

    z = 0.38904 * sex + \
        -0.05748 * smoking_status1 + 0.92091 * smoking_status2 + \
        1.12320 * type2 + 0.66086 * type3 + \
        0.76735 * tps + \
        0.65945 * pre_smvi_group + \
        0.04367 * delta_smvi + \
        0.01408 * delta_savi + \
        -2.61810
    
    y = 1 / (1 + np.exp(-z))
    
    with open(RESULTS_DIR / f"{task_name}_prediction.txt", "a") as f:
        f.write(f"sex = {sex}\n")
        f.write(f"smoking_status1 = {smoking_status1}\n")
        f.write(f"smoking_status2 = {smoking_status2}\n")
        f.write(f"type2 = {type2}\n")
        f.write(f"type3 = {type3}\n")
        f.write(f"tps = {tps}\n")
        f.write(f"pre_smvi_group = {pre_smvi_group}\n")
        f.write(f"delta_smvi = {delta_smvi}\n")
        f.write(f"delta_savi = {delta_savi}\n")
        f.write(f"intercept = -2.61810\n")
        f.write(f"--------------------------------\n")
        z_str = f"z = 0.38904 * sex -0.05748 * smoking_status1 + 0.92091 * smoking_status2 + 1.12320 * type2 + 0.66086 * type3 + 0.76735 * tps + 0.65945 * pre_smvi_group + 0.04367 * delta_smvi + 0.01408 * delta_savi -2.61810\n"
        f.write(z_str)
        f.write(f"z = {z}\n")
        f.write(f"--------------------------------\n")
        f.write(f"y = 1 / (1 + np.exp(-z)) = {y}\n")
        f.write(f"y = {y}\n")
    print("z: ", z, flush=True)
    print("y: ", y, flush=True)
    print(f"callback@y@{y}", flush=True)
    return float(y)

def run(pre_path, post_path, parameters, preprocessed_files=None):
    """
    Main processing function
    
    Args:
        pre_path: Pre image file path
        post_path: Post image file path
        parameters: Parameter dictionary containing sex, smoking, types, tps, height
        preprocessed_files: Required dict containing paths to preprocessed segmentation files
                           Keys: 'pre_bc', 'pre_bone', 'post_bc', 'post_bone'
    """
    # 使用时间戳起一个任务名
    task_name = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    print("=== Starting Processing Task ===", flush=True)
    print(f"Pre file: {pre_path}", flush=True)
    print(f"Post file: {post_path}", flush=True)
    print(f"Parameters: {parameters}", flush=True)
    
    if preprocessed_files is None:
        preprocessed_files = {}
    print(f"Preprocessed files: {preprocessed_files}", flush=True)
    
    print("Calculating file MD5...", flush=True)
    pre_md5 = get_file_md5(pre_path)
    post_md5 = get_file_md5(post_path)
    print(f"Pre MD5: {pre_md5}", flush=True)
    print(f"Post MD5: {post_md5}", flush=True)

    # All segmentation files are now required
    if 'pre_bc' not in preprocessed_files or not preprocessed_files['pre_bc']:
        raise ValueError("Pre BC segmentation file is required")
    if 'pre_bone' not in preprocessed_files or not preprocessed_files['pre_bone']:
        raise ValueError("Pre bone segmentation file is required")
    if 'post_bc' not in preprocessed_files or not preprocessed_files['post_bc']:
        raise ValueError("Post BC segmentation file is required")
    if 'post_bone' not in preprocessed_files or not preprocessed_files['post_bone']:
        raise ValueError("Post bone segmentation file is required")

    pre_bc_path = Path(preprocessed_files['pre_bc'])
    pre_bone_path = Path(preprocessed_files['pre_bone'])
    post_bc_path = Path(preprocessed_files['post_bc'])
    post_bone_path = Path(preprocessed_files['post_bone'])

    print("Checking segmentation files...", flush=True)
    
    # Verify all required files exist
    if not pre_bc_path.exists():
        raise FileNotFoundError(f"Pre BC file does not exist: {pre_bc_path}")
    print(f"Using pre BC segmentation: {pre_bc_path}", flush=True)
    print(f"callback@pre_bc_path@{pre_bc_path}", flush=True)
        
    if not pre_bone_path.exists():
        raise FileNotFoundError(f"Pre bone file does not exist: {pre_bone_path}")
    print(f"Using pre bone segmentation: {pre_bone_path}", flush=True)
    print(f"callback@pre_bone_path@{pre_bone_path}", flush=True)
    
    if not post_bc_path.exists():
        raise FileNotFoundError(f"Post BC file does not exist: {post_bc_path}")
    print(f"Using post BC segmentation: {post_bc_path}", flush=True)
    print(f"callback@post_bc_path@{post_bc_path}", flush=True)
    
    if not post_bone_path.exists():
        raise FileNotFoundError(f"Post bone file does not exist: {post_bone_path}")
    print(f"Using post bone segmentation: {post_bone_path}", flush=True)
    print(f"callback@post_bone_path@{post_bone_path}", flush=True)

    print("Calculating Pre and Post phase metrics in parallel...", flush=True)
    
    pre_results_path = CACHE_DIR / f"{pre_md5}_results.pkl"
    post_results_path = CACHE_DIR / f"{post_md5}_results.pkl"
    
    # Check which calculations are needed
    need_pre_calc = not pre_results_path.exists()
    need_post_calc = not post_results_path.exists()
    
    pre_results_3d = None
    post_results_3d = None
    
    if need_pre_calc or need_post_calc:
        from concurrent.futures import ProcessPoolExecutor
        
        futures = {}
        with ProcessPoolExecutor(max_workers=2) as executor:
            if need_pre_calc:
                print("Submitting Pre phase calculation...", flush=True)
                futures['pre'] = executor.submit(calc_phase, pre_path, pre_bone_path, pre_bc_path, task_name)
            
            if need_post_calc:
                print("Submitting Post phase calculation...", flush=True)
                futures['post'] = executor.submit(calc_phase, post_path, post_bone_path, post_bc_path, task_name)
            
            # Wait for completion and get results
            if 'pre' in futures:
                print("Waiting for Pre phase calculation to complete...", flush=True)
                pre_results_3d = futures['pre'].result()
                print("Pre phase calculation completed", flush=True)
                
            if 'post' in futures:
                print("Waiting for Post phase calculation to complete...", flush=True)
                post_results_3d = futures['post'].result()
                print("Post phase calculation completed", flush=True)
    
    # Handle caching and loading after parallel execution
    if need_pre_calc and pre_results_3d is not None:
        with open(pre_results_path, "wb") as f:
            pickle.dump(pre_results_3d, f)
        print(f"callback@pre_results_path@{pre_results_path}", flush=True)
    elif not need_pre_calc:
        with open(pre_results_path, "rb") as f:
            pre_results_3d = pickle.load(f)
        print(f"callback@pre_results_path@{pre_results_path}", flush=True)
    
    if need_post_calc and post_results_3d is not None:
        with open(post_results_path, "wb") as f:
            pickle.dump(post_results_3d, f)
        print(f"callback@post_results_path@{post_results_path}", flush=True)
    elif not need_post_calc:
        with open(post_results_path, "rb") as f:
            post_results_3d = pickle.load(f)
        print(f"callback@post_results_path@{post_results_path}", flush=True)

    print("Calculating final result...", flush=True)
    y = calc(parameters["sex"], parameters["smoking"], parameters["types"], parameters["tps"], parameters["height"], pre_results_3d, post_results_3d, task_name)
    
    print(f"Final prediction result: {y}", flush=True)
    print("=== Processing Task Complete ===", flush=True)
    return y