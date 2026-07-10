---
name: benchmark-onnx
description: Use this skill to benchmark an ONNX model on a remote device with OpenVINO (benchmark_app) and summarize the reports. Assumes a deploy package (ONNX model + inference script + assets) already exists; use model-convert-and-benchmark first if you still need to produce one.
---

# Benchmark ONNX Model

## Inputs

- `MODEL_NAME` (required)
- `DEPLOY_PACKAGE` (required) — folder with ONNX model(s), minimal OpenVINO inference script(s), `requirements.txt`, and demo assets
- `REMOTE_HOST` (optional) — run remotely; if omitted, benchmark on localhost
- `TARGET_DEVICE` (optional, user-selected on remote)

## Remote benchmark (`REMOTE_HOST`)

1. Setup passwordless SSH once:
   ```bash
   ./setup_remote_ssh.sh "$REMOTE_HOST"
   ```
2. On remote, set proxy `http://child-prc.intel.com:913`.
3. Install `rtk` to `$HOME/.local/bin`:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | bash
   ```
4. Create `$HOME/ov_bench/{modelname}`.
5. Ensure `$HOME/ov_bench/.venv` exists and use it.
6. Copy deploy package and `gpu_monitor.py` to remote folder.
7. Install latest OpenVINO (`pip install openvino`) and package deps.
8. List devices and let user choose target.
9. Run inference sanity check on target device.
10. Run `benchmark_app` on the ONNX model:
    ```bash
    benchmark_app -m {modelname}.onnx -d {device} -hint throughput -t 15 \
        -report_type no_counters -json_stats true \
        -report_folder ./reports/{modelname}-{device}-{date}-{time}.json
    ```
    When `{device}` is a GPU, wrap it with `gpu_monitor.py` to capture per-process GPU/CPU/mem usage (JSONL log + max-util summary via Intel DRM fdinfo, i915/xe):
    ```bash
    python gpu_monitor.py --summary --log-path ./reports/{modelname}-{device}-{date}-{time}.gpu.jsonl -- \
      benchmark_app -m {modelname}.onnx -d {device} -hint throughput -t 15 \
          -report_type no_counters -json_stats true \
          -report_folder ./reports/{modelname}-{device}-{date}-{time}.json
    ```

## Summarize reports

- Generate a csv summarizing benchmark reports, each row a model, columns: model name, device, input shape, batch size, average latency, throughput, plus peak GPU engine util % (from the `.gpu.jsonl` max-util summary).
- Add cpu model, gpu model, os version, kernel version, gpu driver version, npu driver version, openvino version, benchmark methods in the summary.
