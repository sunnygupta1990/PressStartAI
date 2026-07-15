# PressStartAI --- AI Technical Handoff, Build, Architecture, Maintenance, and Recovery Guide

> **DOCUMENT PURPOSE --- READ THIS BEFORE TOUCHING THE CODE**
>
> This is an **AI-first technical README and permanent project handoff**
> for PressStartAI. It is intentionally detailed. A future AI coding
> assistant, maintainer, or new developer should read this file **before
> installing dependencies, changing architecture, replacing AI models,
> fixing errors, optimizing performance, or adding features**.
>
> **Current accepted project state:** the PressStartAI **core end-to-end
> pipeline is 100% functionally complete** and has passed a real CLI
> production verification on the original development hardware.
>
> **Repository:** `https://github.com/sunnygupta1990/PressStartAI`
>
> **Owner / author:** Sunny Gupta
>
> **Project version in `pyproject.toml`:** `0.1.0`
>
> **Primary operating system:** Windows 11 Pro
>
> **Primary language runtime:** Python 3.12.x, specifically verified
> with Python 3.12.10
>
> This project is not a generic CUDA/NVIDIA reference implementation. It
> was designed, built, debugged, and verified around a **specific Intel
> Core Ultra Windows laptop**. Hardware compatibility must be checked
> before a new build is attempted.

------------------------------------------------------------------------

# 0. CRITICAL HARDWARE COMPATIBILITY GATE --- MUST BE READ FIRST

## STOP: do not install or modify PressStartAI until the target machine is checked

PressStartAI was developed and verified on the following hardware:

  Component                          Verified development hardware
  ---------------------------------- ---------------------------------------
  Operating system                   Windows 11 Pro
  CPU                                Intel Core Ultra 7 155H
  RAM                                32 GB
  Integrated GPU                     Intel Arc integrated graphics
  NPU                                Intel AI Boost NPU
  Storage                            500 GB SSD
  NVIDIA GPU                         None
  CUDA                               Not used / not available
  Python                             3.12.10
  Architecture goal                  CPU / Intel iGPU / Intel NPU friendly
  Preferred acceleration framework   OpenVINO where practical
  AI execution model                 Fully local
  Paid cloud API requirement         None
  Subscription requirement           None

## Mandatory AI instruction for a new machine

If an AI assistant is helping a user install or rebuild this repository
on a new computer, the AI **must ask for and verify the following before
giving build commands**:

1.  Exact Windows version and edition.
2.  Exact CPU model.
3.  Total installed RAM.
4.  GPU model or models.
5.  Whether an Intel NPU is present.
6.  Whether NVIDIA CUDA hardware is present.
7.  Available free SSD space.
8.  Installed Python version.
9.  Whether Python is 64-bit.
10. Installed Git version.
11. Whether FFmpeg is installed and available from Command Prompt.
12. Whether Ollama is installed.
13. Ollama version.
14. Whether `gemma3:4b` is installed locally.
15. Whether the machine has internet access for the initial Python and
    Hugging Face model downloads.
16. Whether corporate SSL inspection, proxying, certificate replacement,
    or restricted administrator permissions are present.
17. Whether Command Prompt can be used.
18. Whether PowerShell script execution is restricted.
19. Whether OpenVINO detects `CPU`, `GPU`, and, when expected, `NPU`.
20. The intended input video resolution, frame rate, codec, duration,
    and approximate file size.

### Recommended first diagnostic commands on a new Windows machine

Run these from **Command Prompt** and save all output before proceeding:

``` bat
winver
systeminfo
wmic cpu get name
wmic computersystem get TotalPhysicalMemory
wmic path win32_VideoController get name
where python
python --version
python -c "import platform, struct; print(platform.platform()); print(struct.calcsize('P') * 8)"
git --version
ffmpeg -version
ollama --version
ollama list
```

After the PressStartAI environment is installed, also run:

``` bat
python -c "from openvino import Core; core = Core(); print(core.available_devices)"
```

### Hardware compatibility classification

A future AI should classify the machine before proceeding:

#### Class A --- closest to the verified system

-   Windows 11
-   Intel Core Ultra platform
-   32 GB RAM or more
-   Intel Arc integrated GPU
-   Intel AI Boost NPU
-   Python 3.12.x

This is the safest target.

#### Class B --- probably adaptable but not yet verified

Examples:

-   newer Intel Core Ultra CPU
-   Intel Arc GPU but different generation
-   Intel NPU with different OpenVINO device behavior
-   16 GB RAM
-   Windows 11 on a conventional Intel CPU
-   AMD CPU or AMD GPU
-   NVIDIA GPU system without matching the current CPU-oriented model
    configuration

Do **not** assume the existing dependency set, device routing, model
dtype, memory use, or timing will behave identically.

#### Class C --- unsupported until deliberately ported and verified

Examples:

-   macOS
-   Linux
-   Python 3.13+
-   Python below 3.12
-   low-memory systems
-   systems without enough storage for local models and intermediate
    video files
-   ARM Windows unless explicitly ported
-   cloud notebooks
-   containers without media codecs and local Ollama access

A future AI must treat these as a **porting project**, not as a normal
installation.

## Why this warning exists

The dependency environment contains large AI, audio, video, PyTorch,
OpenVINO, Hugging Face, ASR, and experimental packages. Several failures
during development were caused by interactions among:

-   PyTorch
-   Torchaudio
-   TorchCodec
-   FFmpeg shared libraries
-   Windows DLL loading
-   SSL certificates
-   model language detection
-   short audio chunks
-   local Ollama executable discovery
-   AI output formatting
-   unsupported script contamination in generated publishing text

The current application works because those problems were handled in the
architecture and implementation. A new AI must **not casually
"modernize" the stack** by upgrading everything.

------------------------------------------------------------------------

# 1. AI MAINTAINER OPERATING RULES

This section is written directly for future AI coding assistants.

## 1.1 Read the repository before editing

Before changing code:

1.  Read this entire file.
2.  Inspect the current Git branch.
3.  Run `git status`.
4.  Inspect the latest commits.
5.  Read the actual current file being changed.
6.  Trace its imports, models, consumers, verification scripts, and
    output contracts.
7.  Check whether a historical failed experiment already covers the
    proposed idea.
8.  Make the smallest architecturally correct change.
9.  Verify the changed component.
10. Verify the affected integration path.
11. Run the production CLI when the change can affect the end-to-end
    pipeline.

Never infer the current implementation only from an old chat handoff.

## 1.2 Source of truth order

Use this priority:

1.  **Current checked-out repository code**
2.  **Current Git history and clean/dirty status**
3.  **This AI README**
4.  Current verification output
5.  Historical handoff/chat notes

If historical notes conflict with current code, inspect Git history and
current code. The project progressed through many milestones; old
stopping points such as "verify HighlightSelector" are obsolete.

## 1.3 Current accepted status

The accepted current state is:

**100% core end-to-end pipeline functionally complete.**

This means the core pipeline successfully accepts a gaming video and can
produce approved, portrait, captioned Short packages with publishing
metadata.

It does **not** mean all future product work is finished. UI, installer,
broad cross-game validation, repository cleanup, long-video tuning, and
commercial productization are separate future phases.

## 1.4 Owner workflow preferences

Sunny Gupta is a non-programmer for this Python project.

When guiding Sunny:

-   Use exact Windows Command Prompt commands.
-   Give one small step at a time.
-   Do not give unnecessary programming theory unless asked.
-   After giving a verification command, stop and wait for terminal
    output.
-   Do not restart completed work.
-   Do not repeat known failed experiments without a genuinely new
    technical reason.
-   If only 1--2 lines need changing, identify the exact small change.
-   If more than 1--2 lines need changing, provide the **full complete
    replacement file**.
-   Do not use broad find-and-replace instructions for substantial
    changes.
-   Production services must remain generic for arbitrary gaming videos.
-   The Returnal test clip is a fixture, not production-specific
    business logic.
-   Never hard-code one test video's timestamps, transcript, rank,
    category, or metadata into a production service.

------------------------------------------------------------------------

# 2. PROJECT MISSION

PressStartAI is a local AI-powered Windows application that converts
long-form gaming footage into YouTube Short packages.

The product was created for the gaming channel:

`Press Start with Sunny`

The target content style includes:

-   Hindi commentary
-   Hinglish commentary
-   English commentary
-   story-mode gaming
-   natural reactions
-   funny failures
-   frustration and rage moments
-   boss fights
-   combat
-   trophy hunting
-   live-stream-derived moments
-   recorded gameplay

The owner is naturally quiet during some gameplay. Therefore, highlight
detection **must not assume that constant shouting equals quality**. A
valuable moment can be identified through a combination of speech,
visual motion, game audio intensity, commentary meaning, visual context,
and multimodal AI reasoning.

## Core product philosophy

The application should minimize manual editing.

Desired high-level experience:

