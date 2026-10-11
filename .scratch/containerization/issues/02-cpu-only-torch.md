# 02 CPU-only torch

Status: resolved
Type: task

## Why
The lock file resolved CUDA builds of torch, so the image was about 5.95 GB. The question "will CPU-only torch still work like Qwen?" was answered: yes, the same
model runs on CPU (it was already running float32 on CPU in these tests).

## Built
`[[tool.uv.index]] pytorch-cpu` (explicit) and `[tool.uv.sources] torch = { index = "pytorch-cpu", marker = "sys_platform == 'linux'" }`.
The override had no effect while torch was only a transitive dependency, so `torch>=2.1` became a direct dependency.

## Result
Image size 5.95 GB to about 1.24 GB (1.19 GB after later cleanup).

## Files
`pyproject.toml`, `uv.lock`
