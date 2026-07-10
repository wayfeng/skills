#!/usr/bin/env python3

import argparse
import json
import os
import queue
import re
import signal
import stat
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


DRM_MAJOR = 226
INTEL_DRIVERS = {"i915", "xe"}


ENGINE_TIME_RE = re.compile(r"^drm-engine-(.+):\s*(\d+)")
CYCLES_RE = re.compile(r"^drm-cycles-(.+):\s*(\d+)")
TOTAL_CYCLES_RE = re.compile(r"^drm-total-cycles-(.+):\s*(\d+)")
ENGINE_CAP_RE = re.compile(r"^drm-engine-capacity-(.+):\s*(\d+)")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def get_sysfs_drm_path(drm_minor: int) -> str:
    return "/sys/class/drm/renderD" if drm_minor >= 128 else "/sys/class/drm/card"


def read_freq_value(path: str) -> Optional[int]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return int(f.readline().strip())
    except (OSError, ValueError):
        return None


def bound_driver(drm_minor: int) -> Optional[str]:
    link_path = f"{get_sysfs_drm_path(drm_minor)}{drm_minor}/device/driver"
    try:
        target = os.readlink(link_path)
    except OSError:
        return None

    return os.path.basename(target)


def get_num_gts(drm_minor: int, driver: str) -> int:
    count = 0
    for gt in range(8):
        if driver == "xe":
            path = f"{get_sysfs_drm_path(drm_minor)}{drm_minor}/device/tile0/gt{gt}"
        else:
            path = f"{get_sysfs_drm_path(drm_minor)}{drm_minor}/gt/gt{gt}"
        if os.path.isdir(path):
            count += 1
        else:
            break
    return count


def get_intel_frequencies(drm_minor: int, driver: str) -> List[Dict[str, Optional[int]]]:
    out = []
    for gt in range(get_num_gts(drm_minor, driver)):
        if driver == "xe":
            cur = read_freq_value(
                f"{get_sysfs_drm_path(drm_minor)}{drm_minor}/device/tile0/gt{gt}/freq0/cur_freq"
            )
            act = read_freq_value(
                f"{get_sysfs_drm_path(drm_minor)}{drm_minor}/device/tile0/gt{gt}/freq0/act_freq"
            )
        else:
            cur = read_freq_value(
                f"{get_sysfs_drm_path(drm_minor)}{drm_minor}/gt/gt{gt}/rps_cur_freq_mhz"
            )
            act = read_freq_value(
                f"{get_sysfs_drm_path(drm_minor)}{drm_minor}/gt/gt{gt}/rps_act_freq_mhz"
            )
        if cur is None and act is None:
            continue
        out.append({"gt": gt, "cur_mhz": cur, "act_mhz": act})
    return out


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


def is_drm_fd(pid: int, fd_name: str) -> Tuple[bool, Optional[int]]:
    path = f"/proc/{pid}/fd/{fd_name}"
    try:
        st = os.stat(path)
    except OSError:
        return False, None

    if not stat.S_ISCHR(st.st_mode):
        return False, None
    if os.major(st.st_rdev) != DRM_MAJOR:
        return False, None

    return True, os.minor(st.st_rdev)


@dataclass
class ParsedFdinfo:
    driver: str = ""
    pdev: str = ""
    client_id: Optional[int] = None
    engine_time: Dict[str, int] = field(default_factory=dict)
    cycles: Dict[str, int] = field(default_factory=dict)
    total_cycles: Dict[str, int] = field(default_factory=dict)
    capacity: Dict[str, int] = field(default_factory=dict)


def parse_fdinfo_text(text: str) -> ParsedFdinfo:
    info = ParsedFdinfo()

    for line in text.splitlines():
        if line.startswith("drm-driver:"):
            info.driver = line.split(":", 1)[1].strip()
            continue
        if line.startswith("drm-client-id:"):
            try:
                info.client_id = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
            continue
        if line.startswith("drm-pdev:"):
            info.pdev = line.split(":", 1)[1].strip()
            continue

        m = ENGINE_CAP_RE.match(line)
        if m:
            info.capacity[m.group(1)] = int(m.group(2))
            continue

        m = ENGINE_TIME_RE.match(line)
        if m:
            info.engine_time[m.group(1)] = int(m.group(2))
            continue

        m = CYCLES_RE.match(line)
        if m:
            info.cycles[m.group(1)] = int(m.group(2))
            continue

        m = TOTAL_CYCLES_RE.match(line)
        if m:
            info.total_cycles[m.group(1)] = int(m.group(2))

    return info


