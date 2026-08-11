\# PressStartAI



Local AI-powered Windows application that converts long-form gaming videos into high-quality YouTube Shorts.



\## Features



\- Local AI processing

\- No cloud APIs

\- No subscriptions

\- Automatic highlight detection

- Intelligent 9:16 reframing

\- Auto 9:16 reframing

\- AI-generated captions

\- Hook generation

\- Title generation

\- Description generation

\- Hashtag generation

\- Thumbnail prompt generation



\## Hardware Target



\- Windows 11

\- Intel Core Ultra 7 155H

\- Intel Arc Graphics

\- Intel AI Boost NPU

\- 32 GB RAM



\## Status



Project under development.



## Checkpoint / Resume

PressStartAI now keeps reusable checkpoints in the configurable cache folder.

Start the application normally:

```cmd
python -m src.cli
```

After confirming recordings, choose:
- **Resume Previous Run** — continue the most recent run for the same input recordings.
- **Fresh Run** — create a new output run. If compatible cache exists, the CLI asks whether to reuse it or rebuild.
- **Clear Cache / Checkpoints** — available from the main menu; final output videos are never removed.

Cache compatibility is validated using input identity, stage code/config fingerprints, payload checksums, and required-file checks. If an upstream stage must rebuild, dependent downstream stages rebuild as well.


## Dynamic CPU / RAM utilization

Performance-only resource management is enabled by default:

- target CPU utilization: 85%
- target RAM utilization: 70%
- RAM pressure throttle: 82%
- reserve: 1 logical CPU for Windows
- worker counts are chosen dynamically from current CPU/RAM headroom
- synchronization audio extraction can use 2 workers
- analysis/source clip extraction can use multiple workers
- final Short rendering can use up to 4 workers when RAM permits
- AI/ASR model inference remains single-model to avoid duplicate model memory and quality/stability risk

These settings do not change final encode quality, layout, selection thresholds, or AI models.