``` text
Gaming video
    ↓
Local analysis
    ↓
Interesting moments discovered
    ↓
Weak/duplicate moments removed
    ↓
Commentary and visual context understood
    ↓
Best moments approved
    ↓
Portrait Shorts rendered
    ↓
Captions generated and burned
    ↓
Publishing metadata generated
    ↓
Ready-to-review Short packages
```

## Local-first constraints

The application is designed around:

-   local AI
-   no paid cloud APIs
-   no paid AI services
-   no recurring AI subscription dependency
-   CPU/iGPU/NPU-friendly architecture
-   OpenVINO preferred where useful
-   Ollama for local language/vision reasoning
-   local ASR
-   local FFmpeg rendering

Do not introduce a mandatory paid API without explicit owner approval.

------------------------------------------------------------------------

# 3. CURRENT FEATURE INVENTORY

The following capabilities are implemented in the completed core
pipeline.

## 3.1 Video ingestion

-   accepts an arbitrary input video path through the CLI
-   validates and loads video information
-   determines source duration
-   supports the production pipeline instead of requiring a hard-coded
    test path

## 3.2 Audio extraction

-   extracts audio from the source video
-   creates analysis-friendly audio
-   uses FFmpeg
-   mono 16 kHz audio was verified during development

## 3.3 Voice activity detection

-   Silero VAD detects human speech regions
-   SoundFile is used for audio loading
-   speech timestamps are preserved

## 3.4 Speech-region merging and chunking

-   nearby VAD regions are merged
-   very short fragments are reduced
-   maximum chunk duration is controlled
-   exported speech chunks retain their original source-video timeline
    positions

This is important because tiny chunks caused severe ASR
language-detection instability.

## 3.5 Local ASR

Primary ASR:

`Qwen/Qwen3-ASR-0.6B`

Python package:

`qwen-asr==0.0.6`

The primary ASR was selected after testing multiple alternatives.

The pipeline supports commentary that may contain:

-   Hindi
-   Hinglish
-   English

ASR output is mapped back to the source timeline.

### Important ASR limitation

Qwen Hindi transcription can still be imperfect. The architecture should
not assume every Hindi word is exact.

Highlight reasoning should use the transcript as a signal, not as
infallible ground truth.

## 3.6 Scene detection

-   PySceneDetect content-based scene detection
-   short-scene merging
-   source timeline preservation

## 3.7 Transcript-to-scene mapping

Each transcript segment is assigned to the scene with the **maximum
temporal overlap**.

This was deliberately implemented to prevent one long ASR segment from
being duplicated into several adjacent scenes.

Do not replace this with naive "any overlap means attach to scene" logic
unless the duplication problem is deliberately solved another way.

## 3.8 Motion analysis

-   OpenCV video decoding
-   sampled frame analysis
-   grayscale conversion
-   Gaussian blur
-   absolute frame difference
-   average motion score
-   maximum motion score

Motion is one highlight signal.

## 3.9 Audio intensity analysis

-   SoundFile audio loading
-   RMS analysis
-   average RMS
-   peak-window RMS

Important: this signal is based on the **mixed gameplay + commentary
audio**.

It is a general intensity signal.

It is **not pure voice energy**.

## 3.10 Highlight feature extraction

Per scene, the system combines information such as:

-   scene start
-   scene end
-   scene duration
-   transcript text
-   whether speech exists
-   speech character count
-   speech word count
-   average motion
-   maximum motion
-   average audio RMS
-   maximum audio RMS

## 3.11 Heuristic highlight scoring

The original scoring design normalized scene features and combined:

-   motion
-   speech
-   audio

Historical first-version weights were:

-   motion: 45%
-   speech word count: 30%
-   audio average RMS: 25%

These weights were explicitly considered provisional.

A future AI tuning scoring must inspect the current `HighlightScorer`
implementation before assuming these historical values are unchanged.

## 3.12 Candidate selection

-   minimum score filtering
-   maximum candidate count
-   ranked candidates
-   padding before a scene
-   padding after a scene
-   video-boundary clamping

## 3.13 Overlap resolution

Candidate windows can overlap because of scene adjacency and padding.

The pipeline includes overlap handling so duplicate or heavily
overlapping highlight windows are not blindly carried forward as
independent final moments.

## 3.14 Highlight clip generation

-   source video clipping
-   audio retained
-   generated MP4 highlight clips
-   clip metadata preserved for later reasoning and export

## 3.15 Commentary AI reasoning

Local AI reasoning analyzes commentary context.

The pipeline includes:

-   local Ollama invocation
-   executable path handling
-   model invocation
-   AI response parsing
-   Markdown-fence/JSON extraction
-   ANSI/control-sequence sanitization
-   structured commentary analysis

The local model used and verified is:

`gemma3:4b`

## 3.16 Commentary analysis combination

Commentary reasoning outputs are combined with candidate information for
downstream multimodal analysis.

## 3.17 Representative frame extraction

Representative visual frames are extracted from candidate clips.

These frames provide visual context to the local visual AI.

## 3.18 Visual AI reasoning

Local visual reasoning uses `gemma3:4b`.

The visual AI model is warmed up once before candidate reasoning.

This area was a major performance bottleneck and was deliberately
optimized.

Historical early timing:

-   visual reasoning rank 1: about 100.29 seconds
-   visual reasoning rank 4: about 101.14 seconds

After optimization, verified timing was approximately:

-   visual AI warmup: 2.61 seconds
-   visual reasoning rank 1: 11.56 seconds
-   visual reasoning rank 4: 11.82 seconds

Do not reintroduce repeated model cold starts or an unnecessarily
expensive frame strategy without benchmarking.

## 3.19 Multimodal AI fusion

The pipeline combines:

-   commentary analysis
-   visual analysis
-   candidate information

The fusion stage makes a stronger local AI decision about whether a
candidate is genuinely valuable as a gaming Short.

## 3.20 Final keep/reject decision

-   multimodal keep/reject decision
-   confidence
-   category/context
-   final filtering

## 3.21 Final approved highlight selection

Only approved highlights continue into the final Short-building path.

## 3.22 Decision-to-clip linking

Approved AI decisions are linked back to the correct generated media
clips.

Timeline, rank, and media relationships must remain consistent.

## 3.23 Final highlight export

The final highlight package includes:

-   approved media
-   structured metadata
-   UTF-8 JSON export

UTF-8 handling is important because commentary and generated metadata
may contain Hindi and other Unicode characters.

## 3.24 Portrait 9:16 rendering

The Short builder produces:

`1080 x 1920`

portrait output.

The pipeline includes portrait conversion/reframing logic suitable for
YouTube Shorts.

## 3.25 Intelligent reframing / visual tracking

The current core feature set includes face/visual tracking and automatic
9:16 reframing.

When changing this area, verify:

-   target selection
-   crop center stability
-   source aspect ratio handling
-   edge clamping
-   face/ROI continuity
-   rapid camera movement
-   gameplay HUD preservation
-   whether the tracked subject is Sunny's face cam, gameplay action, or
    another relevant ROI

Do not assume a single crop strategy works for all games.

## 3.26 Caption segment generation

Transcript information is converted into caption segments aligned to the
Short timeline.

## 3.27 SRT generation

The pipeline writes `.srt` subtitle files.

The final verified Short packages contained caption files.

## 3.28 Caption rendering

Captions are burned into the rendered Short.

The repository includes dedicated caption renderer and caption segment
builder verification scripts.

## 3.29 Hook generation

The publishing metadata generator creates a hook.

Generated text is validated.

A real failure occurred where a hook contained unwanted Tamil script:

`OMG! செக் பண்ணு!`

The metadata validation was fixed so unsupported script contamination is
rejected rather than silently accepted.

Do not remove this type of validation.

## 3.30 Title generation

Local AI generates a suggested YouTube Short title.

## 3.31 Description generation

Local AI generates a suggested description.

The content style is intended for the `Press Start with Sunny` gaming
channel and Indian/Hindi/Hinglish gaming audience.

## 3.32 Hashtag generation

Local AI generates hashtags.

## 3.33 Thumbnail prompt generation

Local AI generates a thumbnail creative prompt.

Channel creative defaults historically include:

-   Sunny's real facial identity must be preserved when an actual face
    reference is available to the image-generation workflow
-   black hoodie by default
-   expression should match the video mood
-   blue/black gaming branding
-   genuine reaction emphasis

The video-processing repository generates the **prompt/metadata**. It
does not magically possess Sunny's reference photo unless a later
image-generation workflow explicitly receives one.

## 3.34 Final per-Short package

A verified output package follows a structure similar to:

``` text
output/
└── runs/
    └── <run_id>/
        ├── ...
        └── shorts/
            ├── short_001/
            │   ├── final_short.mp4
            │   └── captions.srt
            └── short_004/
                ├── final_short.mp4
                └── captions.srt
```

The exact current output structure must be read from the current
pipeline and Short package builder before being changed.

## 3.35 CLI result output

The CLI prints a human-readable result including:

-   source video
-   video duration
-   final highlight count
-   exported file count
-   Short package count
-   total pipeline time
-   output folder
-   per-rank final Short path
-   caption path
-   category
-   confidence
-   hook
-   title
-   description
-   hashtags
-   thumbnail prompt