def read_fdinfo(pid: int, fd_name: str) -> Optional[ParsedFdinfo]:
    path = f"/proc/{pid}/fdinfo/{fd_name}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None

    info = parse_fdinfo_text(text)
    if not info.driver or info.client_id is None:
        return None
    if info.driver not in INTEL_DRIVERS:
        return None
    if not (info.engine_time or info.cycles or info.total_cycles):
        return None
    return info


def scan_proc_drm_clients(include_freq: bool = True) -> List[dict]:
    clients = []
    seen = set()

    try:
        proc_entries = os.listdir("/proc")
    except OSError:
        return clients

    for ent in proc_entries:
        if not ent.isdigit():
            continue

        pid = int(ent)
        pname = read_process_name(pid)
        fdinfo_dir = f"/proc/{pid}/fdinfo"

        try:
            fd_entries = os.listdir(fdinfo_dir)
        except OSError:
            continue

        for fd_name in fd_entries:
            if not fd_name.isdigit():
                continue

            is_drm, drm_minor = is_drm_fd(pid, fd_name)
            if not is_drm or drm_minor is None:
                continue

            info = read_fdinfo(pid, fd_name)
            if info is None:
                continue

            key = (drm_minor, info.client_id)
            if key in seen:
                continue
            seen.add(key)

            driver = bound_driver(drm_minor) or info.driver
            if driver not in INTEL_DRIVERS:
                continue

            engines = sorted(
                set(info.engine_time) | set(info.cycles) | set(info.total_cycles) | set(info.capacity)
            )
            engine_data = {}
            for name in engines:
                engine_data[name] = {
                    "capacity": max(1, info.capacity.get(name, 1)),
                    "engine_time": info.engine_time.get(name),
                    "cycles": info.cycles.get(name),
                    "total_cycles": info.total_cycles.get(name),
                }

            client = {
                "pid": pid,
                "process_name": pname,
                "drm_minor": drm_minor,
                "drm_client_id": info.client_id,
                "driver": driver,
                "pdev": info.pdev,
                "engines": engine_data,
            }
            if include_freq:
                client["frequencies"] = get_intel_frequencies(drm_minor, driver)

            clients.append(client)

    return clients


