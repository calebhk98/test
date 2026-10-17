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
        self._tokenizer = None
        self._language_model = None

    def _ping(self) -> bool:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except ImportError:
            return False

    def _load(self):
        if self._language_model is None:
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
            self._tokenizer = AutoTokenizer.from_pretrained(self.model)
            options = {"dtype": dtype}
            if self.device == "cuda":
                options["device_map"] = "auto"     # spreads big models over several GPUs
            try:
                language_model = AutoModelForCausalLM.from_pretrained(self.model, **options)
            except ValueError:
                # Multimodal checkpoints (Gemma 4 E2B/E4B) register under a different auto class.
                from transformers import AutoModelForImageTextToText
                language_model = AutoModelForImageTextToText.from_pretrained(self.model, **options)
            if self.device != "cuda":
                language_model = language_model.to(self.device)
            self._language_model = language_model.eval()
        return self._tokenizer, self._language_model

    def complete(self, prompt, system=None, *, max_tokens=1024, temperature=0.2, json_mode=False):
        import torch
        tokenizer, language_model = self._load()
        if json_mode:
            prompt += "\n\nReply with only the JSON object."
        messages = ([{"role": "system", "content": system}] if system else []) + \
                   [{"role": "user", "content": prompt}]
        inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt",
                                               return_dict=True, enable_thinking=False)
        input_ids = inputs["input_ids"][:, -self.max_input_tokens:]
        attention_mask = inputs["attention_mask"][:, -self.max_input_tokens:]
        with torch.inference_mode():
            generated = language_model.generate(
                input_ids=input_ids.to(language_model.device),
                attention_mask=attention_mask.to(language_model.device),
                max_new_tokens=max_tokens, do_sample=temperature > 0,
                temperature=temperature if temperature > 0 else None,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)
        return tokenizer.decode(generated[0, input_ids.shape[1]:], skip_special_tokens=True).strip()
