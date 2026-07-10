---
name: model-convert-and-benchmark
description: Use this skill to process a given AI model to a reproducible PyTorch -> ONNX -> OpenVINO pipeline
---

# Convert and Benchmark Model

## Inputs

- `MODEL_NAME` (required)
- `MODEL_URL` (required)
- `REMOTE_HOST` (optional)
- `TARGET_DEVICE` (optional, user-selected on remote)

## Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
```

Torch installs should use CPU wheels via:

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cpu torch
```

## Workflow

1. Get model name and URL.
2. Resolve model source:
   - If URL is GitHub, clone to `./projs/`.
   - Else fetch the URL and find GitHub repo links; if multiple, ask user to choose one/all.
3. Analyze code with CodeGraph (`codegraph sync` if index exists).
4. In cloned repo(s), locate model weights and inference path.
5. Download model files to `./models/`.
6. Install required dependencies into `.venv`.
7. Convert checkpoint to ONNX:
   - Create `./convert/{modelname}/`.
   - Store onnx model to `./convert/{modelname}/`
   - Add conversion script(s).
   - Add pinned `requirements.txt` for conversion.
8. Verify parity (PyTorch vs ONNX/OpenVINO):
   - Reuse original demo assets if available; otherwise use `./assets`.
   - Add compare scripts in `./convert/{modelname}/`.
   - Investigate mismatches until acceptable.
9. Build deploy package containing:
   - ONNX model(s)
   - Minimal OpenVINO inference script(s)
   - `requirements.txt`
   - Demo image/video assets
10. Benchmark the deploy package with the `benchmark-onnx` skill (remote OpenVINO `benchmark_app` + report summary).

## Constraints

- Prefer minimal, reproducible scripts over one-off shell history.
- Validate by running concrete conversion/compare commands added.
- Keep deploy dependencies minimal.
- If source URL resolution is ambiguous, ask user before proceeding.

## Notes

- For `huggingface.co`, use proxy: `http://proxy.ims.intel.com:911`.