class GpuMonitor:
    def __init__(
        self,
        period_s: float = 2.0,
        log_path: Optional[str] = None,
        include_freq: bool = True,
        sort_by: str = "gpu",
        callback=None,
    ):
        self.period_s = period_s
        self.period_us = int(period_s * 1_000_000)
        self.include_freq = include_freq
        self.sort_by = sort_by
        self.callback = callback
        self.log_path = log_path or f"/tmp/gpu_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._latest = None
        self._queue: queue.Queue = queue.Queue()
        self._prev_counters: Dict[Tuple[int, int], Dict[str, dict]] = {}
        self._prev_proc_cpu: Dict[int, int] = {}
        self._clk_tck = os.sysconf("SC_CLK_TCK")
        self._log_fp = None

    def _compute_engine_util(self, prev: Optional[dict], cur: dict) -> dict:
        out = dict(cur)
        out["delta_engine_time"] = None
        out["delta_cycles"] = None
        out["delta_total_cycles"] = None
        out["utilization_pct"] = None
        out["utilization_mode"] = None

        if prev is None:
            return out

        if cur.get("engine_time") is not None and prev.get("engine_time") is not None:
            det = cur["engine_time"] - prev["engine_time"]
            if det >= 0:
                out["delta_engine_time"] = det

        if cur.get("cycles") is not None and prev.get("cycles") is not None:
            dc = cur["cycles"] - prev["cycles"]
            if dc >= 0:
                out["delta_cycles"] = dc

        if cur.get("total_cycles") is not None and prev.get("total_cycles") is not None:
            dtc = cur["total_cycles"] - prev["total_cycles"]
            if dtc >= 0:
                out["delta_total_cycles"] = dtc

        cap = max(1, int(cur.get("capacity", 1)))
        if out["delta_cycles"] is not None and out["delta_total_cycles"]:
            pct = (out["delta_cycles"] / out["delta_total_cycles"]) * 100.0 / cap
            out["utilization_pct"] = clamp(pct, 0.0, 100.0)
            out["utilization_mode"] = "cycles"
        elif out["delta_engine_time"] is not None:
            pct = (out["delta_engine_time"] / self.period_us / 1e3) * 100.0 / cap
            out["utilization_pct"] = clamp(pct, 0.0, 100.0)
            out["utilization_mode"] = "engine_time"

        return out

    def _compute_sample(self, clients: List[dict], ts_epoch: float) -> dict:
        sample_clients = []
        next_prev = {}
        next_prev_proc_cpu: Dict[int, int] = {}

        for client in clients:
            key = (client["drm_minor"], client["drm_client_id"])
            prev = self._prev_counters.get(key, {})
            cur_eng = client["engines"]
            next_prev[key] = cur_eng

            pid = client["pid"]
            cpu_ticks, rss_kb = read_proc_cpu_mem(pid)
            cpu_usage_pct = None
            prev_cpu_ticks = self._prev_proc_cpu.get(pid)
            if cpu_ticks is not None:
                next_prev_proc_cpu[pid] = cpu_ticks
                if prev_cpu_ticks is not None and cpu_ticks >= prev_cpu_ticks:
                    delta_sec = (cpu_ticks - prev_cpu_ticks) / self._clk_tck
                    cpu_usage_pct = max(0.0, (delta_sec / self.period_s) * 100.0)

            engines = {}
            agg_engine_time = 0
            agg_cycles = 0
            agg_total_cycles = 0

            for eng_name, cur_vals in cur_eng.items():
                eng = self._compute_engine_util(prev.get(eng_name), cur_vals)
                engines[eng_name] = eng

                if eng["delta_engine_time"] is not None:
                    agg_engine_time += eng["delta_engine_time"]
                if eng["delta_cycles"] is not None:
                    agg_cycles += eng["delta_cycles"]
                if eng["delta_total_cycles"] is not None:
                    agg_total_cycles += eng["delta_total_cycles"]

            sample_clients.append(
                {
                    "pid": client["pid"],
                    "process_name": client["process_name"],
                    "drm_minor": client["drm_minor"],
                    "drm_client_id": client["drm_client_id"],
                    "driver": client["driver"],
                    "pdev": client["pdev"],
                    "frequencies": client.get("frequencies", []),
                    "cpu_usage_pct": cpu_usage_pct,
                    "memory_rss_kb": rss_kb,
                    "memory_rss_mib": (rss_kb / 1024.0) if rss_kb is not None else None,
                    "agg_delta_engine_time": agg_engine_time,
                    "agg_delta_cycles": agg_cycles,
                    "agg_delta_total_cycles": agg_total_cycles,
                    "engines": engines,
                }
            )

        self._prev_counters = next_prev
        self._prev_proc_cpu = next_prev_proc_cpu
        if self.sort_by == "cpu":
            sample_clients.sort(key=lambda c: c.get("cpu_usage_pct") or 0.0, reverse=True)
        elif self.sort_by == "mem":
            sample_clients.sort(key=lambda c: c.get("memory_rss_kb") or 0, reverse=True)
        else:
            sample_clients.sort(key=lambda c: c["agg_delta_engine_time"], reverse=True)

        return {
            "timestamp": ts_epoch,
            "iso_time": datetime.fromtimestamp(ts_epoch).isoformat(),
            "period_s": self.period_s,
            "num_clients": len(sample_clients),
            "clients": sample_clients,
        }

    def _run(self):
        while not self._stop.is_set():
            start = time.monotonic()
            ts_epoch = time.time()
            clients = scan_proc_drm_clients(include_freq=self.include_freq)
            sample = self._compute_sample(clients, ts_epoch)

            if self._log_fp:
                self._log_fp.write(json.dumps(sample, separators=(",", ":")) + "\n")
                self._log_fp.flush()

            with self._lock:
                self._latest = sample

            self._queue.put(sample)

            if self.callback:
                self.callback(sample)

            elapsed = time.monotonic() - start
            remaining = self.period_s - elapsed
            if remaining > 0:
                self._stop.wait(remaining)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        if self.log_path:
            self._log_fp = open(self.log_path, "a", encoding="utf-8")
        self._thread = threading.Thread(target=self._run, name="gpu-monitor", daemon=True)
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
            if self._latest is None:
                return None
            return dict(self._latest)

    def iter_samples(self):
        while not self._stop.is_set() or not self._queue.empty():
            try:
                yield self._queue.get(timeout=0.1)
            except queue.Empty:
                continue


