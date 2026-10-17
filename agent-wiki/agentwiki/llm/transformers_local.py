"""An LLM that runs inside this process with Hugging Face transformers.

No server to start or keep running. Slower than a tuned server (Ollama,
llama.cpp, vLLM) on the same hardware, because it does not batch requests or
use quantised kernels, but it works anywhere torch does.
"""
from __future__ import annotations

import logging

from .. import hardware
from ..registry import register
from .base import LLM

log = logging.getLogger(__name__)

# (min VRAM GB, min RAM GB, model). Sizes assume 16-bit weights.
AUTO_TIERS = [
    (70, 0, "google/gemma-4-31B-it"),
    (30, 0, "google/gemma-4-12B-it"),
    (12, 0, "google/gemma-4-E4B-it"),
    (6, 0, "google/gemma-4-E2B-it"),
    (0, 32, "google/gemma-4-E4B-it"),   # CPU with plenty of RAM: slow but good
    (0, 16, "google/gemma-4-E2B-it"),
    (0, 6, "Qwen/Qwen2.5-1.5B-Instruct"),
    (0, 0, "Qwen/Qwen2.5-0.5B-Instruct"),  # phones; expect weak tags, prefer the local enricher
]


@register("llm", "transformers")
class TransformersLLM(LLM):
    def __init__(self, model: str = "auto", device: str = "auto", dtype: str = "auto",
                 max_input_tokens: int = 16384):
        self.model = hardware.pick(AUTO_TIERS) if model == "auto" else model
        self.device = hardware.detect().device if device == "auto" else device
        self.dtype = dtype
        self.max_input_tokens = max_input_tokens
        self._tok = None
        self._lm = None

    def _ping(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except ImportError:
            return False

    def _load(self):
        if self._lm is None:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            dtype = self.dtype
            if dtype == "auto":
                # 16-bit on GPUs. On CPU keep the checkpoint's dtype (usually
                # bf16), which halves RAM; modern CPUs run it fine.
                dtype = {"cuda": torch.bfloat16, "mps": torch.float16}.get(self.device, "auto")
            elif isinstance(dtype, str):
                dtype = getattr(torch, dtype)
            log.info("loading %s on %s", self.model, self.device)
            self._tok = AutoTokenizer.from_pretrained(self.model)
            kw = {"dtype": dtype}
            if self.device == "cuda":
                kw["device_map"] = "auto"     # spreads big models over several GPUs
            try:
                lm = AutoModelForCausalLM.from_pretrained(self.model, **kw)
            except ValueError:
                # Multimodal checkpoints (Gemma 4 E2B/E4B) register under a different auto class.
                from transformers import AutoModelForImageTextToText
                lm = AutoModelForImageTextToText.from_pretrained(self.model, **kw)
            if self.device != "cuda":
                lm = lm.to(self.device)
            self._lm = lm.eval()
        return self._tok, self._lm

    def complete(self, prompt, system=None, *, max_tokens=1024, temperature=0.2, json_mode=False):
        import torch
        tok, lm = self._load()
        if json_mode:
            prompt += "\n\nReply with only the JSON object."
        messages = ([{"role": "system", "content": system}] if system else []) + \
                   [{"role": "user", "content": prompt}]
        inputs = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt",
                                         return_dict=True, enable_thinking=False)
        ids = inputs["input_ids"][:, -self.max_input_tokens:]
        mask = inputs["attention_mask"][:, -self.max_input_tokens:]
        with torch.inference_mode():
            out = lm.generate(input_ids=ids.to(lm.device), attention_mask=mask.to(lm.device),
                              max_new_tokens=max_tokens, do_sample=temperature > 0,
                              temperature=temperature if temperature > 0 else None,
                              pad_token_id=tok.pad_token_id or tok.eos_token_id)
        return tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True).strip()