## 3.36 Stage timing and observability

The CLI prints:

`PIPELINE STAGE TIMINGS`

Timing support was added through pipeline timing models/services.

Verified timing functionality included:

-   `PipelineStageTiming`
-   `PipelineStageRunner`
-   `PipelineResult` timing
-   `HighlightPipeline` timing result
-   CLI timing output

This observability must be preserved. Performance changes should be
evaluated using stage timings, not subjective impressions.

------------------------------------------------------------------------

# 4. VERIFIED END-TO-END ARCHITECTURE

## 4.1 Complete logical flow

``` text
INPUT GAMING VIDEO
        │
        ▼
VideoLoader
        │
        ├── validates/loads source
        └── obtains video duration and source information
        │
        ▼
AudioExtractor
        │
        └── extracts analysis audio
        │
        ▼
Silero VoiceActivityDetector
        │
        └── identifies likely human speech regions
        │
        ▼
SpeechChunkExtractor
        │
        ├── merges nearby speech
        ├── limits chunk duration
        ├── exports WAV chunks
        └── preserves original video timestamps
        │
        ▼
QwenASR / TranscriptionPipeline
        │
        ├── local Qwen3-ASR-0.6B
        ├── Hindi/Hinglish/English commentary
        └── returns ASRSegment objects on original timeline
        │
        ├──────────────────────────────────────────────┐
        │                                              │
        ▼                                              ▼
SceneDetector                                   AudioAnalyzer
        │                                              │
        ├── content scene detection                    ├── average RMS
        └── short-scene merge                          └── peak RMS
        │
        ▼
SceneTranscriptMapper
        │
        └── maximum temporal overlap assignment
        │
        ▼
MotionAnalyzer
        │
        ├── sampled frames
        ├── frame difference
        ├── average motion
        └── maximum motion
        │
        └──────────────────────┬───────────────────────┘
                               ▼
                    HighlightFeatureExtractor
                               │
                               ▼
                        HighlightScorer
                               │
                               ▼
                       HighlightSelector
                               │
                               ├── score threshold
                               ├── top candidate count
                               └── before/after padding
                               │
                               ▼
                    HighlightOverlapResolver
                               │
                               ▼
                    HighlightClipGenerator
                               │
                               ▼
                  Commentary AI reasoning
                               │
                               ▼
                Commentary analysis combination
                               │
                               ▼
                 Representative frame extraction
                               │
                               ▼
                    Visual AI model warmup
                               │
                               ▼
                    Visual AI reasoning
                               │
                               ▼
                    Multimodal AI fusion
                               │
                               ▼
                Final approved highlight selection
                               │
                               ▼
                  Decision-to-clip linking
                               │
                               ▼
                  Final highlight package export
                               │
                               ▼
                  Final YouTube Short builder
                               │
             ┌─────────────────┼─────────────────────┐
             │                 │                     │
             ▼                 ▼                     ▼
      1080x1920 render   Caption segments     Publishing metadata
             │                 │                     │
             ▼                 ▼                     ├── hook
      intelligent crop       SRT file                ├── title
             │                 │                     ├── description
             ▼                 ▼                     ├── hashtags
      portrait video     caption burn-in             └── thumbnail prompt
             │                 │
             └─────────────────┴─────────────────────┐
                                                     ▼
                                         FINAL SHORT PACKAGE
                                                     │
                                                     ▼
                                           CLI result + timings
```

## 4.2 Why the architecture is staged

The system deliberately does not send the entire raw long video directly
to one AI prompt.

Instead it reduces the problem progressively:

1.  detect speech
2.  detect scenes
3.  measure motion and audio
4.  score scenes cheaply
5.  select a smaller candidate set
6.  resolve overlap
7.  generate clips
8.  run local language reasoning
9.  extract representative visual evidence
10. run visual reasoning only on shortlisted moments
11. fuse signals
12. approve the strongest moments
13. spend rendering and metadata work only on approved moments

This architecture matters because local AI inference is expensive.

The design minimizes unnecessary visual AI calls and final rendering.

------------------------------------------------------------------------

# 5. VERIFIED PRODUCTION RUN

The final real CLI verification used:

``` bat
python -m src.cli "C:\Users\SunGupta\Downloads\returnal video\1.mp4"
```

The source development fixture had:

-   duration: 31.30 seconds
-   resolution: 1920x1080
-   frame rate: 30 FPS
-   video codec: H.264
-   audio: AAC
-   approximate original development file size: 79.7 MB

The final accepted run produced:

-   final highlights: 2
-   exported files: 2
-   Short packages: 2
-   pipeline time: 168.87 seconds
-   run output folder: `output\runs\20260715_205234_1_9b640c0c`

Example package paths:

``` text
output\runs\20260715_205234_1_9b640c0c\shorts\short_001\final_short.mp4
output\runs\20260715_205234_1_9b640c0c\shorts\short_001\captions.srt
output\runs\20260715_205234_1_9b640c0c\shorts\short_004\final_short.mp4
output\runs\20260715_205234_1_9b640c0c\shorts\short_004\captions.srt
```

Example accepted Rank 1 metadata:

``` text
Category         : reaction
Confidence       : 0.9500
Hook             : OMG! Seriously?!
Title            : Rage Boss Fight Moment!
Hashtags         : #Gaming #HindiGaming #Reaction #Rage #FunnyFails #Shorts
```

The final acceptance required **both** final Shorts to have non-empty:

-   Hook
-   Title
-   Description
-   Hashtags
-   Thumbnail Prompt

Both also had:

-   final Short video
-   caption file

## Verified stage timing snapshot

``` text
Loading video                                 0.10s
Extracting audio                              0.10s
Detecting speech                              0.30s
Creating speech chunks                        0.03s
Transcribing commentary                       18.21s
Detecting scenes                              3.35s
Mapping commentary to scenes                  0.00s
Analyzing motion                              4.77s
Analyzing audio intensity                     0.00s
Extracting highlight features                 0.00s
Scoring highlight scenes                      0.00s
Selecting highlight candidates                0.00s
Resolving highlight overlaps                  0.00s
Generating highlight clips                    6.57s
Running commentary AI reasoning               11.17s
Combining commentary analysis                 0.00s
Extracting representative frames for rank 1   0.34s
Extracting representative frames for rank 4   0.31s
Warming up visual AI model                    2.61s
Running visual AI reasoning for rank 1        11.56s
Running visual AI reasoning for rank 4        11.82s
Fusing multimodal AI decisions for rank 1     15.15s
Fusing multimodal AI decisions for rank 4     13.51s
Selecting final approved highlights           0.00s
Linking approved decisions to clips           0.00s
Exporting final highlight package             0.03s
Building final YouTube Short packages         68.94s
```

This timing snapshot is a benchmark clue, not a guaranteed SLA.

------------------------------------------------------------------------

# 6. REPOSITORY ORGANIZATION

The public repository currently contains top-level items including:

``` text
PressStartAI/
├── config/
├── docs/
├── separated/
│   └── htdemucs/
│       └── 1/
├── src/
│   ├── core/
│   ├── exceptions/
│   ├── models/
│   ├── services/
│   └── cli.py
├── tools/
├── .gitignore
├── README.md
├── main.py
├── pyproject.toml
├── requirements-dev.txt
└── requirements.txt
```

## Important repository hygiene warning

`separated/htdemucs/1` appears to be historical generated Demucs output.

It may not belong in source control.

Do not delete it blindly. First:

1.  inspect whether current code references it
2.  inspect Git history
3.  confirm it is only generated/experimental data
4.  update `.gitignore`
5.  remove it in a dedicated repository hygiene change
6.  run verification

Other future hygiene targets:

-   generated output
-   temporary audio
-   speech chunks
-   model caches
-   source videos
-   large media
-   machine-specific absolute paths
-   secrets or tokens
-   logs
-   benchmark artifacts

## `src/`

Production code lives under `src`.

Current top-level source areas visible in the repository:

-   `src/core`
-   `src/exceptions`
-   `src/models`
-   `src/services`
-   `src/cli.py`

### `src/models`

Use model/dataclass objects for structured data contracts between
stages.

Historically implemented model concepts include:

-   `SpeechChunk`
-   `ASRSegment`
-   `Scene`
-   `SceneAnalysis`
-   `MotionFeatures`
-   `AudioFeatures`
-   `HighlightFeatures`
-   `HighlightScore`
-   `HighlightCandidate`
-   generated highlight metadata
-   commentary analysis
-   visual analysis
-   combined/multimodal analysis
-   final decision
-   final highlight
-   pipeline stage timing
-   pipeline result
-   Short package / metadata-related structures

A future AI must inspect the actual current filenames before editing.

### `src/services`

Services implement processing stages.

Important service domains include:

