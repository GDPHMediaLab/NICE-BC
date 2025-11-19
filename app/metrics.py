"""
author: Li Chuanpu
date: 2023_06_08 17:27
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Callable, Sequence, Union
import pandas as pd
import os

def flatten_non_category_dims(
    xs: Union[np.ndarray, Sequence[np.ndarray]], category_dim: int = None
):
    """Flattens all non-category dimensions into a single dimension.

    Args:
        xs (ndarrays): Sequence of ndarrays with the same category dimension.
        category_dim: The dimension/axis corresponding to different categories.
            i.e. `C`. If `None`, behaves like `np.flatten(x)`.

    Returns:
        ndarray: Shape (C, -1) if `category_dim` specified else shape (-1,)
    """
    single_item = isinstance(xs, np.ndarray)
    if single_item:
        xs = [xs]

    if category_dim is not None:
        dims = (xs[0].shape[category_dim], -1)
        xs = (np.moveaxis(x, category_dim, 0).reshape(dims) for x in xs)
    else:
        xs = (x.flatten() for x in xs)

    if single_item:
        return list(xs)[0]
    else:
        return xs

class Metric(Callable, ABC):
    """Interface for new metrics.

    A metric should be implemented as a callable with explicitly defined
    arguments. In other words, metrics should not have `**kwargs` or `**args`
    options in the `__call__` method.

    While not explicitly constrained to the return type, metrics typically
    return float value(s). The number of values returned corresponds to the
    number of categories.

    * metrics should have different name() for different functionality.
    * `category_dim` duck type if metric can process multiple categories at
        once.

    To compute metrics:

    .. code-block:: python

        metric = Metric()
        results = metric(...)
    """

    def __init__(self, units: str = ""):
        self.units = units

    def name(self):
        return type(self).__name__

    def display_name(self):
        """Name to use for pretty printing and display purposes."""
        name = self.name()
        return "{} {}".format(name, self.units) if self.units else name

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass

class HounsfieldUnits(Metric):
    FULL_NAME = "HU"

    def __init__(self, units="hu"):
        super().__init__(units)

    def __call__(self, mask, x, category_dim: int = None):
        mask = mask.astype(np.bool_)
        if category_dim is None:
            return np.mean(x[mask])

        assert category_dim == -1
        num_classes = mask.shape[-1]

        return np.array([np.mean(x[mask[..., c]]) for c in range(num_classes)])

    def name(self):
        return self.FULL_NAME

class CrossSectionalArea2D(Metric):
    def __call__(self, mask, spacing=None, category_dim: int = None):
        pixel_area = np.prod(spacing) if spacing else 1
        mask = mask.astype(np.bool_)
        mask = flatten_non_category_dims(mask, category_dim)

        return pixel_area * np.count_nonzero(mask, -1) / 100.0

    def name(self):
        if self.units:
            return "Area"
        else:
            return "Cross-sectional Area"

class CrossSectionalArea3D(Metric):
    def __call__(self, mask, spacing=None, category_dim: int = None):
        pixel_volume = np.prod(spacing) if spacing else 1    #
        mask = mask.astype(np.bool_)
        mask = flatten_non_category_dims(mask, category_dim)

        return pixel_volume * np.count_nonzero(mask, -1) / 1000.0

    def name(self):
        if self.units:
            return "Volume"
        else:
            return "Cross-sectional Volume"

def compute_metrics_2d(image, mask, spacing, categories, h):   # categories为体成分对应的字典 h为身高

    """Compute basic results for a given segmentation."""
    hu = HounsfieldUnits()
    csa_units = "cm^2" if spacing else ""
    csa = CrossSectionalArea2D(csa_units)

    hu_vals = hu(mask, image, category_dim=-1)    # mask内部的HU平均值
    csa_vals = csa(mask=mask, spacing=spacing, category_dim=-1)

    assert mask.shape[-1] == len(
        categories
    ), "{} categories found in mask, " "but only {} categories specified".format(
        mask.shape[-1], len(categories)
    )

    results = {
        cat: {
            "mask": mask[..., idx],
            hu.name(): hu_vals[idx],
            csa.name(): csa_vals[idx],
        }
        for idx, cat in enumerate(categories.keys())
    }    # 5个成分的基本结果

    # 综合参数
    results['total_parameters'] = {}
    SMG = results['Muscle']['HU'] * results['Muscle']['Area']
    TAT = results['IMAT']['Area'] + results['VAT']['Area'] + results['SAT']['Area']

    results['total_parameters']['SMG'] = SMG
    results['total_parameters']['TAT'] = TAT

    # 身高标准化
    results['height_norm'] = {}
    SMI = results['Muscle']['Area'] / (h**2)
    results['height_norm']['SMI'] = SMI   # 跟名称不对应，直接先算
    for key in ['IMAT', 'SAT', 'VAT']:
        new_name = key.replace('T', 'I')
        results['height_norm'][new_name] = results[key]['Area'] / (h**2)

    # 骨质标准化
    results['bone_norm'] = {}
    MBR = results['Muscle']['Area'] / results['Bone']['Area']
    results['bone_norm']['MBR'] = MBR
    for key in ['IMAT', 'SAT', 'VAT']:
        new_name = key.replace('AT', 'BR')
        results['bone_norm'][new_name] = results[key]['Area'] / results['Bone']['Area']

    # 分布比例关系
    results['ratio_relationships'] = {}
    SMR = results['SAT']['Area'] / results['Muscle']['Area']
    FF = results['IMAT']['Area'] / results['Muscle']['Area']
    VMR = results['VAT']['Area'] / results['Muscle']['Area']
    IMSR = results['IMAT']['Area'] / results['SAT']['Area']
    VSR = results['VAT']['Area'] / results['SAT']['Area']
    IMVR = results['IMAT']['Area'] / results['VAT']['Area']

    results['ratio_relationships']['SMR'] = SMR
    results['ratio_relationships']['FF'] = FF
    results['ratio_relationships']['VMR'] = VMR
    results['ratio_relationships']['ISMR'] = IMSR
    results['ratio_relationships']['VSR'] = VSR
    results['ratio_relationships']['IMVR'] = IMVR

    return results

def compute_metrics_3d(image, mask, spacing, categories, h=None):   # categories为体成分对应的字典 h为身高

    """Compute basic results for a given segmentation."""
    hu = HounsfieldUnits()
    csa_units = "cm^3" if spacing else ""
    csa = CrossSectionalArea3D(csa_units)

    hu_vals = hu(mask, image, category_dim=-1)    # mask内部的HU平均值
    csa_vals = csa(mask=mask, spacing=spacing, category_dim=-1)

    assert mask.shape[-1] == len(
        categories
    ), "{} categories found in mask, " "but only {} categories specified".format(
        mask.shape[-1], len(categories)
    )

    results = {
        cat: {
            "mask": mask[..., idx],
            hu.name(): hu_vals[idx],
            csa.name(): csa_vals[idx],
        }
        for idx, cat in enumerate(categories.keys())
    }    # 5个成分的基本结果

    # 综合参数
    results['total_parameters'] = {}
    SMM = results['Muscle']['HU'] * results['Muscle']['Volume']
    TFV = results['IMAT']['Volume'] + results['VAT']['Volume'] + results['SAT']['Volume']

    results['total_parameters']['SMM'] = SMM
    results['total_parameters']['TFV'] = TFV

    # 身高标准化
    if h!= None:
        results['height_norm'] = {}
        SMVI = results['Muscle']['Volume'] / (h ** 2)
        results['height_norm']['SMVI'] = SMVI  # 跟名称不对应，直接先算
        for key in ['IMAT', 'SAT', 'VAT']:
            new_name = key.replace('AT', 'FVI')
            results['height_norm'][new_name] = results[key]['Volume'] / (h ** 2)

    # 骨质标准化
    results['bone_norm'] = {}
    MBVR = results['Muscle']['Volume'] / results['Bone']['Volume']
    results['bone_norm']['MBVR'] = MBVR
    for key in ['IMAT', 'SAT', 'VAT']:
        new_name = key.replace('AT', 'BVR')
        results['bone_norm'][new_name] = results[key]['Volume'] / results['Bone']['Volume']

    # 分布比例关系
    results['ratio_relationships'] = {}
    SMVR = results['SAT']['Volume'] / results['Muscle']['Volume']
    VFF = results['IMAT']['Volume'] / results['Muscle']['Volume']
    VMVR = results['VAT']['Volume'] / results['Muscle']['Volume']
    IMSVR = results['IMAT']['Volume'] / results['SAT']['Volume']
    VSVR = results['VAT']['Volume'] / results['SAT']['Volume']
    IMVVR = results['IMAT']['Volume'] / results['VAT']['Volume']

    results['ratio_relationships']['SMVR'] = SMVR
    results['ratio_relationships']['VFF'] = VFF
    results['ratio_relationships']['VMVR'] = VMVR
    results['ratio_relationships']['ISMVR'] = IMSVR
    results['ratio_relationships']['VSVR'] = VSVR
    results['ratio_relationships']['IMVVR'] = IMVVR

    return results

def save_results_2d(categories, results, output_dir):
    """Save results to a CSV file."""
    cats = list(categories.keys())

    # 第一列和第二列先单独创建，其他的后面直接写入
    column1 = []
    column2 = []
    for key1 in results[list(results.keys())[0]].keys():
        if key1 in cats:
            # 第一列
            column1.append(key1)
            column1 += ['']
            column2 += ['HU', 'Area']
        else:
            column1.append(key1)
            for i, key2 in enumerate(results[list(results.keys())[0]][key1].keys()):
                if i == 0:     # 有一行是有字的 不算空行
                    column2.append(key2)
                else:
                    column1.append('')
                    column2.append(key2)

    column_dict = {' ': column1, '  ': column2}     # 表头为空

    # 其他列值写入
    value_dict = {}
    for level in results.keys():
        value_list = []
        for key1 in results[list(results.keys())[0]].keys():
            if key1 in cats:
                value_list.append(results[level][key1]['HU'])
                value_list.append(results[level][key1]['Area'])
            else:
                for key2, value2 in results[level][key1].items():
                    value_list.append(value2)

        value_dict[level] = value_list

    column_dict.update(value_dict)

    df = pd.DataFrame(column_dict)
    df.to_csv(os.path.join(output_dir, "body_composition_metrics_2d.csv"), index=False)

def save_results_3d(categories, results, start_level, end_level, csv_output_dir, filename):
    """Save results to a CSV file."""
    cats = list(categories.keys())

    # 第一列和第二列先单独创建，其他的后面直接写入
    column1 = []
    column2 = []
    for key1 in results.keys():
        if key1 in cats:
            # 第一列
            column1.append(key1)
            column1 += ['']
            column2 += ['HU', 'Volume']
        else:
            column1.append(key1)
            for i, key2 in enumerate(results[key1].keys()):
                if i == 0:     # 有一行是有字的 不算空行
                    column2.append(key2)
                else:
                    column1.append('')
                    column2.append(key2)

    column_dict = {'': column1, ' ': column2}     # 表头为空

    # 其他列值写入
    value_dict = {}
    value_list = []
    for key1 in results.keys():
        if key1 in cats:
            value_list.append(results[key1]['HU'])
            value_list.append(results[key1]['Volume'])
        else:
            for key2, value2 in results[key1].items():
                value_list.append(value2)

    value_dict[f'{start_level}-{end_level}'] = value_list

    column_dict.update(value_dict)

    df = pd.DataFrame(column_dict)
    df.to_csv(os.path.join(csv_output_dir, f"{filename}.csv"), index=False)