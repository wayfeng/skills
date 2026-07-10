# benchmark-onnx

Benchmark an ONNX model on a remote device with OpenVINO (`benchmark_app`), while
capturing per-process device utilization, and summarize the reports.

The full workflow (SSH setup, deploy, device selection, report CSV) lives in
[`SKILL.md`](SKILL.md). This README documents the standalone monitor utilities.

## Files

- `SKILL.md` — the agent skill / workflow.
- `setup_remote_ssh.sh` — one-time passwordless SSH setup: `./setup_remote_ssh.sh <host>`.
- `gpu_monitor.py` — Intel GPU per-process utilization (DRM fdinfo, i915/xe).
- `npu_monitor.py` — Intel NPU utilization (accel `runtime_active_time`, `intel_vpu`).

## Monitors

Both wrap a command with `-- <cmd>`: they start sampling, run the command,
stop when it exits, and print a peak-usage summary. Use `--summary` for a
per-sample line and `--log-path FILE` for a JSONL trace (one sample per line).

```bash
# GPU: per-process engine/CPU/mem while benchmarking
python gpu_monitor.py --summary --log-path run.gpu.jsonl -- \
  benchmark_app -m model.onnx -d GPU -hint throughput -t 15

# NPU: device utilization + benchmark process CPU/mem
python npu_monitor.py --summary --log-path run.npu.jsonl -- \
  benchmark_app -m model.onnx -d NPU -hint throughput -t 15
```

Both accept `-p/--period` (sample seconds), `-n/--iterations`, `--duration`,
and `--no-log`. Run without a command to monitor continuously (Ctrl-C to stop).

Linux + Intel hardware only. `gpu_monitor.py` reads `/proc/*/fdinfo` DRM
clients; `npu_monitor.py` reads `/sys/class/accel/accel*` and the pids holding
`/dev/accel/*`. Non-matching targets (e.g. CPU) still log process CPU/mem.