-   video loading
-   audio extraction
-   VAD
-   speech chunk extraction
-   ASR
-   scene detection
-   scene/transcript mapping
-   motion analysis
-   audio analysis
-   highlight feature extraction
-   scoring
-   candidate selection
-   overlap resolution
-   clip generation
-   local AI commentary reasoning
-   representative frame extraction
-   visual reasoning
-   multimodal fusion
-   final selection
-   final linking
-   final export
-   portrait/Short rendering
-   caption building
-   caption rendering
-   publishing metadata generation
-   production pipeline orchestration
-   timing/progress support

### `src/core`

Read this directory before changing pipeline infrastructure,
configuration, execution wrappers, timing, or other cross-cutting
behavior.

### `src/exceptions`

Use project-specific exception handling where already established.

Do not replace structured exceptions with broad
`except Exception: pass`.

### `src/cli.py`

This is the verified command-line entry path.

Production invocation:

``` bat
python -m src.cli "FULL_PATH_TO_VIDEO"
```

Any CLI change must preserve arbitrary quoted Windows paths, including
paths with spaces.

## `tools/`

The repository deliberately contains many verification and benchmark
scripts.

Visible/current verification scripts include examples such as:

``` text
benchmark_openvino.py
benchmark_visual_reasoner.py
verify_audio_analyzer.py
verify_audio_extractor.py
verify_caption_renderer.py
verify_caption_segment_builder.py
verify_final_highlight_combiner.py
verify_final_highlight_exporter.py
verify_final_highlight_selector.py
verify_full_highlight_pipeline.py
verify_funasr_hindi.py
verify_highlight_analysis_combiner.py
verify_highlight_candidates.py
```

Historical verification scripts also covered:

-   video loading
-   transcript behavior
-   VAD
-   speech chunks
-   Qwen ASR
-   transcription pipeline
-   scene detection
-   scene/transcript mapping
-   motion
-   audio
-   highlight scoring
-   overlap handling
-   generated clips
-   commentary reasoner
-   visual reasoner
-   multimodal fusion
-   final export
-   OpenVINO

### Do not casually delete verification scripts

Some scripts document failures and design decisions that are not obvious
from production code.

A cleanup phase should classify tools as:

-   active regression verification
-   benchmark
-   historical experiment
-   obsolete
-   fixture-specific

Only then should scripts be archived or removed.

------------------------------------------------------------------------

# 7. SOFTWARE REQUIREMENTS AND DEPENDENCY POLICY

## 7.1 Python version is intentionally constrained

`pyproject.toml` currently specifies:

``` toml
requires-python = ">=3.12,<3.13"
```

The project was verified with:

`Python 3.12.10`

Do not install with Python 3.13 unless the repository is deliberately
ported and all AI/media dependencies are reverified.

## 7.2 Current project metadata

The current `pyproject.toml` defines:

``` toml
[project]
name = "pressstartai"
version = "0.1.0"
description = "Local AI powered gaming video to YouTube Shorts generator"
requires-python = ">=3.12,<3.13"
authors = [
    {name = "Sunny Gupta"}
]

[tool.black]
line-length = 100

[tool.ruff]
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## 7.3 Important current dependency families

The committed `requirements.txt` is a full pinned environment snapshot
and currently includes many direct and transitive packages.

Important functional dependencies include:

### AI / ML

-   `torch==2.13.0`
-   `transformers==4.57.6`
-   `accelerate==1.12.0`
-   `huggingface_hub==0.36.2`
-   `safetensors==0.8.0`
-   `tokenizers==0.22.2`
-   `onnxruntime==1.27.0`
-   `openvino==2026.2.1`
-   `openvino-tokenizers==2026.2.1.0`
-   `qwen-asr==0.0.6`
-   `silero-vad==6.2.1`

### Video / image

-   `opencv-python==5.0.0.93`
-   `scenedetect==0.7`
-   `ffmpeg-python==0.2.0`
-   `av==18.0.0`
-   `pillow==12.3.0`

### Audio

-   `soundfile==0.14.0`
-   `librosa==0.11.0`
-   `audioread==3.1.0`
-   `pydub==0.25.1`
-   `sox==1.5.0`
-   `soxr==1.1.0`

### Configuration / data / runtime

-   `PyYAML==6.0.3`
-   `numpy==2.4.6`
-   `pydantic==2.13.4`
-   `requests==2.34.2`
-   `truststore==0.10.4`
-   `psutil==7.2.2`

### Development / verification

The environment snapshot also includes:

-   `pytest==9.1.1`
-   `pytest-cov==7.1.0`
-   `black==26.5.1`
-   `ruff==0.15.21`

### Historical/experimental packages still present

The environment also contains packages related to experiments that were
rejected as primary production paths, including:

-   `faster-whisper==1.2.1`
-   `demucs==4.1.0`
-   FunASR installed from a pinned Git commit
-   `torchcodec==0.14.0`
-   `torchaudio==2.11.0`

Do not conclude that every package in `requirements.txt` is an active
production dependency.

## 7.4 Dependency cleanup is future work

The current `requirements.txt` appears to be a broad environment freeze
rather than a carefully minimized direct dependency manifest.

A future dependency-cleanup phase should:

1.  create a clean clone
2.  identify imports from production code
3.  identify runtime external executables
4.  identify model-download dependencies
5.  separate production dependencies
6.  separate development dependencies
7.  separate historical experiment dependencies
8.  build a fresh environment
9.  run component verification
10. run the full CLI
11. compare output
12. only then replace the requirements files

Do not "clean" dependencies merely because a package looks unused.

------------------------------------------------------------------------

# 8. EXTERNAL EXECUTABLES AND LOCAL MODELS

## 8.1 Git

Git is used for source control.

The public repository is:

`https://github.com/sunnygupta1990/PressStartAI`

The verified local `main` branch tracks `origin/main`.

The final 100% checkpoint had:

`nothing to commit, working tree clean`

## 8.2 FFmpeg

FFmpeg is required for media work.

`ffmpeg-python` is only the Python wrapper. The FFmpeg executable must
also be installed and usable.

Verify:

``` bat
ffmpeg -version
where ffmpeg
```

If FFmpeg is unavailable, do not debug Python rendering code first.

## 8.3 Ollama

Verified development version:

`0.32.0`

Verify:

``` bat
ollama --version
ollama list
```

Required verified model:

`gemma3:4b`

If missing:

``` bat
ollama pull gemma3:4b
```

Then verify local reasoning separately before running the entire video
pipeline.

Historical verification prompt returned:

`PressStartAI verification successful.`

## 8.4 Hugging Face / Qwen model

Primary ASR model:

`Qwen/Qwen3-ASR-0.6B`

The initial setup may require internet access to download model files.

Model cache size and storage must be considered.

Corporate TLS interception can interfere with downloads.

------------------------------------------------------------------------

# 9. WINDOWS INSTALLATION GUIDE FOR A NEW MACHINE

## 9.1 Before installation

Collect the hardware and software answers from Section 0.

Do not proceed if Python is 3.13.

Do not assume the project works on macOS/Linux.

## 9.2 Install prerequisites

Required external prerequisites:

1.  Windows 11
2.  Git
3.  Python 3.12.x 64-bit
4.  FFmpeg
5.  Ollama
6.  sufficient SSD space
7.  internet access for initial package/model download

Recommended:

-   32 GB RAM
-   Intel Core Ultra 7 155H class hardware
-   Intel Arc iGPU
-   Intel AI Boost NPU

## 9.3 Clone the repository

``` bat
cd /d "C:\AI Projects"
git clone https://github.com/sunnygupta1990/PressStartAI.git
cd /d "C:\AI Projects\PressStartAI"
```

Verify:

``` bat
git status
git remote -v
```

## 9.4 Create the virtual environment

Use Python 3.12.

``` bat
python --version
python -m venv .venv
```

Activate from Command Prompt:

``` bat
.venv\Scripts\activate.bat
```

Expected prompt style:

``` text
(.venv) C:\AI Projects\PressStartAI>
```

### Important PowerShell history

PowerShell activation previously failed because script execution was
disabled.

Command Prompt activation worked.

Do not waste time debugging PowerShell execution policy unless
PowerShell support is an explicit goal.

## 9.5 Upgrade basic packaging tools cautiously

Before changing package versions, prefer installing the committed
environment.

If a clean build requires packaging bootstrap:

``` bat
python -m pip install --upgrade pip
```

Do not globally upgrade the full AI stack.

## 9.6 Install committed Python requirements

``` bat
python -m pip install -r requirements.txt
```

Then:

``` bat
python -m pip check
```

A verified development environment previously returned:

`No broken requirements found.`

### Important warning

The current requirements snapshot contains a Git-based FunASR dependency
and a large dependency graph.

If installation fails:

-   capture the complete error
-   identify the exact package
-   do not randomly remove version pins
-   do not upgrade PyTorch independently
-   check whether the failed package is active production code or a
    historical experiment
-   inspect current imports before deciding the repair

## 9.7 Verify FFmpeg

``` bat
ffmpeg -version
```

## 9.8 Verify Ollama

``` bat
ollama --version
ollama list
```

Confirm:

`gemma3:4b`

If missing:

``` bat
ollama pull gemma3:4b
```

