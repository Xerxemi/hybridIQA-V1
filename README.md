# hybridIQA-V1
An alternative aesthetic scorer based on hyperIQA

This scorer is intended primarily to score anime AI-gen images and sort aesthetic datasets.

Modified ImageReward branch here for benchmark: https://github.com/Xerxemi/ImageReward-hyperIQA-bench

Uses custom "hybrid" dataset and as such efficacy is questionable... only 50% accuracy on ImageReward Figure 3 test, though CLIP is also only 54%...

(good for mini 1263 image dataset comprised of fully anime images on realistic gen test I guess)

![image](https://github.com/SatellaSatella/hybridIQA/assets/140206058/8d2d12d9-0b01-45a0-896c-5fa1127becda)

## Dataset methodology:

URL: https://huggingface.co/datasets/Xerxemi/hybridIQA-V1/

Total dataset size: 1263 images

------------------------------------------------------------------------------------------------------

1181 images generated at 1024x1024 using AUTOMATIC1111/stable-diffusion-webui, utilizing 5 models and 2 upscalers (Latent & None).

Dynamic Prompts extension wildcards used for prompting.

------------------------------------------------------------------------------------------------------

Binned into "Artifact" and "Perfect" folders, then each folder is further binned into score range 1-5.

"Perfect" folder bins are shifted +2 on the score scale (scale 1-7) to increase importance of artifacts.

------------------------------------------------------------------------------------------------------

"8" folder bins are cherry-picked generations (not from the mass-produced image pool).

"9" folder bins are real images from maccha and omutatsu.

## Modifications to original architecture:

Dataloader changed to be suitable for dataset structure (also caches images as tensor on GPU for speed rather than rereading all images on request).

Optimizer swap Adam to Lion with LR/5, weight decay*5, and beta adjusted accordingly.

Resnet50 backbone swapped with Resnet152.

Some minor & major fixes to code.

### Transforms:

Patches per image increased 16x, from 25 to 400.

15% random images converted to grayscale to remove color bias.

RandomCrop replaced with RandomResizeCrop with bilinear interpolation & antialiasing (training only).

### Inference:

Patches per image increased from 10 to 25.

### Training:

Batch size increased to 300 - pretrained model trained to epoch 9.

## Usage:

Place pretrained model from https://huggingface.co/Xerxemi/hybridIQA-V1 in ./pretrained.

Images go in ./data/, then run demo.py with the filename to score.

Training datasets must go in ./data/ and be set up accordingly in the scripts (need dataloader or supported format).

------------------------------------------------------------------------------------------------------

## Citation:
```
@InProceedings{Su_2020_CVPR,
author = {Su, Shaolin and Yan, Qingsen and Zhu, Yu and Zhang, Cheng and Ge, Xin and Sun, Jinqiu and Zhang, Yanning},
title = {Blindly Assess Image Quality in the Wild Guided by a Self-Adaptive Hyper Network},
booktitle = {IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
month = {June},
year = {2020}
}
```
