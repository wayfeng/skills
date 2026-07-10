#!/usr/bin/env python3

import argparse
import glob
import json
import os
import queue
import signal
import subprocess
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple


ACCEL_DEV_PREFIX = "/dev/accel/accel"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def read_sysfs(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except (OSError, ValueError):
        return None


def discover_npu_devices() -> List[dict]:
    """Each Intel NPU shows up as /sys/class/accel/accelN backed by the intel_vpu driver."""
    devices = []
    for class_path in sorted(glob.glob("/sys/class/accel/accel*")):
        name = os.path.basename(class_path)
        dev_path = os.path.join(class_path, "device")
        driver = None
        try:
            driver = os.path.basename(os.readlink(os.path.join(dev_path, "driver")))
        except OSError:
            pass
        # ponytail: accept any accel device if driver link is missing; filter to intel_vpu when known.
        if driver and driver != "intel_vpu":
            continue
        devices.append({
            "name": name,
            "runtime_active_time": os.path.join(dev_path, "power", "runtime_active_time"),
            "runtime_status": os.path.join(dev_path, "power", "runtime_status"),
        })
    return devices


def read_process_name(pid: int) -> str:
    try:
        with open(f"/proc/{pid}/stat", "r", encoding="utf-8") as f:
            data = f.read()
    except OSError:
        return ""

    start = data.find("(")
    end = data.rfind(")")
    if start < 0 or end < 0 or end <= start + 1:
        return ""
    return data[start + 1 : end]


def read_proc_cpu_mem(pid: int) -> Tuple[Optional[int], Optional[int]]:
    cpu_ticks: Optional[int] = None
    rss_kb: Optional[int] = None

    try:
        with open(f"/proc/{pid}/stat", "r", encoding="utf-8") as f:
            stat_data = f.read()
        fields = stat_data.split()
        if len(fields) >= 15:
            cpu_ticks = int(fields[13]) + int(fields[14])
    except (OSError, ValueError):
        cpu_ticks = None

    try:
        with open(f"/proc/{pid}/status", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        rss_kb = int(parts[1])
                    break
    except (OSError, ValueError):
        rss_kb = None

    return cpu_ticks, rss_kb


def scan_npu_clients() -> Dict[str, List[int]]:
    """Map accel device name -> pids holding an fd to it, by scanning /proc/*/fd links."""
    clients: Dict[str, List[int]] = {}
    try:
        proc_entries = os.listdir("/proc")
    except OSError:
        return clients

    for ent in proc_entries:
        if not ent.isdigit():
            continue
        pid = int(ent)
        fd_dir = f"/proc/{pid}/fd"
        try:
            fd_entries = os.listdir(fd_dir)
        except OSError:
            continue
        for fd_name in fd_entries:
            try:
                target = os.readlink(os.path.join(fd_dir, fd_name))
            except OSError:
                continue
            if target.startswith(ACCEL_DEV_PREFIX):
                dev_name = os.path.basename(target)
                pids = clients.setdefault(dev_name, [])
                if pid not in pids:
                    pids.append(pid)
    return clients


class NpuMonitor:
    def __init__(
        self,
        period_s: float = 2.0,
        log_path: Optional[str] = None,
        callback=None,
    ):
        self.period_s = period_s
        self.callback = callback
        self.log_path = log_path  # None disables logging

        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._latest = None
        self._queue: queue.Queue = queue.Queue()
        self._devices = discover_npu_devices()
        self._prev_active_ms: Dict[str, int] = {}
        self._prev_proc_cpu: Dict[int, int] = {}
        self._clk_tck = os.sysconf("SC_CLK_TCK")
        self._log_fp = None

    def _proc_stats(self, pid: int) -> dict:
        cpu_ticks, rss_kb = read_proc_cpu_mem(pid)
        cpu_usage_pct = None
        prev_cpu_ticks = self._prev_proc_cpu.get(pid)
        if cpu_ticks is not None:
            self._next_proc_cpu[pid] = cpu_ticks
            if prev_cpu_ticks is not None and cpu_ticks >= prev_cpu_ticks:
                delta_sec = (cpu_ticks - prev_cpu_ticks) / self._clk_tck
                cpu_usage_pct = max(0.0, (delta_sec / self.period_s) * 100.0)
        return {
            "pid": pid,
            "process_name": read_process_name(pid),
            "cpu_usage_pct": cpu_usage_pct,
            "memory_rss_kb": rss_kb,
            "memory_rss_mib": (rss_kb / 1024.0) if rss_kb is not None else None,
        }

    def _compute_sample(self, ts_epoch: float) -> dict:
        clients = scan_npu_clients()
        self._next_proc_cpu = {}
        period_ms = self.period_s * 1000.0

        sample_devices = []
        for dev in self._devices:
            name = dev["name"]
            active_str = read_sysfs(dev["runtime_active_time"])
            active_ms = int(active_str) if active_str and active_str.isdigit() else None

            util_pct = None
            prev = self._prev_active_ms.get(name)
            if active_ms is not None:
                self._prev_active_ms[name] = active_ms
                if prev is not None and active_ms >= prev and period_ms > 0:
                    util_pct = clamp((active_ms - prev) / period_ms * 100.0, 0.0, 100.0)

            processes = [self._proc_stats(pid) for pid in clients.get(name, [])]

            sample_devices.append({
                "name": name,
                "runtime_status": read_sysfs(dev["runtime_status"]),
                "active_time_ms": active_ms,
                "npu_util_pct": util_pct,
                "num_processes": len(processes),
                "processes": processes,
            })

        self._prev_proc_cpu = self._next_proc_cpu

        return {
            "timestamp": ts_epoch,
            "iso_time": datetime.fromtimestamp(ts_epoch).isoformat(),
            "period_s": self.period_s,
            "num_devices": len(sample_devices),
            "devices": sample_devices,
        }

    def _run(self):
        while not self._stop.is_set():
            start = time.monotonic()
            sample = self._compute_sample(time.time())

            if self._log_fp:
                self._log_fp.write(json.dumps(sample, separators=(",", ":")) + "\n")
                self._log_fp.flush()

            with self._lock:
                self._latest = sample
            self._queue.put(sample)

            if self.callback:
                self.callback(sample)

            remaining = self.period_s - (time.monotonic() - start)
            if remaining > 0:
                self._stop.wait(remaining)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        if self.log_path:
            self._log_fp = open(self.log_path, "a", encoding="utf-8")
        self._thread = threading.Thread(target=self._run, name="npu-monitor", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join()
        if self._log_fp:
            self._log_fp.close()
            self._log_fp = None

    def snapshot(self) -> Optional[dict]:
        with self._lock:
            return dict(self._latest) if self._latest is not None else None

    def iter_samples(self):
        while not self._stop.is_set() or not self._queue.empty():
            try:
                yield self._queue.get(timeout=0.1)
            except queue.Empty:
                continue


def print_summary(sample: dict):
    print(f"[{sample['iso_time']}] devices={sample['num_devices']}")
    for dev in sample["devices"]:
        util = dev.get("npu_util_pct")
        util_str = f"{util:.1f}%" if util is not None else "n/a"
        print(f"  {dev['name']} util={util_str} status={dev.get('runtime_status')} procs={dev['num_processes']}")
        for p in dev["processes"]:
            cpu = p.get("cpu_usage_pct")
            cpu_str = f"{cpu:.1f}%" if cpu is not None else "n/a"
            rss = p.get("memory_rss_mib")
            rss_str = f"{rss:.1f} MiB" if rss is not None else "n/a"
            print(f"    pid={p['pid']} name={p['process_name']} cpu={cpu_str} rss={rss_str}")


def update_max_utilization(summary: dict, sample: dict):
    devices = summary.setdefault("devices", {})
    procs = summary.setdefault("procs", {})
    for dev in sample.get("devices", []):
        util = dev.get("npu_util_pct")
        if util is not None and util > devices.get(dev["name"], -1.0):
            devices[dev["name"]] = util

        for p in dev.get("processes", []):
            key = (p.get("pid"), p.get("process_name", ""))
            peak = procs.setdefault(key, {"cpu_pct": None, "rss_kb": None})
            cpu = p.get("cpu_usage_pct")
            if cpu is not None and (peak["cpu_pct"] is None or cpu > peak["cpu_pct"]):
                peak["cpu_pct"] = cpu
            rss = p.get("memory_rss_kb")
            if rss is not None and (peak["rss_kb"] is None or rss > peak["rss_kb"]):
                peak["rss_kb"] = rss


def print_final_max_utilization_summary(summary: dict):
    devices = summary.get("devices", {})
    procs = summary.get("procs", {})

    print("\nFinal max NPU utilization per device:")
    if not devices:
        print("  No NPU utilization samples collected.")
    else:
        for name, pct in sorted(devices.items()):
            print(f"  {name}: {pct:.1f}%")

    print("\nFinal max CPU/mem per process:")
    if not procs:
        print("  No process samples collected.")
        return
    for (pid, name), peak in sorted(procs.items(), key=lambda x: (x[0][1], x[0][0])):
        cpu = peak["cpu_pct"]
        cpu_str = f"{cpu:.1f}%" if cpu is not None else "n/a"
        rss_kb = peak["rss_kb"]
        rss_str = f"{rss_kb} ({rss_kb / 1024.0:.1f} MiB)" if rss_kb is not None else "n/a"
        print(f"  pid={pid} name={name}: cpu={cpu_str} rss={rss_str}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Intel NPU utilization monitor via accel sysfs")
    parser.add_argument("-p", "--period", type=float, default=2.0, help="Sampling period in seconds")
    parser.add_argument("-n", "--iterations", type=int, default=0, help="Number of samples (0 = unlimited)")
    parser.add_argument("--duration", type=float, default=0.0, help="Monitor duration in seconds (0 = unlimited)")
    parser.add_argument("--log-path", default=None, help="JSONL output path (default: /tmp/npu_monitor_<timestamp>.jsonl)")
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL logging")
    parser.add_argument("--summary", action="store_true", help="Print compact summary per sample")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Optional command to run while monitoring, use: -- cmd args")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    callback = (lambda sample: print_summary(sample)) if args.summary else None
    if args.no_log:
        log_path = None
    else:
        log_path = args.log_path or f"/tmp/npu_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

    monitor = NpuMonitor(period_s=args.period, log_path=log_path, callback=callback)

    if not monitor._devices:
        print("No Intel NPU (accel) device found under /sys/class/accel.")

    stop_flag = {"stop": False}

    def _signal_handler(_sig, _frame):
        stop_flag["stop"] = True

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]

    proc = None
    monitor.start()

    if monitor.log_path:
        print(f"Logging NPU samples to {monitor.log_path}")

    start = time.monotonic()
    samples = 0
    max_util_summary = {}

    try:
        if cmd:
            proc = subprocess.Popen(cmd)

        while not stop_flag["stop"]:
            sample = next(monitor.iter_samples())
            if sample is not None:
                samples += 1
                update_max_utilization(max_util_summary, sample)

            if args.iterations and samples >= args.iterations:
                break
            if args.duration and (time.monotonic() - start) >= args.duration:
                break
            if proc and proc.poll() is not None:
                break

    finally:
        monitor.stop()
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    print_final_max_utilization_summary(max_util_summary)

    if proc:
        return proc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