## 9.9 Verify OpenVINO devices

``` bat
python -c "from openvino import Core; core = Core(); print(core.available_devices)"
```

The original development machine previously verified CPU, GPU, and NPU
availability.

Record the exact output on the new machine.

## 9.10 Verify core imports

Use the repository's verification scripts where possible.

At minimum, confirm critical imports before a full run.

Examples:

``` bat
python -c "import cv2; print(cv2.__version__)"
python -c "import soundfile; print('SoundFile OK')"
python -c "import openvino; print(openvino.__version__)"
python -c "import qwen_asr; print('Qwen ASR OK')"
python -c "from silero_vad import load_silero_vad; print('Silero VAD OK')"
```

## 9.11 Run focused repository verification

Inspect `tools` and run active verification scripts in dependency order.

Recommended logical order:

1.  OpenVINO/device verification
2.  video loader
3.  audio extractor
4.  VAD
5.  speech chunk extraction
6.  Qwen ASR
7.  transcription pipeline
8.  scene detector
9.  transcript mapping
10. motion analyzer
11. audio analyzer
12. feature extraction
13. scorer
14. candidate selection
15. overlap resolver
16. clip generation
17. commentary AI
18. representative frames
19. visual AI
20. multimodal fusion
21. final selection
22. final exporter
23. caption segment builder
24. caption renderer
25. Short metadata generator
26. production pipeline
27. CLI

Use actual current tool filenames.

## 9.12 Run the production CLI

``` bat
python -m src.cli "C:\FULL\PATH\TO\YOUR\VIDEO.mp4"
```

Always quote Windows paths.

## 9.13 Acceptance criteria for a successful installation

A new build is not accepted merely because imports pass.

Require:

-   source video loads
-   audio extracts
-   speech detection runs
-   ASR returns without crashing
-   scenes are detected
-   candidates are produced or the system correctly explains why none
    qualify
-   Ollama commentary reasoning runs
-   visual reasoning runs
-   final decision stage completes
-   final export completes
-   1080x1920 Short is rendered for approved highlights
-   captions SRT is created
-   captions are rendered/burned as designed
-   publishing metadata is non-empty
-   output is organized under a run folder
-   CLI prints timings
-   generated MP4 opens and has audio
-   captions are readable
-   Unicode metadata is valid
-   no unsupported-script contamination passes validation
-   `python -m pip check` is clean or every exception is understood
-   `git status` does not show accidental generated media unless
    expected

------------------------------------------------------------------------

# 10. HISTORICAL FAILURES --- DO NOT REPEAT BLINDLY

This section is critical for AI error recovery.

## 10.1 Whisper was rejected as the primary Hindi/Hinglish ASR

`faster-whisper` was installed and tested.

Observed behavior:

-   Whisper small detected Urdu and produced Urdu-script nonsense.
-   large-v3-turbo recognized the English phrase `I was going good`
-   Hindi was missed
-   forced Hindi produced repeated nonsense similar to `वाग वाग वाग...`

Decision:

**Whisper is not the primary ASR.**

It may only be reconsidered as a fallback if a future implementation has
a concrete new strategy and is benchmarked against Qwen on real Sunny
commentary.

## 10.2 FunASR was rejected

FunASR imported successfully.

On Hindi speech it produced Chinese text:

`我这个了，都会压力太大。`

Decision:

Do not use FunASR as the primary ASR for the verified workflow.

## 10.3 Demucs did not reliably isolate commentary

Demucs installed and ran.

Sunny manually listened to the stems.

Observed:

-   drums and bass separation sounded good
-   approximately half of Sunny's vocals went to `other`
-   approximately half went to `vocals`

Decision:

The Demucs vocals stem is not a reliable isolated commentary track.

Do not build core ASR logic around the assumption that `vocals.wav`
contains all commentary.

## 10.4 TorchCodec / Torchaudio path failed

Initial Silero VAD audio loading used `torchaudio.load`.

This failed because TorchCodec was required.

TorchCodec was installed but failed to load `libtorchcodec` DLLs.

The environment involved:

-   PyTorch 2.13.0 CPU-oriented use
-   FFmpeg shared-library compatibility issues
-   Windows DLL loading failures

Decision:

**Do not use `torchaudio.load` for the current VAD audio-loading path.**

Working solution:

`SoundFile`

The VAD implementation loads audio with `soundfile.read`, converts
stereo to mono when needed, and uses NumPy float32 data.

## 10.5 DeepFilterNet was unavailable

`pip install deepfilternet` failed.

Reason:

-   Rust/Cargo was not installed
-   `deepfilterlib` required compilation

Decision:

DeepFilterNet is not part of the working core pipeline.

## 10.6 Tiny speech chunks broke ASR language detection

Original tiny VAD chunks caused Qwen automatic language detection to
jump among:

-   Hindi
-   Malay
-   Portuguese
-   Chinese
-   English

Working fix:

Merge nearby speech regions.

Verified merged chunks from the original fixture were approximately:

``` text
3.28s  -> 6.10s
19.66s -> 27.06s
29.17s -> 30.80s
```

After merging, Qwen output became much more stable:

-   Hindi
-   Hindi
-   English

Architectural lesson:

**ASR chunking is part of model quality.**

Do not tune the ASR model in isolation while ignoring chunk duration and
silence gaps.

## 10.7 Transcript duplication across scenes

An early scene mapper attached one transcript segment to every
overlapping scene.

One long segment was duplicated across multiple scenes.

Working fix:

Assign each transcript segment to the scene with **maximum time
overlap**.

Do not restore naive multi-scene duplication.

## 10.8 `ModuleNotFoundError: No module named 'src'` in tool scripts

Some verification scripts failed because the project root was not on
`sys.path`.

A working pattern was:

``` python
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

If a tool script fails to import `src`, inspect how it is launched and
how current scripts handle project-root imports.

Do not alter production package architecture solely to fix one badly
launched script.

## 10.9 Qwen generation warnings

Warnings observed:

``` text
The following generation flags are not valid and may be ignored: ['temperature']
Setting pad_token_id to eos_token_id:151645 for open-end generation.
```

These warnings did not prevent transcription.

Do not treat them as the root cause of unrelated pipeline failures.

## 10.10 Ollama response formatting required defensive parsing

Local AI can return:

-   Markdown code fences
-   JSON wrapped in prose
-   ANSI/control sequences
-   imperfect formatting

The pipeline added:

-   Markdown-fence/JSON extraction
-   ANSI/control-sequence sanitization
-   structured parsing

Do not replace defensive parsing with a simple `json.loads(raw_stdout)`
unless the current model behavior is revalidated.

## 10.11 Visual AI was too slow before optimization

An early run took approximately:

`285.28s`

Visual reasoning consumed about 100 seconds per candidate.

The visual AI path was optimized and model warmup/timing behavior
improved substantially.

Do not add more frames, more prompts, repeated model initialization, or
duplicate visual calls without comparing stage timings.

## 10.12 Publishing metadata could be empty

A near-final run produced valid Rank 1 metadata but Rank 4 had empty:

-   Hook
-   Title
-   Description
-   Hashtags
-   Thumbnail Prompt

This was rejected.

The metadata generator was fixed to validate generated output and avoid
silently returning incomplete publishing metadata.

Acceptance rule:

A final Short package must not be considered complete when required
publishing fields are empty.

## 10.13 Unsupported script contamination

A generated hook contained Tamil script:

`OMG! செக் பண்ணு!`

The intended output context was Hindi/Hinglish/English.

Validation was added.

Do not remove language/script validation unless a future product
requirement explicitly expands supported languages.

------------------------------------------------------------------------

# 11. IMPORTANT DATA CONTRACTS AND HISTORICAL MODEL SHAPES

The current repository code is authoritative. These historical shapes
explain the intended contracts.

## 11.1 `SpeechChunk`

Purpose:

A speech WAV chunk mapped to the original video timeline.

Historical fields:

``` python
file_path: str
start_seconds: float
end_seconds: float
```

## 11.2 `ASRSegment`

Purpose:

Transcribed speech mapped to the source video timeline.

Historical fields:

``` python
start_seconds: float
end_seconds: float
language: str
text: str
```

## 11.3 `Scene`

Purpose:

Detected source-video scene.

Historical fields:

``` python
start_seconds: float
end_seconds: float
```

Computed:

``` python
duration_seconds
```

## 11.4 `SceneAnalysis`

Purpose:

Scene plus assigned transcript segments.

Important behavior:

`transcript_text` joins non-empty assigned segment text.

## 11.5 `MotionFeatures`

Historical fields:

``` python
scene_start_seconds
scene_end_seconds
average_motion_score
maximum_motion_score
```

## 11.6 `AudioFeatures`

Historical fields:

``` python
scene_start_seconds
scene_end_seconds
average_rms
maximum_rms
```

## 11.7 `HighlightFeatures`

Historical fields:

``` python
scene_start_seconds
scene_end_seconds
scene_duration_seconds
transcript_text
has_speech
speech_character_count
speech_word_count
average_motion_score
maximum_motion_score
average_audio_rms
maximum_audio_rms
```

## 11.8 `HighlightScore`

Historical relationship:

``` python
features: HighlightFeatures
speech_score: float
motion_score: float
audio_score: float
final_score: float
```

## 11.9 `HighlightCandidate`

Historical fields:

``` python
start_seconds
end_seconds
rank
score
```

Computed:

``` python
duration_seconds
```

## Data-contract rule for future AI

If a model/dataclass field changes:

1.  search every constructor
2.  search every attribute access
3.  inspect serialization
4.  inspect CLI formatting
5.  inspect verification scripts
6.  inspect JSON export
7.  inspect pipeline orchestration
8.  update all affected call sites
9.  run focused verification
10. run the full CLI if the model crosses stage boundaries

Do not make isolated dataclass edits.

------------------------------------------------------------------------

# 12. CORE ALGORITHM NOTES

## 12.1 VAD configuration history

A working Silero VAD configuration historically used:

``` text
threshold = 0.5
min_speech_duration_ms = 250
min_silence_duration_ms = 700
speech_pad_ms = 400
return_seconds = False
```

Audio was loaded as float32.

Stereo audio was averaged to mono.

Before changing VAD parameters, test:

-   quiet speech
-   shouting
-   game music
-   gunfire
-   menu audio
-   long silence
-   Hindi commentary
-   short punch lines

## 12.2 Speech merge history

Historical defaults:

``` text
merge_gap_seconds = 2.0
maximum_chunk_seconds = 20.0
```

The merge strategy considers:

-   gap to next speech region
-   proposed merged duration

Changing these values can directly affect ASR language detection and
transcript quality.

## 12.3 Scene detection history

Historical scene detector configuration:

``` text
threshold = 27.0
minimum_scene_length_frames = 15
minimum_scene_duration_seconds = 2.0
```

Short scenes were merged.

Do not optimize scene count in isolation. Candidate quality depends on
the relationship among:

-   scene boundaries
-   transcript assignment
-   motion aggregation
-   audio aggregation
-   candidate padding

## 12.4 Motion algorithm history

Historical approach:

-   sample every 5 frames
-   grayscale
-   Gaussian blur `(5, 5)`
-   absolute difference from previous sampled frame
-   mean pixel difference as motion score

This is intentionally lightweight.

A future optical-flow or neural motion model must justify its compute
cost on the target Intel hardware.

## 12.5 Audio RMS history

Average RMS:

``` text
sqrt(mean(square(audio)))
```

Peak RMS was historically measured in approximately 0.25-second windows.

Again, this is mixed game/commentary audio.

## 12.6 Highlight scoring history

First heuristic:

``` text
final =
    motion_score * 0.45
    + speech_score * 0.30
    + audio_score * 0.25
