"""Find out what this machine can run, so `model = "auto"` works from a phone
to a workstation. Nothing here is required: every lookup degrades to "CPU,
unknown memory" when a library or OS call is missing.
"""
from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Hardware:
    device: str              # "cuda", "mps" or "cpu"
    accelerator: str         # GPU name, or ""
    vram_gb: float           # 0 on CPU; unified memory on Apple counts as RAM
    ram_gb: float
    cpu_cores: int
    arch: str

    @property
    def gpu(self) -> bool:
        return self.device != "cpu"

    def to_dict(self) -> dict:
        return {**self.__dict__, "gpu": self.gpu}


def _ram_gb() -> float:
    try:
        import psutil
        return psutil.virtual_memory().total / 2**30
    except ImportError:
        pass
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
    except (ValueError, OSError, AttributeError):
        pass
    if os.name == "nt":
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MEMORYSTATUSEX()
        m.dwLength = ctypes.sizeof(m)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return m.ullTotalPhys / 2**30
    return 0.0


@lru_cache(maxsize=1)
def detect() -> Hardware:
    ram = _ram_gb()
    cores = os.cpu_count() or 1
    arch = platform.machine().lower()
    forced = os.environ.get("AGENTWIKI_DEVICE")      # e.g. "cpu" to keep the GPU free
    try:
        import torch
        if forced != "cpu" and torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            return Hardware("cuda", p.name, p.total_memory / 2**30, ram, cores, arch)
        if forced != "cpu" and getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return Hardware("mps", "Apple GPU", 0.0, ram, cores, arch)
    except ImportError:
        pass
    try:  # faster-whisper's backend can see CUDA without torch installed
        import ctranslate2
        if forced != "cpu" and ctranslate2.get_cuda_device_count() > 0:
            return Hardware("cuda", "CUDA GPU", 0.0, ram, cores, arch)
    except ImportError:
        pass
    return Hardware("cpu", "", 0.0, ram, cores, arch)


def pick(tiers: list[tuple[float, float, str]], hw: Hardware | None = None) -> str:
    """First tier whose (min VRAM GB, min RAM GB) this machine meets.

    VRAM 0 in a tier means "no GPU needed". Tiers go from biggest to smallest;
    the last one should be (0, 0, smallest) so something always matches.
    """
    hw = hw or detect()
    for min_vram, min_ram, value in tiers:
        if min_vram and not (hw.device == "cuda" and hw.vram_gb >= min_vram):
            continue
        if hw.ram_gb and hw.ram_gb < min_ram:
            continue
        return value
    return tiers[-1][2]
