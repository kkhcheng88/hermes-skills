---
name: llm-proxy-debug
description: Debug 400/401 errors with third-party LLM proxies (e.g. huoyuanqudao.cn, custom OpenAI-compatible endpoints). Covers Hermes is_kimi detection, reasoning parameter issues, and config-based fixes for multi-model proxies.
version: 1.0.0
author: Kars
license: MIT
metadata:
  hermes:
    tags: [llm, proxy, api, 400-error, kimi, debugging, config]
    related_skills: [systematic-debugging]
---

# LLM Proxy 400 Error Debugging

## Overview

Third-party LLM proxies often cause HTTP 400 errors in Hermes. The root cause is usually one of:

1. **Hermes `is_kimi` misdetection** — proxy domain not in hardcoded Kimi list
2. **Reasoning parameters rejected** — `reasoning_effort`, `extra_body.thinking`, or `stream=true` not supported
3. **Rate limiting / intermittent 400s** — proxy backend rotation causes sporadic failures
4. **Multi-model proxy confusion** — same endpoint serves both Kimi and non-Kimi models

## Quick Diagnosis Script

Create a test script to isolate the issue:

```python
import requests
import json
import time

BASE_URL = "https://your-proxy.com/v1"
API_KEY = "sk-..."
MODEL = "your-model-name"

def test_request(name, payload):
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    print(f"\n=== {name} ===")
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Response: {r.text[:500]}")
        return r.status_code
    except Exception as e:
        print(f"Error: {e}")
        return -1

# Test combinations
payload_minimal = {"model": MODEL, "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 10}
payload_stream = {**payload_minimal, "stream": True}
payload_reasoning = {**payload_minimal, "reasoning_effort": "medium"}
payload_thinking = {**payload_minimal, "extra_body": {"thinking": {"type": "enabled", "budget_tokens": 1024}}}

for name, payload in [("Minimal", payload_minimal), ("Stream", payload_stream), 
                      ("Reasoning", payload_reasoning), ("Thinking", payload_thinking)]:
    test_request(name, payload)
    time.sleep(1)

# Check for intermittent pattern
for i in range(10):
    test_request(f"Run #{i+1}", payload_minimal)
    time.sleep(0.5)
```

## Interpreting Results

| Pattern | Likely Cause | Fix |
|---------|-------------|-----|
| All 400 | API key or endpoint wrong | Verify credentials |
| Reasoning/Thinking 400 only | Proxy rejects reasoning params | Disable reasoning in agent config |
| Stream 400 only | No streaming support | Disable streaming |
| **Stream + reasoning_effort 400** | **Proxy rejects top-level reasoning_effort when streaming** | **Move reasoning_effort into extra_body or disable streaming** |
| Intermittent 400 | Rate limiting / backend rotation | Add retry logic |

## Critical Finding: Stream + reasoning_effort Conflict

Some proxies (e.g., huoyuanqudao.cn) accept `reasoning_effort` as a top-level
parameter when `stream: false`, but **reject it with HTTP 400 when `stream: true`**.

Test matrix for huoyuanqudao.cn proxy:

| stream | reasoning_effort location | Result |
|--------|---------------------------|--------|
| false | top-level | 200 |
| true | top-level | **400** |
| true | inside extra_body | 200 |

**Workaround:** If your proxy shows this pattern, either:
1. Set `agent.streaming: false` in Hermes config
2. Or patch Hermes to always nest `reasoning_effort` inside `extra_body`
3. Or clear `agent.reasoning_effort` to stop sending the parameter

## Hermes is_kimi Detection

Hermes detects Kimi in multiple places:

1. **Domain-based** (`run_agent.py` ~6807):
```python
is_kimi = any(domain in base_url for domain in ("api.kimi.com", "moonshot.ai", "moonshot.cn"))
```

2. **Model name-based** (`run_agent.py`): If model contains "kimi" or "K2.6", `is_kimi=True`.

3. **Custom providers** (`hermes_cli/config.py`): If provider name is "kimi" or base_url contains moonshot domains.

**Critical file for proxy users:** `agent/transports/chat_completions.py` ~line 183 — this is where `is_kimi` is read from params and determines whether reasoning params are injected into the API request.

## Solutions (in order of preference)

### Option 1: Force is_kimi=False in chat_completions.py (Recommended)

If your proxy is OpenAI-compatible but Hermes misdetects model name as Kimi,
force disable Kimi-native parameters at the transport layer:

```python
# File: agent/transports/chat_completions.py ~line 183
# Change:
#     is_kimi = params.get("is_kimi", False)
# To:
    # Force is_kimi=False for custom proxies that don't support Kimi-native params
    # (reasoning_effort, extra_body.thinking). See: llm-proxy-debug skill.
    is_kimi = False
```

This prevents Hermes from sending:
- `reasoning_effort` (top-level parameter)
- `extra_body.thinking` (Kimi-native thinking control)

### Option 2: Disable reasoning globally
Set `agent.reasoning_effort: ""` or `"none"` in Hermes config. Less reliable as
some code paths may still add reasoning params.

### Option 3: Rename model to avoid detection
Change model name from `K2.6` to `custom-k2.6` so Hermes doesn't detect `is_kimi`.

### Option 4: Add domain to kimi_domains config (Advanced)
If proxy actually supports Kimi features, add domain to detection list in
run_agent.py ~6807. Only do this if proxy truly supports Kimi-native API.

## Key Files

- run_agent.py ~6807: is_kimi domain check
- agent/transports/chat_completions.py ~200: build_kwargs with reasoning params
- hermes_constants.py: parse_reasoning_effort function

## Pitfalls

- Don't assume 400 = parameter issue; test minimal request first
- Intermittent 400s are usually rate limiting, not parameters
- Adding domain to is_kimi can break non-Kimi models on same proxy
- Always test with diagnosis script before modifying source