```

Normalization was relative to maximum values in the analyzed
video/candidate set.

Potential future weakness:

Relative max normalization can behave differently on a two-minute quiet
video versus a three-hour high-intensity video.

Any scoring redesign should be benchmarked across multiple games and
durations.

## 12.7 Candidate padding history

Historical selector defaults:

``` text
maximum_candidates = 5
minimum_score = 0.40
padding_before_seconds = 3.0
padding_after_seconds = 3.0
```

Padding improves event context but can cause overlap.

That is why overlap resolution exists.

------------------------------------------------------------------------

# 13. LOCAL AI DESIGN RULES

## 13.1 AI is not allowed to be the only first-pass detector

The current architecture uses cheap deterministic signals before
expensive AI reasoning.

Preserve this principle unless benchmarks prove a replacement is
superior.

## 13.2 Commentary AI should tolerate imperfect ASR

Prompts and reasoning should understand that Hindi/Hinglish ASR may be
phonetically imperfect.

Do not reject a visually strong moment solely because the transcript is
grammatically bad.

## 13.3 Visual AI must be bounded

Visual reasoning was the largest early bottleneck.

Rules:

-   warm the model once
-   avoid repeated initialization
-   shortlist before visual reasoning
-   extract representative evidence
-   measure stage timings
-   do not process every frame through an LLM/VLM

## 13.4 Structured AI output requires validation

Every AI-generated structured object should be treated as untrusted
input.

Validate:

-   parseability
-   required keys
-   types
-   empty strings
-   numeric ranges
-   supported categories
-   supported scripts/languages
-   path safety where applicable

## 13.5 AI failure should not silently produce "success"

Examples of unacceptable silent success:

-   empty title
-   empty hook
-   empty description
-   missing final Short path
-   zero-byte MP4
-   malformed JSON
-   captions missing when package claims captions exist
-   unsupported script contamination accepted as valid metadata

Prefer an explicit error or controlled fallback.

------------------------------------------------------------------------

# 14. ERROR-DIAGNOSIS PLAYBOOK FOR FUTURE AI

When the pipeline fails, do not rewrite the application immediately.

## Step 1 --- capture exact failure context

Record:

-   command
-   current directory
-   active virtual environment
-   Python version
-   Git commit
-   input video path
-   input video properties
-   full traceback
-   last successful stage
-   pipeline stage timings
-   output run folder
-   Ollama status
-   free disk space

## Step 2 --- identify the stage

Map the failure to:

-   environment
-   video loading
-   FFmpeg/audio extraction
-   VAD
-   chunking
-   ASR
-   scene detection
-   mapping
-   motion
-   audio
-   scoring
-   selection
-   overlap
-   clipping
-   commentary AI
-   frame extraction
-   visual AI
-   multimodal fusion
-   final selection
-   export
-   portrait rendering
-   caption building
-   SRT
-   caption burning
-   metadata generation
-   CLI/reporting

## Step 3 --- run the smallest relevant verification

Use `tools`.

Do not run a 3-hour video through the full pipeline to debug one import
error.

## Step 4 --- compare against known failures

Check Section 10.

## Step 5 --- inspect current implementation and call chain

Read:

-   model
-   service
-   caller
-   pipeline orchestrator
-   CLI
-   verification script

## Step 6 --- fix the root cause

Do not suppress exceptions simply to make verification green.

## Step 7 --- verify locally

Run focused verification.

## Step 8 --- run integration verification

Run the nearest downstream path.

## Step 9 --- run production CLI when needed

Required for changes to:

-   ASR
-   candidate timing
-   AI reasoning
-   final selection
-   media generation
-   captions
-   metadata
-   pipeline orchestration
-   output structure

## Step 10 --- inspect generated media manually

Automated verification cannot fully judge:

-   crop quality
-   caption readability
-   audio/video sync
-   event completeness
-   whether a Short is actually entertaining

------------------------------------------------------------------------

# 15. COMMON FAILURE TREES

## 15.1 `ModuleNotFoundError: src`

Check:

1.  current directory
2.  command used
3.  whether script is under `tools`
4.  project-root `sys.path` bootstrap
5.  package invocation style

Prefer:

``` bat
cd /d "C:\AI Projects\PressStartAI"
```

Then run the documented command.

## 15.2 FFmpeg not found

Check:

``` bat
where ffmpeg
ffmpeg -version
```

Do not blame `ffmpeg-python` if the executable is missing.

## 15.3 Ollama model failure

Check:

``` bat
ollama --version
ollama list
```

Confirm:

`gemma3:4b`

Then test Ollama independently.

## 15.4 ASR model download SSL error

Check:

-   internet
-   corporate proxy
-   certificate interception
-   trust store
-   `certifi`
-   `truststore`
-   Hugging Face access

The project historically used `truststore.inject_into_ssl()` in the Qwen
ASR service.

Do not disable TLS verification globally as a first fix.

## 15.5 VAD audio load / TorchCodec DLL error

Do not return to `torchaudio.load`.

Use/inspect the SoundFile path.

## 15.6 Random ASR languages

Check speech chunk durations.

Do not immediately replace Qwen.

Inspect:

-   VAD fragmentation
-   merge gap
-   maximum chunk duration
-   actual extracted WAV audio

Listen to the chunks.

## 15.7 Repeated transcript across scenes

Inspect `SceneTranscriptMapper`.

Expected design:

maximum overlap assignment.

## 15.8 Very slow pipeline

Read `PIPELINE STAGE TIMINGS`.

If visual AI is slow:

-   confirm model warmup
-   confirm model is not reloaded per candidate
-   inspect frame count
-   inspect prompt/input size
-   benchmark `benchmark_visual_reasoner.py`

If Short building is slow:

-   inspect FFmpeg operations
-   inspect number of render passes
-   inspect caption burn
-   inspect portrait render
-   inspect codec settings
-   inspect source resolution

## 15.9 Empty metadata

Do not accept the package.

Inspect:

-   raw Ollama output
-   parser
-   sanitizer
-   required field validation
-   fallback generation
-   supported script validation

## 15.10 No highlights selected

This may be a valid result.

Before calling it a bug, inspect:

-   scene count
-   features
-   normalized scores
-   minimum score
-   candidate count
-   overlap resolution
-   AI keep/reject decisions
-   confidence threshold

Do not force a highlight from every video unless the product requirement
explicitly says so.

## 15.11 Output file exists but video is broken

Check:

``` bat
ffprobe "PATH_TO_FILE"
```

Verify:

-   duration
-   video stream
-   audio stream
-   resolution
-   codec
-   file size

Open the file manually.

------------------------------------------------------------------------

# 16. CHANGE IMPACT MAP

Use this map before modifications.

## Changing ASR

Inspect:

-   speech chunks
-   Qwen ASR service
-   transcription pipeline
-   ASR segment model
-   scene transcript mapper
-   commentary reasoner
-   captions
-   metadata prompts

Full CLI verification required.

## Changing VAD/chunking

Impacts:

-   ASR language detection
-   transcript completeness
-   timestamps
-   captions
-   commentary reasoning

Full CLI verification required.

## Changing scene detection

Impacts:

-   transcript mapping
-   motion windows
-   audio windows
-   feature extraction
-   scores
-   candidates
-   highlight boundaries

Full pipeline verification required.

## Changing scoring

Impacts:

-   candidate rank
-   candidate count
-   visual AI workload
-   final highlight diversity
-   performance

Benchmark multiple videos.

## Changing overlap resolution

Impacts:

-   duplicate moments
-   event completeness
-   clip timing
-   rank-to-clip relationships

Verify decision-to-clip linking.

## Changing Ollama model

Impacts:

-   commentary reasoning
-   visual reasoning
-   multimodal fusion
-   metadata
-   JSON formatting
-   speed
-   RAM

Treat as a major architecture change.

## Changing visual frame extraction

Impacts:

-   visual context
-   AI decision quality
-   speed

Run `benchmark_visual_reasoner.py` and full CLI.

## Changing portrait crop/tracking

Impacts:

-   final media only, but user-visible quality is critical

Test different game HUDs and face-cam layouts.

## Changing captions

Inspect:

-   ASR timestamps
-   source-to-clip timeline conversion
-   caption segment builder
-   SRT writer
-   caption renderer
-   FFmpeg escaping/fonts

Test Hindi Unicode.

## Changing metadata prompts

Preserve:

-   non-empty required fields
-   supported script validation
-   JSON parsing
-   channel context
-   thumbnail prompt constraints

## Changing a dataclass/model

Search all constructors and consumers.

Never change a shared model in isolation.

## Changing output paths

Inspect:

-   pipeline result
-   exporter
-   Short builder
-   CLI
-   verification scripts
-   metadata serialization

------------------------------------------------------------------------

# 17. TESTING AND VERIFICATION STRATEGY

## 17.1 Current project reality

The repository has a large `tools` verification suite.

`pyproject.toml` points pytest to:

``` toml
testpaths = ["tests"]
```

A future AI should inspect whether a formal `tests/` suite currently
exists and how complete it is.

## 17.2 Recommended future test layers

### Unit tests

For:

-   normalization
-   overlap math
-   temporal overlap
-   timestamp conversion
-   caption segment timing
-   script validation
-   metadata required fields
-   output path construction

### Integration tests

For:

-   audio extraction
-   VAD + chunking
-   ASR + timeline
-   scene mapping
-   feature + score + selector
-   clip generation
-   Ollama parser
-   final export
-   caption rendering

### Golden fixture tests

Use small legal test fixtures.

Do not commit copyrighted full-length gameplay.

Record expected:

-   scene count ranges
-   candidate rank/order
-   final highlight count
-   metadata required-field completeness
-   output dimensions
-   audio presence

Avoid asserting exact AI prose unless deterministic behavior is
guaranteed.

### Performance regression tests

Record:

-   total runtime
-   ASR time
-   visual warmup
-   visual reasoning per candidate
-   multimodal fusion
-   final Short build

Use the verified Intel machine as the reference baseline.

------------------------------------------------------------------------

# 18. PERFORMANCE AND SCALABILITY NOTES

The final fixture was only 31.30 seconds.

The architecture is core-complete, but long-form scalability remains a
product-validation area.

Future tests should include:

-   5 minutes
-   15 minutes
-   30 minutes
-   60 minutes
-   2+ hours

Games should include:

-   slow story exploration
-   fast combat
-   dark scenes
-   bright scenes
-   face cam
-   no face cam
-   HUD-heavy gameplay
-   subtitles already present in the game
-   Hindi commentary
-   Hinglish commentary
-   mostly silent gameplay
-   continuous speech

Measure:

-   peak RAM
-   disk use
-   temp file growth
-   number of scenes
-   number of speech chunks
-   ASR runtime
-   candidate count
-   Ollama runtime
-   FFmpeg runtime
-   output size

Do not extrapolate 31-second timing linearly without measuring.

------------------------------------------------------------------------

# 19. SECURITY, PRIVACY, AND DATA HANDLING

## Local processing advantage

The design is local-first.

Gameplay, commentary, and generated clips do not require paid cloud AI
APIs.

## Still inspect for data exposure

A future AI must verify:

-   no API keys are committed
-   no personal tokens are committed
-   no private source video is committed
-   no machine-specific secrets are in config
-   no absolute user path is required by production logic
-   logs do not expose sensitive environment information unnecessarily

## Public repository warning

The repository is public.

Before every push:

``` bat
git status
git diff
```

Inspect new files.

Never commit:

-   `.env` secrets
-   tokens
-   credentials
-   private videos
-   private audio
-   model cache
-   huge generated outputs

------------------------------------------------------------------------

# 20. CONFIGURATION POLICY

The repository contains a `config` directory.

A future AI should move tunable behavior toward explicit configuration
only after inspecting current configuration usage.

Good configuration candidates:

-   VAD threshold
-   speech merge gap
-   maximum speech chunk duration
-   scene threshold
-   minimum scene duration
-   motion sample interval
-   highlight scoring weights
-   candidate minimum score
-   maximum candidates
-   before/after padding
-   overlap threshold
-   AI model names
-   final confidence threshold
-   portrait dimensions
-   caption style
-   metadata language policy

Do not create configuration for values that must remain invariant for
correctness.

Validate configuration at startup.

------------------------------------------------------------------------

# 21. FUTURE PRODUCT WORK --- NOT TO BE CONFUSED WITH CORE COMPLETION

The core pipeline is accepted as complete.

Future phases may include:

## Validation

-   long-video validation
-   cross-game validation
-   more Hindi/Hinglish samples
-   quiet-persona highlight validation
-   false positive analysis
-   false negative analysis

## Quality

-   event-boundary tuning
-   highlight duration tuning
-   better crop/reframe quality
-   caption styling
-   hook quality
-   metadata quality
-   thumbnail prompt quality

## Performance

-   OpenVINO optimization
-   Intel NPU use where practical
-   Intel GPU use where practical
-   fewer media render passes
-   smarter frame sampling
-   model caching
-   memory profiling

## Productization

-   Windows UI
-   installer
-   first-run hardware diagnostic
-   model setup wizard
-   progress bar
-   cancellation
-   resumable runs
-   crash recovery
-   output browser
-   settings
-   logs
-   automatic update strategy

## Engineering maturity

-   formal pytest suite
-   CI
-   dependency minimization
-   license review
-   repository hygiene
-   typed interfaces
-   structured logging
-   error codes
-   fixture strategy
-   benchmark suite
-   release process

------------------------------------------------------------------------

# 22. RECOMMENDED FIRST-RUN HARDWARE DIAGNOSTIC FEATURE

Because this project is hardware-sensitive, a future product version
should implement a first-run preflight command.

Suggested future command:

``` bat
python -m src.cli --diagnose
```

Suggested checks:

``` text
[PASS] Windows 11 detected
[PASS] 64-bit Python detected
[PASS] Python 3.12.x detected
[PASS] RAM: 32 GB
[PASS] FFmpeg found
[PASS] Git found
[PASS] Ollama found
[PASS] gemma3:4b installed
[PASS] OpenVINO CPU detected
[PASS] OpenVINO GPU detected
[PASS] OpenVINO NPU detected
[PASS] Qwen ASR import
[PASS] Silero VAD import
[PASS] OpenCV import
[PASS] SoundFile import
[PASS] Free disk space
[WARN] Hardware differs from verified Intel Core Ultra 7 155H baseline
```

The diagnostic should output a machine-readable JSON report so an AI
assistant can inspect it.

Example future file:

``` text
diagnostics/pressstartai_system_report.json
```

Do not claim compatibility solely from CPU brand.

------------------------------------------------------------------------

# 23. RECOMMENDED AI-FRIENDLY MAINTENANCE FILES

This README is the first AI handoff.

Future repository improvements should consider:

``` text
docs/
├── ARCHITECTURE.md
├── AI_MAINTAINER_GUIDE.md
├── TROUBLESHOOTING.md
├── HARDWARE_COMPATIBILITY.md
├── MODEL_DECISIONS.md
├── PERFORMANCE_BASELINE.md
├── OUTPUT_SCHEMA.md
├── DEVELOPMENT_HISTORY.md
└── RELEASE_CHECKLIST.md
```

Also consider:

``` text
CHANGELOG.md
CONTRIBUTING.md
LICENSE
SECURITY.md
```

The public repository should explicitly choose a license before outside
reuse is encouraged.

------------------------------------------------------------------------

# 24. GIT AND RELEASE DISCIPLINE

Before work:

``` bat
git status
git branch
git log --oneline -10
```

Before a commit:

``` bat
git status
git diff
```

After verification:

``` bat
git status
```

Use meaningful commits.

Do not mix:

-   repository cleanup
-   dependency upgrades
-   ASR replacement
-   scoring changes
-   UI work

into one commit.

For a production release, record:

-   commit hash
-   Python version
-   Ollama version
-   model names
-   requirements lock/snapshot
-   hardware
-   full CLI verification
-   benchmark timing
-   known limitations

------------------------------------------------------------------------

# 25. PROJECT-SPECIFIC AI DECISION HISTORY

## Primary ASR

Chosen:

`Qwen/Qwen3-ASR-0.6B`

Reason:

It was the first tested local ASR that produced usable Hindi-like output
and stabilized after speech chunk merging.

Rejected primary alternatives:

-   faster-whisper
-   FunASR

## Audio loading for VAD

Chosen:

`SoundFile`

Reason:

TorchCodec/Torchaudio path failed on the verified Windows environment.

## Voice separation

No reliable Demucs vocals-only dependency.

Reason:

Sunny's commentary was split between Demucs stems.

## Local reasoning

Chosen:

Ollama + `gemma3:4b`

Used for local commentary/visual/multimodal/publishing reasoning in the
completed pipeline.

## Visual AI performance strategy

Shortlist first, extract representative evidence, warm model, reason
only on candidates.

Reason:

Visual AI was initially the dominant bottleneck.

## Transcript mapping

Chosen:

maximum temporal overlap.

Reason:

prevents transcript duplication across adjacent scenes.

## Metadata validation

Required.

Reason:

real outputs contained empty fields and unwanted Tamil script.

------------------------------------------------------------------------

# 26. ORIGINAL DEVELOPMENT FIXTURE --- NEVER HARD-CODE IT

Historical test video:

``` text
C:\Users\SunGupta\Downloads\returnal video\1.mp4
```

Properties:

``` text
Duration: 31.3 seconds
Resolution: 1920x1080
FPS: 30
Video: H.264
Audio: AAC
Approximate size: 79.7 MB
```

Historical scene boundaries after merging:

``` text
0.00  -> 9.17
9.17  -> 13.77
13.77 -> 21.00
21.00 -> 26.17
26.17 -> 28.90
28.90 -> 31.30
```

Historical ASR examples:

``` text
[3.28 - 6.10] Hindi
[19.66 - 27.06] Hindi
[29.17 - 30.80] English: I was going good.
```

Historical top heuristic score:

``` text
Scene: 21.00s -> 26.17s
Speech Score: 1.0000
Motion Score: 0.6315
Audio Score: 1.0000
Final Score: 0.8342
```

These values are documentation and regression context.

They must never become production constants.

------------------------------------------------------------------------

# 27. WHAT "DONE" MEANS FOR A CORE PIPELINE CHANGE

A future AI should not say "fixed" after editing a file.

For a change affecting the core pipeline, "done" means:

1.  code change completed
2.  syntax/import verified
3.  focused verification passed
4.  affected integration verification passed
5.  full CLI passed when appropriate
6.  output package created
7.  final MP4 manually opens
8.  audio is present
9.  portrait dimensions are correct
10. captions exist and are usable
11. required metadata is non-empty
12. Unicode is preserved
13. unsupported script validation still works
14. stage timings are reviewed
15. Git diff is reviewed
16. no accidental generated files are committed

------------------------------------------------------------------------

# 28. QUICK START FOR AN AI ASSISTANT JOINING THE PROJECT

If you are an AI receiving this repository for the first time:

## First response behavior

Do not ask Sunny to explain PressStartAI again.

State that you understand:

-   local gaming-video-to-Shorts pipeline
-   verified Intel hardware baseline
-   Python 3.12 requirement
-   Qwen ASR
-   Silero VAD
-   SoundFile audio path
-   Ollama `gemma3:4b`
-   multimodal highlight selection
-   1080x1920 Short rendering
-   captions
-   publishing metadata
-   100% core pipeline status

## First technical actions

Ask Sunny to run only:

``` bat
cd /d "C:\AI Projects\PressStartAI"
git status
git log --oneline -5
```

Wait for output.

Then inspect the current repository state before proposing code.

## If the request is installation on another machine

Do **not** give installation commands immediately.

First collect the 20-item hardware/software preflight from Section 0.

## If the request is an error

Ask for or use:

-   exact command
-   full terminal output
-   last successful stage
-   `PIPELINE STAGE TIMINGS`
-   current Git status

Then map the error to Section 14.

------------------------------------------------------------------------

# 29. CURRENT KNOWN REPOSITORY STATUS AT THE TIME OF THIS DOCUMENT

At the time this AI README was prepared:

-   repository was public
-   branch was `main`
-   approximately 27 commits were visible
-   core pipeline was accepted as 100% functionally complete
-   final real CLI verification had passed
-   two complete Short packages had been produced from the fixture
-   publishing metadata was complete for both accepted Shorts
-   final Git checkpoint had been clean
-   local `main` tracked `origin/main`
-   a repository hygiene concern existed around `separated/htdemucs/1`
-   the top-level public README was still short and did not contain this
    full AI handoff
-   `requirements.txt` was a very large pinned environment snapshot
-   future product work had not yet replaced the accepted core-complete
    status

Always re-check the live repository because this section becomes
historical after new commits.

------------------------------------------------------------------------

# 30. FINAL NON-NEGOTIABLE RULES FOR FUTURE AI

1.  **Check hardware first on a new machine.**
2.  **Use Python 3.12.x unless deliberately porting.**
3.  **Do not assume NVIDIA/CUDA.**
4.  **Preserve the local-first, no-paid-cloud requirement.**
5.  **Do not restart completed milestones.**
6.  **Do not use the Returnal fixture as production logic.**
7.  **Do not replace Qwen ASR casually.**
8.  **Do not use `torchaudio.load` in the known VAD path without solving
    the historical TorchCodec issue.**
9.  **Do not trust Demucs vocals as complete Sunny commentary.**
10. **Do not attach a transcript to every overlapping scene.**
11. **Preserve maximum-overlap transcript mapping unless deliberately
    redesigned.**
12. **Do not ignore speech chunking when debugging ASR.**
13. **Do not trust raw Ollama output without sanitization and
    validation.**
14. **Do not accept empty publishing metadata.**
15. **Preserve supported-script validation.**
16. **Do not repeatedly cold-start visual AI per candidate.**
17. **Use pipeline stage timings before optimizing.**
18. **Inspect all consumers before changing shared models.**
19. **Run focused verification before the full pipeline.**
20. **Run the real CLI for changes that can affect final output.**
21. **Inspect generated video manually.**
22. **Keep production code generic across gaming videos.**
23. **Do not randomly upgrade the AI dependency stack.**
24. **Do not delete historical verification scripts without
    classification.**
25. **Check `git status` and `git diff` before pushing to the public
    repository.**
26. **Never commit private media, tokens, model caches, or generated
    output accidentally.**
27. **Treat different hardware as a compatibility validation task.**
28. **Core pipeline status is 100% complete; UI/productization is a
    future phase.**
29. **When guiding Sunny, use exact Command Prompt steps and stop after
    verification commands.**
30. **When a substantial file change is needed, provide the full
    replacement file.**

------------------------------------------------------------------------

# 31. FINAL PROJECT SUMMARY

PressStartAI is a fully local, Windows-first gaming video intelligence
and YouTube Shorts generation pipeline designed around Sunny Gupta's
Intel Core Ultra 7 155H laptop.

Its completed core architecture combines:

-   FFmpeg media processing
-   SoundFile audio handling
-   Silero voice activity detection
-   speech-region merging
-   Qwen3-ASR-0.6B local transcription
-   PySceneDetect scene analysis
-   maximum-overlap transcript mapping
-   OpenCV motion analysis
-   RMS audio intensity analysis
-   heuristic highlight scoring
-   candidate selection
-   overlap resolution
-   highlight clip generation
-   Ollama local commentary reasoning
-   representative visual frame extraction
-   `gemma3:4b` visual reasoning
-   multimodal AI fusion
-   confidence-based final highlight approval
-   final highlight export
-   1080x1920 portrait Short rendering
-   intelligent reframing/tracking
-   caption segment generation
-   SRT generation
-   caption burn-in
-   hook generation
-   title generation
-   description generation
-   hashtag generation
-   thumbnail prompt generation
-   per-run/per-Short output packaging
-   CLI reporting
-   per-stage performance timing

The most important maintenance lesson is that the current working system
is the result of many hardware- and model-specific decisions.

A future AI should improve it carefully, empirically, and one verified
stage at a time.

**End of AI technical handoff.**