def print_summary(sample: dict, top_n: int):
    print(f"[{sample['iso_time']}] clients={sample['num_clients']}")
    if top_n and top_n > 0:
        clients = sample["clients"][:top_n]
    else:
        clients = sample["clients"]

    for client in clients:
        busiest = []
        for eng_name, eng in client["engines"].items():
            pct = eng.get("utilization_pct")
            if pct is not None:
                busiest.append((pct, eng_name))
        busiest.sort(reverse=True)
        engines = ", ".join(f"{name}:{pct:.1f}%" for pct, name in busiest[:3])
        cpu_pct = client.get("cpu_usage_pct")
        cpu_str = f"{cpu_pct:.1f}%" if cpu_pct is not None else "n/a"
        rss_kb = client.get("memory_rss_kb")
        rss_mib = client.get("memory_rss_mib")
        if rss_kb is not None and rss_mib is not None:
            rss_str = f"{rss_kb} ({rss_mib:.1f} MiB)"
        else:
            rss_str = "n/a"
        print(
            f"  pid={client['pid']} name={client['process_name']} "
            f"minor={client['drm_minor']} client={client['drm_client_id']} "
            f"cpu={cpu_str} rss={rss_str} "
            f"{engines}"
        )


def update_max_utilization(summary: dict, sample: dict):
    for client in sample.get("clients", []):
        proc_key = (client.get("pid"), client.get("process_name", ""))
        per_proc = summary.setdefault(proc_key, {})

        for eng_name, eng in client.get("engines", {}).items():
            pct = eng.get("utilization_pct")
            if pct is None:
                continue
            if pct <= 0.0:
                continue
            prev = per_proc.get(eng_name)
            if prev is None or pct > prev:
                per_proc[eng_name] = pct


def print_final_max_utilization_summary(summary: dict):
    print("\nFinal max utilization per process:")
    if not summary:
        print("  No engine utilization samples collected.")
        return

    for (pid, name), engines in sorted(summary.items(), key=lambda x: (x[0][1], x[0][0])):
        if not engines:
            continue
        engines_str = ", ".join(
            f"{eng}:{pct:.1f}%" for eng, pct in sorted(engines.items(), key=lambda x: x[0])
        )
        print(f"  pid={pid} name={name}: {engines_str}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Intel per-process GPU monitor via DRM fdinfo")
    parser.add_argument("-p", "--period", type=float, default=2.0, help="Sampling period in seconds")
    parser.add_argument("-n", "--iterations", type=int, default=0, help="Number of samples (0 = unlimited)")
    parser.add_argument("--duration", type=float, default=0.0, help="Monitor duration in seconds (0 = unlimited)")
    parser.add_argument("--log-path", default=None, help="JSONL output path (default: /tmp/gpu_monitor_<timestamp>.jsonl)")
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL logging")
    parser.add_argument("--no-freq", action="store_true", help="Disable Intel frequency probing")
    parser.add_argument("--summary", action="store_true", help="Print compact summary per sample")
    parser.add_argument("--top", type=int, default=0, help="Max clients to print in summary mode (default: all)")
    parser.add_argument(
        "--sort-by",
        choices=["gpu", "cpu", "mem"],
        default="gpu",
        help="Sort clients by gpu(engine time), cpu, or mem",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Optional command to run while monitoring, use: -- cmd args")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    callback = (lambda sample: print_summary(sample, args.top)) if args.summary else None
    log_path = None if args.no_log else args.log_path

    monitor = GpuMonitor(
        period_s=args.period,
        log_path=log_path,
        include_freq=not args.no_freq,
        sort_by=args.sort_by,
        callback=callback,
    )

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
        print(f"Logging GPU samples to {monitor.log_path}")

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
