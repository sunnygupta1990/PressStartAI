# PressStartAI --- Complete Human Maintenance, Development, Installation, and Operations Manual

> **This is not a short README.**
>
> This document is the complete human-readable manual for PressStartAI.
>
> It is written for a developer, maintainer, technical support engineer,
> or future contributor who may know nothing about the history of this
> project.
>
> The goal is simple:
>
> **A person should be able to read this document, understand what
> PressStartAI does, understand why it was built this way, install it
> safely, run it, diagnose common failures, maintain it, and add new
> functionality without first having to reconstruct months of
> development history.**
>
> The explanations intentionally use plain English and layman terms.
> Technical terms are explained when they first appear.
>
> **Repository:** `https://github.com/sunnygupta1990/PressStartAI`
>
> **Project owner / author:** Sunny Gupta
>
> **Current project version:** `0.1.0`
>
> **Current accepted status:** Core end-to-end pipeline is functionally
> complete and has passed a real production-style command-line
> verification on the original development laptop.

------------------------------------------------------------------------

# Table of Contents

1.  The Most Important Warning: Hardware Compatibility
2.  What PressStartAI Is
3.  What Problem It Solves
4.  What the Application Can Do Today
5.  What the Application Does Not Yet Claim
6.  The Original Development Computer
7.  Basic Technical Concepts Explained
8.  The Entire Pipeline in One Picture
9.  The Entire Pipeline Explained Step by Step
10. Project Folder Structure
11. Important Data Objects and Why They Exist
12. Local AI Models Used by the Project
13. Software and External Program Requirements
14. Installing PressStartAI on a New Computer
15. Verifying a New Installation
16. Running PressStartAI
17. Understanding the Output
18. Understanding Pipeline Timings
19. Detailed Explanation of Every Major Processing Stage
20. Known Historical Failures and Lessons
21. Troubleshooting Guide
22. How to Diagnose a New Error
23. How to Safely Change Existing Functionality
24. How to Add New Functionality
25. Change Impact Guide
26. Testing and Verification
27. Performance and Long-Video Considerations
28. Hardware Porting and Compatibility
29. Dependency Management
30. Git and Repository Maintenance
31. Generated Files and Repository Hygiene
32. Security and Privacy
33. Configuration and Tunable Values
34. AI Output Validation
35. Captions and Language Handling
36. Portrait Video and Reframing
37. Publishing Metadata
38. Recommended Future Product Work
39. Recommended Engineering Improvements
40. Release Checklist
41. Maintainer Quick Reference
42. Glossary
43. Final Maintenance Principles

------------------------------------------------------------------------

# 1. THE MOST IMPORTANT WARNING: HARDWARE COMPATIBILITY

## Please read this section before installing anything

PressStartAI was not originally built as a universal application that
had already been tested on every type of computer.

It was developed, debugged, optimized, and finally verified on one
specific Windows laptop.

That matters because this project uses:

-   local artificial intelligence models
-   video processing
-   audio processing
-   PyTorch
-   OpenVINO
-   Intel hardware acceleration
-   Ollama
-   Hugging Face models
-   FFmpeg
-   OpenCV

These technologies can behave differently depending on the processor,
graphics hardware, AI accelerator, Windows version, Python version,
memory, and installed media libraries.

## Original verified development hardware

  Part                            Verified system
  ------------------------------- -------------------------------
  Operating system                Windows 11 Pro
  Processor                       Intel Core Ultra 7 155H
  Memory                          32 GB RAM
  Graphics                        Intel Arc integrated graphics
  AI accelerator                  Intel AI Boost NPU
  Storage                         500 GB SSD
  NVIDIA graphics card            None
  CUDA                            Not used
  Python                          Python 3.12.10
  Main AI approach                Fully local
  Preferred Intel acceleration    OpenVINO
  Local AI runtime                Ollama
  Main local Ollama model         `gemma3:4b`
  Main speech recognition model   `Qwen/Qwen3-ASR-0.6B`

## Why this is important

Imagine that a car engine has been tuned and tested using one type of
fuel.

The car may work with another fuel, but you should not simply assume
that it will behave exactly the same.

PressStartAI is similar.

For example:

-   an NVIDIA computer may have CUDA, but the current application was
    not designed around CUDA
-   an AMD computer may run the Python code but behave differently with
    acceleration
-   a computer without an Intel NPU may still run parts of the
    application, but performance may differ
-   Python 3.13 may break packages that work on Python 3.12
-   16 GB RAM may be enough for some videos but could fail with larger
    models or longer videos
-   macOS and Linux have not been accepted as verified platforms
-   a different FFmpeg installation may affect video encoding
-   a corporate computer may block AI model downloads because of SSL
    certificate inspection

## Before building on another computer, collect this information

A new maintainer should record:

1.  Windows version.
2.  Exact CPU model.
3.  Total RAM.
4.  Exact GPU model.
5.  Whether an Intel NPU is available.
6.  Whether an NVIDIA GPU is available.
7.  Whether CUDA is installed.
8.  Available SSD space.
9.  Python version.
10. Whether Python is 64-bit.
11. Git version.
12. FFmpeg version.
13. Ollama version.
14. Installed Ollama models.
15. OpenVINO detected devices.
16. Internet restrictions.
17. Corporate proxy or SSL inspection.
18. Administrator permission restrictions.
19. Intended video resolution and frame rate.
20. Typical video duration.

## Useful diagnostic commands

Open **Command Prompt** and run:

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

After installing the Python environment:

``` bat
python -c "from openvino import Core; core = Core(); print(core.available_devices)"
```

## Practical compatibility levels

### Closest to the original system

The lowest-risk system is:

-   Windows 11
-   Intel Core Ultra processor
-   Intel Arc integrated graphics
-   Intel AI Boost NPU
-   32 GB RAM
-   Python 3.12.x

### Different but probably adaptable

Examples:

-   a newer Intel Core Ultra laptop
-   Intel processor without the same NPU
-   16 GB RAM
-   NVIDIA laptop
-   AMD computer

These systems may work, but they must be tested.

### Treat as a porting project

Do not expect a normal installation process for:

-   macOS
-   Linux
-   Windows ARM
-   Python 3.13 or newer without testing
-   cloud notebooks
-   low-memory computers
-   containers without FFmpeg and Ollama access

------------------------------------------------------------------------

# 2. WHAT PRESSSTARTAI IS

PressStartAI is a local AI application for gaming videos.

Its job is to take a long gaming video and automatically find moments
that may be useful as YouTube Shorts.

It then prepares final Short packages.

In simple words:

> **You give PressStartAI a gameplay video. It watches, listens,
> analyzes, selects interesting moments, creates vertical Shorts, adds
> captions, and suggests publishing text.**

The project was originally created for the YouTube gaming channel:

`Press Start with Sunny`

The channel style includes:

-   Hindi commentary
-   Hinglish commentary
-   English commentary
-   story games
-   funny reactions
-   natural frustration
-   failures
-   boss fights
-   combat
-   trophy hunting
-   live-stream moments

## A very important design decision

Sunny is not a creator who constantly screams or talks every second.

Therefore, the application must not use a simple rule such as:

> Loud voice = good Short.

Instead, it combines several clues:

-   Was someone speaking?
-   What was said?
-   Was the gameplay moving quickly?
-   Was the game audio intense?
-   What was visually happening?
-   Did the local AI think the moment had entertainment value?
-   Did commentary and visual context agree?

This is why PressStartAI is a **multimodal** system.

Multimodal simply means it uses more than one type of information.

In this project, the major information types are:

-   speech
-   text
-   audio intensity
-   video motion
-   images/frames
-   local AI reasoning

------------------------------------------------------------------------

# 3. WHAT PROBLEM IT SOLVES

A long gaming recording can contain:

-   walking
-   menus
-   loading screens
-   repeated attempts
-   quiet exploration
-   combat
-   jokes
-   accidental deaths
-   boss moments
-   reactions

A human editor normally watches the entire video and manually asks:

-   Is this moment interesting?
-   Where should the clip start?
-   Where should it end?
-   Does the reaction make sense without earlier context?
-   Is this duplicate footage?
-   Should I make a Short from it?
-   How should I crop it vertically?
-   What captions should I add?
-   What should the title be?
-   What hook should I use?
-   Which hashtags should I use?

PressStartAI tries to automate this work.

## Why not simply ask one AI model to watch the entire video?

Because local AI is expensive in terms of:

-   processing time
-   RAM
-   model loading
-   video frame processing

The project therefore uses a filtering pipeline.

Cheap calculations happen first.

Expensive AI reasoning happens only on shortlisted moments.

This is similar to airport security:

1.  everyone passes through basic screening
2.  only suspicious or important cases receive deeper inspection

PressStartAI does the same with video moments.

------------------------------------------------------------------------

# 4. WHAT THE APPLICATION CAN DO TODAY

The completed core pipeline includes the following features.

## Video input

The command-line application accepts a video path.

Example:

``` bat
python -m src.cli "C:\Videos\gameplay.mp4"
```

## Audio extraction

It extracts audio from the gameplay video.

## Human speech detection

It uses Silero VAD to find likely human speech.

VAD means **Voice Activity Detection**.

It answers:

> "At what times does this audio probably contain human speech?"

## Speech chunk creation

Nearby speech regions are merged into larger audio chunks.

This improves speech recognition.

## Local speech recognition

The project uses:

`Qwen/Qwen3-ASR-0.6B`

It is used for Hindi, Hinglish, and English commentary.

## Scene detection

The video is divided into visual scenes.

## Speech-to-scene mapping

Recognized speech is attached to the scene where it overlaps the most.

## Motion analysis

The application measures how much the image changes.

More visual change generally means more movement or action.

## Audio intensity analysis

The application measures audio energy.

This includes game audio and commentary.

## Highlight feature creation

Speech, motion, and audio information are combined.

## Highlight scoring

Scenes receive a score.

## Candidate selection

The best-scoring scenes become possible highlight candidates.

## Context padding

Extra seconds can be added before and after a selected scene.

This helps preserve context.

## Overlap handling

Overlapping candidate clips are resolved.

This helps reduce duplicate Shorts.

## Highlight clip generation

Candidate video clips are created.

## Commentary AI reasoning

A local AI model examines the commentary context.

## Representative frame extraction

Important visual frames are extracted from candidate clips.

## Visual AI reasoning

A local vision-capable AI examines the visual evidence.

## Multimodal AI fusion

Commentary and visual reasoning are combined.

## Final highlight approval

The system decides which candidates should actually become final
highlights.

## Final media linking

AI decisions are connected back to the correct video clips.

## Final highlight export

Approved highlight information is exported.

## 9:16 vertical Short creation

The final Short is rendered at:

`1080 x 1920`

## Intelligent reframing

The application includes visual tracking/reframing logic for portrait
output.

## Caption creation

Speech information is converted into timed caption segments.

## SRT subtitles

A `.srt` subtitle file is generated.

## Caption rendering

Captions are burned into the final Short.

## Hook generation

The AI suggests a hook.

## Title generation

The AI suggests a YouTube Short title.

## Description generation

The AI suggests a description.

## Hashtag generation

The AI suggests hashtags.

## Thumbnail prompt generation

The AI creates a prompt that can be used for thumbnail creation.

## Organized output

Each run receives its own output folder.

Each final Short receives its own package folder.

## Pipeline timing

The application measures how long each major stage takes.

This is extremely useful for maintenance and optimization.

------------------------------------------------------------------------

# 5. WHAT THE APPLICATION DOES NOT YET CLAIM

The core pipeline is complete.

That does not mean PressStartAI is a finished commercial desktop
product.

The following should be considered future work or further validation
areas:

-   graphical Windows user interface
-   one-click installer
-   automatic hardware compatibility wizard
-   broad testing on many computers
-   broad testing on many games
-   formal long-video performance certification
-   automatic crash recovery
-   resumable processing
-   background processing
-   cancellation support
-   automatic application updates
-   commercial release packaging
-   extensive formal pytest coverage
-   continuous integration
-   full dependency minimization

Do not confuse:

> "The core pipeline works end to end"

with:

> "The product is finished for every user and every computer."

------------------------------------------------------------------------

# 6. THE ORIGINAL DEVELOPMENT COMPUTER

The original machine is the reference system.

``` text
Operating system : Windows 11 Pro
CPU              : Intel Core Ultra 7 155H
RAM              : 32 GB
GPU              : Intel Arc integrated graphics
NPU              : Intel AI Boost NPU
Storage          : 500 GB SSD
NVIDIA GPU       : None
CUDA             : None
Python           : 3.12.10
```

The development goal was:

-   no paid cloud AI
-   no NVIDIA requirement
-   no CUDA requirement
-   local AI
-   CPU/iGPU/NPU friendly
-   OpenVINO preferred where useful

If a maintainer introduces a mandatory CUDA feature, that changes a
fundamental project requirement.

------------------------------------------------------------------------

# 7. BASIC TECHNICAL CONCEPTS EXPLAINED

This section is for maintainers who are new to AI/video systems.

## Pipeline

A pipeline is a sequence of processing steps.

Example:

``` text
Video → Audio → Speech → Scenes → Scores → AI → Short
```

The output of one step becomes the input of another step.

## Model

In this repository, the word "model" can mean two different things.

### AI model

Examples:

-   Qwen ASR
-   Gemma 3

These are trained artificial intelligence systems.

### Python data model

Examples:

-   `Scene`
-   `ASRSegment`
-   `HighlightCandidate`

These are structured Python objects that hold data.

Always understand which meaning is intended.

## Service

A service is a Python component that performs a task.

Examples:

-   `MotionAnalyzer`
-   `AudioAnalyzer`
-   `SceneDetector`

## ASR

ASR means:

**Automatic Speech Recognition**

It converts audio speech into text.

## VAD

VAD means:

**Voice Activity Detection**

It finds where speech probably exists.

VAD does not understand the words.

## RMS

RMS is a mathematical way to measure audio energy.

In simple terms:

> higher RMS usually means stronger/louder audio energy.

## Scene detection

Scene detection tries to find visual boundaries in a video.

## Candidate

A candidate is a possible highlight.

It has not necessarily been approved as a final Short.

## Multimodal

Multimodal means using multiple information types.

PressStartAI combines:

-   transcript
-   audio
-   motion
-   visual frames

## Ollama

Ollama is a local AI model runner.

It allows PressStartAI to use an AI model on the computer instead of
sending data to a paid cloud API.

## OpenVINO

OpenVINO is Intel's toolkit for running AI workloads efficiently on
supported Intel hardware.

## FFmpeg

FFmpeg is a media-processing program.

It is used for audio/video tasks.

The Python package `ffmpeg-python` does not replace the FFmpeg
executable.

## SRT

SRT is a subtitle file format.

It contains:

-   caption number
-   start time
-   end time
-   caption text

## CLI

CLI means Command-Line Interface.

PressStartAI currently has a command-line entry point.

------------------------------------------------------------------------

# 8. THE ENTIRE PIPELINE IN ONE PICTURE

``` text
GAMEPLAY VIDEO
      │
      ▼
LOAD AND INSPECT VIDEO
      │
      ▼
EXTRACT AUDIO
      │
      ▼
FIND HUMAN SPEECH
      │
      ▼
MERGE SPEECH INTO USEFUL CHUNKS
      │
      ▼
CONVERT SPEECH TO TEXT
      │
      ├───────────────────────────────┐
      │                               │
      ▼                               ▼
DETECT VIDEO SCENES             MEASURE AUDIO ENERGY
      │
      ▼
ATTACH SPEECH TO BEST SCENE
      │
      ▼
MEASURE VIDEO MOTION
      │
      └───────────────┬───────────────┘
                      ▼
         COMBINE SPEECH + MOTION + AUDIO
                      │
                      ▼
               SCORE THE SCENES
                      │
                      ▼
            SELECT BEST CANDIDATES
                      │
                      ▼
             FIX OVERLAPPING CLIPS
                      │
                      ▼
            CREATE CANDIDATE VIDEOS
                      │
                      ▼
          AI READS COMMENTARY CONTEXT
                      │
                      ▼
           EXTRACT REPRESENTATIVE FRAMES
                      │
                      ▼
             AI EXAMINES VISUAL CONTEXT
                      │
                      ▼
        COMBINE COMMENTARY + VISUAL AI
                      │
                      ▼
          APPROVE OR REJECT HIGHLIGHTS
                      │
                      ▼
            LINK DECISION TO VIDEO CLIP
                      │
                      ▼
             EXPORT FINAL HIGHLIGHTS
                      │
                      ▼
              BUILD YOUTUBE SHORT
                      │
        ┌─────────────┼───────────────┐
        ▼             ▼               ▼
   9:16 VIDEO      CAPTIONS       PUBLISHING TEXT
        │             │               │
        │             │               ├── Hook
        │             │               ├── Title
        │             │               ├── Description
        │             │               ├── Hashtags
        │             │               └── Thumbnail prompt
        │             │
        └─────────────┴───────────────┘
                      │
                      ▼
               FINAL SHORT PACKAGE
```

------------------------------------------------------------------------

# 9. THE ENTIRE PIPELINE EXPLAINED STEP BY STEP

## Step 1: Load the source video

The application receives the path to a gaming video.

It first needs to confirm that the source can be processed.

The video duration is important because later clip boundaries must never
go below zero or beyond the end of the source.

## Step 2: Extract audio

The application creates audio that is easier for speech-processing tools
to analyze.

During development, mono 16 kHz audio was verified.

## Step 3: Find speech

Silero VAD analyzes the audio.

It produces time regions where human speech is likely.

Example concept:

``` text
3.2s to 5.7s  → speech
5.7s to 18.9s → no speech
19.6s to 26.8s → speech
```

## Step 4: Merge nearby speech

Very small speech fragments are bad for the selected speech recognition
model.

During development, tiny fragments caused the ASR model to incorrectly
switch among languages such as:

-   Hindi
-   Malay
-   Portuguese
-   Chinese
-   English

The fix was to merge nearby speech regions.

This is an important example of why the pipeline architecture matters.

The ASR model itself was not necessarily the only problem.

The input chunks were also a problem.

## Step 5: Convert speech into text

Qwen ASR processes each speech chunk.

The transcript is stored with original video timestamps.

This means the application knows both:

> "What was said?"

and:

> "When was it said?"

## Step 6: Detect visual scenes

PySceneDetect looks for visual changes.

Short scenes are merged when needed.

## Step 7: Attach speech to scenes

A transcript may cross a scene boundary.

The application assigns each transcript segment to the scene with the
greatest time overlap.

This prevents one transcript from being copied into several scenes.

## Step 8: Measure motion

OpenCV reads sampled video frames.

Frames are:

1.  converted to grayscale
2.  blurred slightly
3.  compared with the previous sampled frame

The average pixel difference becomes a simple motion signal.

## Step 9: Measure audio intensity

The application calculates RMS values.

The current audio signal contains:

-   game audio
-   Sunny's commentary

It is not a clean voice-only measurement.

Therefore, audio intensity means:

> "This part of the video has stronger audio energy."

It does not necessarily mean:

> "Sunny is shouting."

## Step 10: Build highlight features

The application creates one structured set of clues for each scene.

Examples:

-   scene duration
-   transcript
-   speech word count
-   average motion
-   maximum motion
-   average audio energy
-   peak audio energy

## Step 11: Score scenes

The original heuristic scoring approach combined:

-   motion
-   speech
-   audio

Historical first-version weights were:

``` text
Motion : 45%
Speech : 30%
Audio  : 25%
```

These weights were described as provisional.

Always inspect the current `HighlightScorer` before assuming the values
are still identical.

## Step 12: Select candidates

High-scoring scenes become highlight candidates.

Historical selector defaults included:

``` text
Maximum candidates : 5
Minimum score      : 0.40
Padding before     : 3 seconds
Padding after      : 3 seconds
```

## Step 13: Resolve overlap

Padding can make two candidate clips overlap.

The overlap resolver prevents the application from blindly creating
duplicate highlights.

## Step 14: Generate candidate clips

The application creates actual video clips for shortlisted candidates.

## Step 15: Understand commentary

A local AI examines the commentary context.

This is useful because raw word count cannot understand meaning.

For example:

``` text
“No no no no no!”
```

may have a low vocabulary count but still be a strong gaming reaction.

## Step 16: Extract representative frames

The application extracts visual evidence from a candidate.

It does not ask the visual AI to inspect every single frame of the
entire source video.

## Step 17: Understand visual context

The local Gemma model examines representative visual information.

This stage was historically expensive and was optimized.

## Step 18: Fuse commentary and visual reasoning

The application combines what the AI understood from:

-   commentary
-   visual context

This creates a stronger final decision.

## Step 19: Approve highlights

The final AI decision decides whether the candidate should continue.

## Step 20: Link decisions to clips

The approved decision must be connected to the correct media clip.

This sounds simple, but rank and timeline consistency are important.

## Step 21: Export approved highlights

Approved highlights and metadata are exported.

Unicode handling is important because Hindi text may be present.

## Step 22: Build a vertical Short

The application renders a 1080x1920 video.

## Step 23: Reframe

The source gameplay is normally 16:9 landscape.

YouTube Shorts are 9:16 portrait.

The application must choose which area of the source should remain
visible.

## Step 24: Build captions

Transcript information is converted into caption timing for the Short.

## Step 25: Write SRT

The subtitle file is generated.

## Step 26: Burn captions into the Short

Captions are rendered into the video.

## Step 27: Generate publishing metadata

The local AI generates:

-   hook
-   title
-   description
-   hashtags
-   thumbnail prompt

## Step 28: Validate metadata

The application checks the generated metadata.

This is required because real AI outputs previously contained:

-   empty fields
-   unwanted Tamil script

## Step 29: Package the Short

The final Short and subtitle file are stored in an organized output
folder.

## Step 30: Print results and timings

The CLI tells the user:

-   what was processed
-   how many highlights were approved
-   where files were written
-   how long each stage took
-   suggested publishing metadata

------------------------------------------------------------------------

# 10. PROJECT FOLDER STRUCTURE

The repository has a structure similar to:

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

Always inspect the current repository because files may be added later.

## `config/`

Configuration-related files belong here.

Before adding a new configuration file, inspect existing configuration
loading.

## `docs/`

Long technical documents and architecture notes belong here.

## `src/`

This is the main production code.

## `src/core/`

Cross-cutting application infrastructure belongs here.

Examples may include:

-   execution helpers
-   timing
-   configuration
-   shared runtime behavior

Read the current directory before making assumptions.

## `src/exceptions/`

Project-specific errors belong here.

A custom error is useful when the application should clearly explain a
specific failure.

Avoid code like:

``` python
try:
    ...
except Exception:
    pass
```

This hides the real problem.

## `src/models/`

This contains structured data objects.

A model should mainly describe data.

For example:

``` text
Scene
```

describes a scene.

A service should normally perform the processing.

## `src/services/`

This contains the main processing logic.

Examples of service responsibilities:

-   audio extraction
-   speech detection
-   ASR
-   scene detection
-   motion analysis
-   highlight scoring
-   AI reasoning
-   video rendering

## `src/cli.py`

This is the verified command-line entry point.

Normal usage:

``` bat
python -m src.cli "FULL_VIDEO_PATH"
```

## `tools/`

This directory contains verification and benchmark scripts.

These scripts are extremely important.

They document:

-   component behavior
-   integration behavior
-   historical experiments
-   performance

Do not delete them simply because they are not imported by production
code.

## `separated/htdemucs/1`

This appears to be historical Demucs-generated content.

It is a repository hygiene concern.

Before deleting it:

1.  search the production code for references
2.  inspect Git history
3.  confirm it is not required
4.  update `.gitignore`
5.  remove it in a separate cleanup change
6.  rerun verification

------------------------------------------------------------------------

# 11. IMPORTANT DATA OBJECTS AND WHY THEY EXIST

The exact current source code is always the final authority.

The following objects explain the architecture.

## `SpeechChunk`

Represents one exported speech audio file.

Conceptually contains:

``` text
audio file path
original video start time
original video end time
```

Why timestamps matter:

If the ASR says:

> "I was going good."

the application must know where that sentence happened in the original
gameplay.

## `ASRSegment`

Represents recognized speech.

Conceptually:

``` text
start time
end time
language
text
```

## `Scene`

Represents a visual scene.

Conceptually:

``` text
scene start
scene end
```

## `SceneAnalysis`

Represents:

``` text
one scene
+
speech assigned to that scene
```

## `MotionFeatures`

Stores motion measurements for a scene.

## `AudioFeatures`

Stores audio energy measurements for a scene.

## `HighlightFeatures`

Combines all important low-cost signals for a scene.

## `HighlightScore`

Stores:

-   speech score
-   motion score
-   audio score
-   final score

## `HighlightCandidate`

Represents a possible highlight window.

It can include extra time before and after the original scene.

## Later AI and final-output models

The current repository also uses structured information for areas such
as:

-   commentary analysis
-   visual analysis
-   combined AI analysis
-   final decision
-   final highlight
-   pipeline timing
-   pipeline result
-   final Short package
-   publishing metadata

## Rule when changing a model

Never add, remove, or rename a model field without searching the entire
repository.

For example, if you change:

``` python
final_score
```

to:

``` python
score
```

you must find:

-   every constructor
-   every `.final_score` access
-   sorting logic
-   filtering logic
-   JSON export
-   CLI printing
-   verification scripts

A model change can break many downstream stages.

------------------------------------------------------------------------

# 12. LOCAL AI MODELS USED BY THE PROJECT

## Qwen ASR

Model:

`Qwen/Qwen3-ASR-0.6B`

Purpose:

Speech-to-text.

Historical CPU configuration included:

``` text
dtype = torch.float32
device_map = cpu
max_inference_batch_size = 1
max_new_tokens = 256
```

Always inspect the current ASR service before changing model
configuration.

## Gemma 3 through Ollama

Model:

`gemma3:4b`

Purpose includes local AI reasoning such as:

-   commentary understanding
-   visual reasoning
-   multimodal decision support
-   publishing metadata generation

## Why local models?

The project requirement is to avoid mandatory paid AI APIs.

Benefits:

-   no per-video AI bill
-   greater privacy
-   offline-friendly after models are installed
-   predictable local workflow

Trade-offs:

-   slower than powerful cloud systems in some cases
-   hardware-sensitive
-   model formatting can be imperfect
-   local RAM and processing power matter

------------------------------------------------------------------------

# 13. SOFTWARE AND EXTERNAL PROGRAM REQUIREMENTS

## Operating system

Verified:

`Windows 11 Pro`

## Python

Verified:

`Python 3.12.10`

The project metadata specifies:

``` text
>=3.12,<3.13
```

Do not casually use Python 3.13.

## Git

Required for repository management.

## FFmpeg

Required for media processing.

Verify:

``` bat
ffmpeg -version
where ffmpeg
```

## Ollama

Verified development version:

`0.32.0`

Verify:

``` bat
ollama --version
ollama list
```

Required verified model:

``` text
gemma3:4b
```

## OpenVINO

Verified package version in the development environment:

`2026.2.1`

## Important Python package families

The environment includes packages for:

-   PyTorch
-   Transformers
-   Qwen ASR
-   Silero VAD
-   OpenVINO
-   OpenCV
-   PySceneDetect
-   SoundFile
-   FFmpeg Python wrapper
-   NumPy
-   Pydantic
-   PyYAML
-   Requests
-   Truststore

The exact committed `requirements.txt` should be used for the current
environment.

------------------------------------------------------------------------

# 14. INSTALLING PRESSSTARTAI ON A NEW COMPUTER

## Step 1: Check hardware first

Do not skip Section 1.

## Step 2: Install Python 3.12 64-bit

Verify:

``` bat
python --version
```

Expected version family:

``` text
Python 3.12.x
```

Verify 64-bit:

``` bat
python -c "import struct; print(struct.calcsize('P') * 8)"
```

Expected:

``` text
64
```

## Step 3: Install Git

Verify:

``` bat
git --version
```

## Step 4: Install FFmpeg

Verify:

``` bat
ffmpeg -version
where ffmpeg
```

## Step 5: Install Ollama

Verify:

``` bat
ollama --version
```

## Step 6: Install the Gemma model

Check:

``` bat
ollama list
```

If `gemma3:4b` is missing:

``` bat
ollama pull gemma3:4b
```

## Step 7: Clone the repository

``` bat
cd /d "C:\AI Projects"
git clone https://github.com/sunnygupta1990/PressStartAI.git
cd /d "C:\AI Projects\PressStartAI"
```

## Step 8: Check Git

``` bat
git status
git remote -v
```

## Step 9: Create a virtual environment

``` bat
python -m venv .venv
```

## Step 10: Activate it

Use Command Prompt:

``` bat
.venv\Scripts\activate.bat
```

Expected prompt:

``` text
(.venv) C:\AI Projects\PressStartAI>
```

### PowerShell warning

PowerShell activation previously failed because script execution was
disabled.

Command Prompt worked.

Do not spend time changing Windows execution policy unless PowerShell
support is actually required.

## Step 11: Install dependencies

``` bat
python -m pip install -r requirements.txt
```

## Step 12: Check dependency consistency

``` bat
python -m pip check
```

A previously verified environment returned:

``` text
No broken requirements found.
```

## Step 13: Check OpenVINO devices

``` bat
python -c "from openvino import Core; core = Core(); print(core.available_devices)"
```

Save the output.

## Step 14: Verify critical packages

``` bat
python -c "import cv2; print(cv2.__version__)"
python -c "import soundfile; print('SoundFile OK')"
python -c "import openvino; print(openvino.__version__)"
python -c "import qwen_asr; print('Qwen ASR OK')"
python -c "from silero_vad import load_silero_vad; print('Silero VAD OK')"
```

## Step 15: Run focused verification

Inspect the `tools` directory.

Run current verification scripts in logical order.

## Step 16: Run a real video

``` bat
python -m src.cli "C:\FULL\PATH\TO\VIDEO.mp4"
```

------------------------------------------------------------------------

# 15. VERIFYING A NEW INSTALLATION

An installation is not successful just because:

``` text
pip install completed
```

A proper verification should confirm the complete workflow.

## Environment checks

-   Python 3.12
-   virtual environment active
-   FFmpeg available
-   Ollama available
-   `gemma3:4b` installed
-   OpenVINO imports
-   Qwen ASR imports
-   Silero imports
-   SoundFile imports
-   OpenCV imports

## Media checks

-   video opens
-   audio extracts
-   generated MP4 has video
-   generated MP4 has audio
-   final resolution is correct

## AI checks

-   ASR runs
-   commentary reasoning runs
-   visual reasoning runs
-   multimodal fusion runs
-   metadata generation runs

## Output checks

For each approved final Short:

-   `final_short.mp4` exists
-   file size is not zero
-   video opens
-   audio is present
-   portrait dimensions are correct
-   `captions.srt` exists
-   captions are readable
-   hook is not empty
-   title is not empty
-   description is not empty
-   hashtags are not empty
-   thumbnail prompt is not empty

## Manual visual review

A human must watch the output.

Check:

-   Was the correct moment selected?
-   Does the clip begin too late?
-   Does the clip end too early?
-   Is the crop useful?
-   Is important gameplay cut off?
-   Are captions readable?
-   Are captions synchronized?
-   Is audio synchronized?
-   Does the Short feel complete?

------------------------------------------------------------------------

# 16. RUNNING PRESSSTARTAI

## Open Command Prompt

Move to the project:

``` bat
cd /d "C:\AI Projects\PressStartAI"
```

Activate the environment:

``` bat
.venv\Scripts\activate.bat
```

Run:

``` bat
python -m src.cli "C:\FULL\PATH\TO\VIDEO.mp4"
```

## Always quote Windows paths

Correct:

``` bat
python -m src.cli "C:\Users\Sunny\My Videos\gameplay.mp4"
```

Incorrect:

``` bat
python -m src.cli C:\Users\Sunny\My Videos\gameplay.mp4
```

Without quotes, spaces can split the path into several command
arguments.

## Original verified fixture command

``` bat
python -m src.cli "C:\Users\SunGupta\Downloads\returnal video\1.mp4"
```

The original fixture is for development history.

Do not hard-code it into production code.

------------------------------------------------------------------------

# 17. UNDERSTANDING THE OUTPUT

A run uses an organized folder structure.

A verified example looked like:

``` text
output/
└── runs/
    └── 20260715_205234_1_9b640c0c/
        └── shorts/
            ├── short_001/
            │   ├── final_short.mp4
            │   └── captions.srt
            └── short_004/
                ├── final_short.mp4
                └── captions.srt
```

## Why run folders exist

Without run folders, a new processing run could overwrite files from an
older run.

A run folder makes debugging easier.

You can say:

> "The problem happened in run X."

and inspect only that run.

## Why Short folders exist

Each approved Short is its own package.

This makes later product features easier, such as:

-   review screen
-   upload workflow
-   metadata editing
-   thumbnail generation
-   approval/rejection

------------------------------------------------------------------------

# 18. UNDERSTANDING PIPELINE TIMINGS

The CLI prints stage timings.

A verified timing example was:

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

## How to use timings

Suppose a run suddenly becomes 20 minutes slower.

Do not guess.

Compare stage timings.

If:

``` text
Transcribing commentary = 600 seconds
```

investigate ASR.

If:

``` text
Visual reasoning = 500 seconds per candidate
```

investigate the visual AI path.

If:

``` text
Building final YouTube Short packages = 900 seconds
```

investigate FFmpeg/rendering/captions.

Timings tell you where to look.

------------------------------------------------------------------------

# 19. DETAILED EXPLANATION OF EVERY MAJOR PROCESSING STAGE

## Video loading

Responsibility:

-   locate source
-   confirm it exists
-   inspect source information
-   expose duration to the pipeline

Common problems:

-   wrong path
-   unsupported media
-   damaged video
-   missing video stream

## Audio extraction

Responsibility:

-   create analysis audio

Common problems:

-   FFmpeg missing
-   video has no audio
-   unusual codec
-   file permissions

## Voice activity detection

Responsibility:

-   find likely speech

Historical working parameters included:

``` text
threshold                 = 0.5
minimum speech duration   = 250 ms
minimum silence duration  = 700 ms
speech padding            = 400 ms
```

Do not tune one value based on one clip.

## Speech chunk extraction

Historical defaults:

``` text
merge gap       = 2.0 seconds
maximum chunk   = 20.0 seconds
```

Why:

Very short chunks damaged language detection.

## Qwen ASR

Purpose:

Convert commentary audio to text.

Important limitation:

Hindi text can be imperfect.

Do not build logic that requires every recognized word to be correct.

## Scene detection

Historical configuration:

``` text
threshold                    = 27.0
minimum scene length frames  = 15
minimum scene duration       = 2.0 seconds
```

Short scenes are merged.

## Scene transcript mapping

Rule:

One transcript segment goes to the scene with maximum overlap.

This was a deliberate bug fix.

## Motion analysis

Historical method:

-   sample every 5 frames
-   grayscale
-   Gaussian blur
-   absolute frame difference
-   average difference

This is a lightweight motion signal.

It is not a full action-recognition neural network.

## Audio analysis

Measures:

-   average RMS
-   peak RMS

The audio is mixed game + commentary.

## Feature extraction

Combines low-cost signals.

## Scoring

Historical scoring:

``` text
45% motion
30% speech
25% audio
```

Relative normalization was used.

Potential future issue:

A relative score can behave differently depending on the intensity
distribution of the entire video.

## Candidate selection

Filters by score and candidate count.

Adds context padding.

## Overlap resolution

Reduces duplicate/overlapping moments.

## Clip generation

Creates candidate media.

## Commentary reasoning

Uses local AI to understand commentary.

The parser must handle imperfect AI formatting.

## Representative frames

Provides visual evidence without processing every frame through the AI.

## Visual reasoning

Uses local AI.

Historically, this was a major bottleneck.

Early visual reasoning took about 100 seconds per candidate.

After optimization:

``` text
Warmup          ≈ 2.61 seconds
Rank 1 visual   ≈ 11.56 seconds
Rank 4 visual   ≈ 11.82 seconds
```

Preserve warmup and efficient frame selection.

## Multimodal fusion

Combines commentary and visual reasoning.

## Final selection

Approves final highlights.

## Decision-to-clip linking

Ensures the AI decision references the correct clip.

## Final export

Writes final structured output.

Use UTF-8.

## Short builder

Builds final YouTube Short packages.

This stage can involve expensive video rendering.

## Caption pipeline

Creates timed caption segments, SRT, and rendered captions.

## Publishing metadata

Creates text needed to publish or prepare the Short.

------------------------------------------------------------------------

# 20. KNOWN HISTORICAL FAILURES AND LESSONS

This section can save days of repeated debugging.

## Whisper failed as the primary Hindi ASR

Tested:

`faster-whisper`

Observed:

-   Urdu detection
-   Urdu-script nonsense
-   English phrase recognized
-   Hindi missed
-   forced Hindi produced repeated nonsense

Conclusion:

Whisper is not the current primary ASR.

Do not switch back simply because Whisper is popular.

## FunASR returned Chinese for Hindi speech

Observed output included:

``` text
我这个了，都会压力太大。
```

Conclusion:

Rejected as primary ASR.

## Demucs did not isolate Sunny's voice reliably

Sunny listened to the stems.

His commentary was split between:

-   `vocals`
-   `other`

Conclusion:

Do not assume the Demucs vocals stem contains all commentary.

## Torchaudio/TorchCodec failed

The original VAD path used:

``` python
torchaudio.load
```

TorchCodec DLL loading failed.

Conclusion:

The working VAD path uses SoundFile.

Do not return to `torchaudio.load` without deliberately solving the
compatibility problem.

## DeepFilterNet installation failed

Reason:

-   Rust/Cargo missing
-   native compilation requirement

Conclusion:

Not part of the working pipeline.

## Tiny speech chunks caused random language detection

This was fixed by merging speech.

Lesson:

Always listen to and inspect ASR input chunks before blaming the model.

## Transcript was duplicated across scenes

The early mapper used broad overlap behavior.

Fix:

Maximum temporal overlap.

## Tool scripts sometimes could not import `src`

Working pattern:

``` python
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

Do not redesign production packaging solely because one tool was
launched incorrectly.

## Qwen produced warnings

Examples:

``` text
The following generation flags are not valid and may be ignored: ['temperature']
Setting pad_token_id to eos_token_id:151645 for open-end generation.
```

Transcription still worked.

Warnings are not automatically fatal errors.

## Ollama output was not always clean JSON

Possible AI output:

-   Markdown fences
-   prose
-   ANSI/control characters

The project added defensive parsing and sanitization.

Do not assume raw AI output is perfect JSON.

## Visual AI was originally extremely slow

Early pipeline time:

approximately 285 seconds on the small fixture.

Visual reasoning was around 100 seconds per candidate.

This was optimized.

Do not accidentally reintroduce repeated model cold starts.

## Publishing metadata was sometimes empty

One candidate had empty:

-   hook
-   title
-   description
-   hashtags
-   thumbnail prompt

This was rejected and validation was improved.

## AI generated unwanted Tamil script

Example:

``` text
OMG! செக் பண்ணு!
```

The intended context was Hindi/Hinglish/English.

Script validation was added.

Do not remove it accidentally.

------------------------------------------------------------------------

# 21. TROUBLESHOOTING GUIDE

## Error: `ModuleNotFoundError: No module named 'src'`

Check current folder:

``` bat
cd
```

Move to project:

``` bat
cd /d "C:\AI Projects\PressStartAI"
```

Check whether the virtual environment is active.

If the problem is in a `tools` script, inspect project-root path
handling.

## Error: FFmpeg not found

Run:

``` bat
where ffmpeg
ffmpeg -version
```

If these fail, fix FFmpeg installation/PATH first.

## Error: Ollama not found

Run:

``` bat
ollama --version
```

## Error: Gemma model missing

Run:

``` bat
ollama list
```

If missing:

``` bat
ollama pull gemma3:4b
```

## Error: ASR download SSL failure

Check:

-   internet access
-   corporate proxy
-   corporate SSL inspection
-   Windows certificates
-   trust store

The Qwen ASR service historically used:

``` python
truststore.inject_into_ssl()
```

Do not disable SSL verification globally as the first solution.

## Error: TorchCodec DLL failure

Do not move VAD audio loading back to Torchaudio.

Inspect the SoundFile path.

## ASR detects random languages

Inspect:

-   VAD regions
-   chunk duration
-   merge gap
-   exported speech WAV files

Listen to the chunks.

## Same transcript appears in several scenes

Inspect the transcript mapper.

Expected rule:

maximum temporal overlap.

## Pipeline is suddenly slow

Read stage timings.

Do not optimize the entire application blindly.

## Visual AI is slow

Check:

-   model warmup
-   repeated model loading
-   number of representative frames
-   input size
-   prompt size
-   candidate count

Use the visual benchmark script.

## Metadata is empty

Inspect:

-   raw Ollama response
-   sanitizer
-   parser
-   required-field validation
-   fallback behavior

Do not accept an incomplete package.

## No highlights are selected

This may be correct.

Inspect:

-   detected scenes
-   speech
-   features
-   scores
-   candidate threshold
-   overlap resolver
-   AI rejection decisions
-   confidence

Do not force a highlight from every video unless that becomes an
explicit product requirement.

## Final MP4 exists but does not play

Use:

``` bat
ffprobe "FULL_PATH_TO_VIDEO"
```

Check:

-   duration
-   video stream
-   audio stream
-   resolution
-   codec
-   file size

## Captions are missing

Trace:

``` text
ASR
→ ASR timestamps
→ selected clip timeline
→ caption segment conversion
→ SRT
→ caption renderer
```

## Captions are out of sync

Check source-time to clip-time conversion.

Example:

If a source sentence starts at 100 seconds and the selected clip starts
at 95 seconds:

``` text
caption time inside clip = 100 - 95 = 5 seconds
```

A timeline conversion bug can shift all captions.

------------------------------------------------------------------------

# 22. HOW TO DIAGNOSE A NEW ERROR

Use this process every time.

## 1. Record the exact command

Example:

``` bat
python -m src.cli "C:\Videos\test.mp4"
```

## 2. Record environment

``` bat
python --version
where python
git status
git log --oneline -5
```

## 3. Save the complete traceback

Do not send only the final error line.

The earlier lines show where the failure started.

## 4. Identify the last successful pipeline stage

Use console output and stage timings.

## 5. Find the relevant verification script

Look in:

``` text
tools/
```

## 6. Reproduce the smallest failure

If caption rendering fails, do not repeatedly run a two-hour gameplay
video.

Run caption verification.

## 7. Read the relevant code path

Read:

1.  model
2.  service
3.  caller
4.  pipeline
5.  CLI
6.  verification script

## 8. Compare with historical failures

Read Section 20.

## 9. Fix the root cause

Do not hide the exception.

## 10. Verify the component

Run focused verification.

## 11. Verify downstream integration

A component can pass alone but break its consumer.

## 12. Run the full CLI when necessary

Required for changes affecting final output.

## 13. Watch the generated Short

Human review is still required.

------------------------------------------------------------------------

# 23. HOW TO SAFELY CHANGE EXISTING FUNCTIONALITY

## Before editing

Run:

``` bat
git status
git branch
git log --oneline -10
```

Make sure you understand whether the working tree is clean.

## Read before changing

Do not open one file and immediately edit it.

Search for:

-   imports
-   constructors
-   method calls
-   attribute access
-   verification scripts

## Make one logical change

Bad change:

> Upgrade PyTorch, replace ASR, change scoring, and redesign captions in
> one commit.

Good changes:

1.  improve caption timing
2.  verify
3.  commit

Then:

1.  adjust scoring
2.  verify
3.  commit

## Preserve generic behavior

Never write:

``` python
if video_name == "1.mp4":
```

Never write:

``` python
if scene_start == 21.0:
```

Never hard-code the Returnal transcript.

The original video is a fixture.

## Verify after changing

Use the smallest relevant tool first.

Then run integration verification.

Then run the CLI if the change affects final output.

------------------------------------------------------------------------

# 24. HOW TO ADD NEW FUNCTIONALITY

Suppose you want to add:

> automatic game-name detection.

Use this design process.

## Step 1: Define the feature in one sentence

Example:

> Detect the likely game name from source frames and expose it to
> metadata generation.

## Step 2: Decide where it belongs in the pipeline

Ask:

-   What input does it need?
-   What output does it create?
-   Which later stages need it?

## Step 3: Define a data contract

Example concept:

``` python
GameIdentity(
    name: str,
    confidence: float,
)
```

## Step 4: Create a focused service

Example concept:

``` text
GameIdentityDetector
```

Avoid placing unrelated logic in `src/cli.py`.

## Step 5: Add verification

Create a small verification script or formal test.

## Step 6: Integrate it

Add it to the pipeline at the correct stage.

## Step 7: Update downstream consumers

Maybe metadata generation should receive the game identity.

## Step 8: Add timing if expensive

Any AI/media stage should be measurable.

## Step 9: Test failure behavior

What happens when the game cannot be identified?

A reasonable result may be:

``` text
name = unknown
confidence = 0.0
```

Do not crash the entire pipeline unnecessarily.

## Step 10: Run full verification

If final metadata changes, run the CLI.

## Step 11: Update documentation

Update this manual and the AI maintainer documentation.

------------------------------------------------------------------------

# 25. CHANGE IMPACT GUIDE

## If you change speech detection

You may affect:

-   speech chunks
-   ASR quality
-   transcripts
-   captions
-   commentary AI
-   highlight scores

Run full pipeline verification.

## If you change speech chunking

You may affect:

-   language detection
-   transcript completeness
-   ASR runtime

Remember the tiny-chunk failure.

## If you change ASR

You may affect:

-   transcript
-   scene mapping
-   captions
-   commentary AI
-   metadata

This is a major change.

## If you change scene detection

You may affect:

-   speech mapping
-   motion measurement
-   audio measurement
-   scores
-   candidate boundaries

## If you change motion analysis

You may affect:

-   ranking
-   candidate count

## If you change audio analysis

Remember:

The current signal is mixed game + commentary audio.

## If you change scoring

You may affect:

-   which candidates are selected
-   how many AI calls happen
-   total processing time
-   final highlight quality

Test multiple games.

## If you change overlap resolution

You may create:

-   duplicate highlights
-   missing context
-   incorrect clip links

## If you change commentary AI prompts

You may affect:

-   categories
-   interpretation
-   final decisions

## If you change the Ollama model

This can affect almost every AI stage.

Check:

-   output format
-   JSON reliability
-   speed
-   memory
-   visual capability
-   language quality

Treat model replacement as a major change.

## If you change visual frame extraction

You may affect:

-   visual understanding
-   speed

## If you change portrait reframing

You may affect final visible quality.

Test several games.

## If you change captions

Check:

-   timing
-   Unicode
-   SRT
-   rendering
-   font support

## If you change metadata generation

Preserve:

-   required fields
-   script validation
-   parser
-   sanitizer

## If you change a shared Python model

Search every consumer.

## If you change output folders

Check:

-   exporter
-   Short builder
-   CLI
-   verification tools

------------------------------------------------------------------------

# 26. TESTING AND VERIFICATION

The repository contains many verification scripts.

Examples include scripts for:

-   video loading
-   audio extraction
-   VAD
-   speech chunks
-   Qwen ASR
-   transcription
-   scene detection
-   scene/transcript mapping
-   motion
-   audio
-   highlight scoring
-   candidates
-   overlap
-   clips
-   commentary reasoning
-   visual reasoning
-   multimodal fusion
-   final selection
-   final export
-   captions
-   Short packages
-   OpenVINO

## Why these scripts matter

This project was developed one verified stage at a time.

The tools are part of the project's engineering history.

## Recommended future formal tests

### Unit tests

Good targets:

-   normalization
-   overlap math
-   timestamp conversion
-   maximum-overlap mapping
-   metadata validation
-   script validation

### Integration tests

Good targets:

-   VAD + chunks
-   chunks + ASR
-   scene + transcript mapping
-   features + scoring
-   final export
-   captions

### Golden fixture tests

Use small, legal media fixtures.

Do not commit full copyrighted gameplay.

## AI test warning

AI-generated wording may vary.

Do not create fragile tests that require an exact title such as:

``` text
Rage Boss Fight Moment!
```

unless generation is deterministic.

Instead test:

-   title is present
-   title is within expected limits
-   title uses allowed scripts
-   required structure is valid

------------------------------------------------------------------------

# 27. PERFORMANCE AND LONG-VIDEO CONSIDERATIONS

The final verified fixture was only:

`31.30 seconds`

The source was:

``` text
1920x1080
30 FPS
H.264
AAC
```

A verified final run took:

`168.87 seconds`

This does not prove a two-hour video will finish in a simple linear
multiple.

Long videos may create:

-   more scenes
-   more speech chunks
-   more temporary audio
-   more candidates
-   more disk usage
-   higher memory pressure

## Future validation durations

Test:

-   5 minutes
-   15 minutes
-   30 minutes
-   60 minutes
-   2 hours or more

## Record

-   total time
-   peak RAM
-   free disk before/after
-   speech chunk count
-   scene count
-   candidate count
-   final highlight count
-   ASR time
-   AI time
-   render time

## Different game types

Test:

-   slow story game
-   action game
-   shooter
-   dark game
-   bright game
-   game with subtitles
-   face cam
-   no face cam
-   HUD-heavy game
-   quiet commentary
-   continuous commentary

------------------------------------------------------------------------

# 28. HARDWARE PORTING AND COMPATIBILITY

## Moving to NVIDIA

Do not simply set:

``` python
device = "cuda"
```

and call the port complete.

Check:

-   PyTorch build
-   CUDA version
-   ASR compatibility
-   memory
-   Ollama behavior
-   OpenVINO assumptions
-   performance

## Moving to AMD

Treat as a compatibility project.

## Moving to macOS

Treat as a port.

Potential differences:

-   file paths
-   FFmpeg
-   Ollama
-   model runtime
-   OpenVINO
-   shell commands

## Moving to Linux

Treat as a port.

## Moving to newer Python

Build a fresh environment.

Do not upgrade the original environment in place first.

Run:

-   imports
-   pip check
-   verification tools
-   full CLI

------------------------------------------------------------------------

# 29. DEPENDENCY MANAGEMENT

The current `requirements.txt` is a large pinned environment snapshot.

It includes active production packages and historical experimental
packages.

Examples of important packages include:

``` text
torch==2.13.0
transformers==4.57.6
openvino==2026.2.1
openvino-tokenizers==2026.2.1.0
qwen-asr==0.0.6
silero-vad==6.2.1
opencv-python==5.0.0.93
scenedetect==0.7
ffmpeg-python==0.2.0
soundfile==0.14.0
numpy==2.4.6
truststore==0.10.4
```

Historical/experimental packages may include:

-   faster-whisper
-   Demucs
-   FunASR
-   TorchCodec
-   Torchaudio

## Do not randomly upgrade everything

This command is dangerous for a working AI project:

``` bat
pip install --upgrade <all packages>
```

AI dependencies have compatibility relationships.

## Safe dependency cleanup process

1.  clone the repository fresh
2.  create a new Python 3.12 environment
3.  inspect imports in production code
4.  list external executables
5.  list model download requirements
6.  create a minimal candidate requirements file
7.  install
8.  run all component verification
9.  run full CLI
10. compare output and timings
11. only then update committed requirements

------------------------------------------------------------------------

# 30. GIT AND REPOSITORY MAINTENANCE

## Before starting work

``` bat
git status
git branch
git log --oneline -10
```

## Before committing

``` bat
git status
git diff
```

## After verification

``` bat
git status
```

## Good commit examples

``` text
Fix caption timeline conversion
Add game identity detection
Improve visual frame sampling
Add hardware diagnostic command
```

## Bad commit example

``` text
updates
```

## Keep changes separated

Repository cleanup should not be mixed with AI model replacement.

Dependency upgrades should not be mixed with scoring changes.

This makes rollback and debugging easier.

------------------------------------------------------------------------

# 31. GENERATED FILES AND REPOSITORY HYGIENE

Generated media can become very large.

Do not accidentally commit:

-   source gameplay
-   extracted audio
-   speech chunks
-   candidate clips
-   final Shorts
-   model caches
-   Ollama data
-   Hugging Face cache
-   temporary frames
-   logs containing sensitive information

## Current hygiene concern

The repository contains:

``` text
separated/htdemucs/1
```

This appears to be historical Demucs output.

Investigate and clean it safely.

## Before every public push

Run:

``` bat
git status
git diff
```

Look at every new file.

------------------------------------------------------------------------

# 32. SECURITY AND PRIVACY

PressStartAI is local-first.

This is useful because gameplay and commentary do not need to be
uploaded to a paid AI provider.

However, maintainers must still be careful.

## Never commit

-   passwords
-   tokens
-   API keys
-   private `.env` files
-   private videos
-   private audio
-   credentials

## Absolute paths

Historical development used paths such as:

``` text
C:\Users\SunGupta\Downloads\returnal video\1.mp4
```

Production logic must not require Sunny's personal path.

## Public repository

The GitHub repository is public.

Assume every committed file can be read by anyone.

------------------------------------------------------------------------

# 33. CONFIGURATION AND TUNABLE VALUES

Possible configuration candidates include:

-   VAD threshold
-   minimum speech duration
-   minimum silence duration
-   speech padding
-   speech merge gap
-   maximum speech chunk duration
-   scene threshold
-   minimum scene duration
-   motion sampling interval
-   scoring weights
-   candidate score threshold
-   maximum candidate count
-   candidate padding
-   overlap rules
-   Ollama model name
-   ASR model name
-   final confidence threshold
-   portrait width
-   portrait height
-   caption style
-   metadata language rules

## Configuration warning

Not every constant should automatically become a user setting.

A setting can make the product harder to support.

Expose a value only when there is a real reason for a user or maintainer
to change it.

Validate configuration.

Example:

A negative portrait width should fail clearly.

------------------------------------------------------------------------

# 34. AI OUTPUT VALIDATION

Local AI output is not trusted automatically.

Why?

An AI model may:

-   add Markdown
-   add explanations
-   omit a field
-   return invalid JSON
-   use an unwanted language
-   return an empty string

## Validate structured AI output

Check:

-   can it be parsed?
-   are required keys present?
-   are values the correct type?
-   are required strings non-empty?
-   is confidence within the expected range?
-   is category allowed?
-   are scripts/languages allowed?

## Sanitization

The project historically needed:

-   Markdown-fence extraction
-   JSON extraction
-   ANSI/control-character removal

Do not simplify the parser without testing real Ollama output.

------------------------------------------------------------------------

# 35. CAPTIONS AND LANGUAGE HANDLING

The project is intended for:

-   Hindi
-   Hinglish
-   English

## Unicode

Always use UTF-8 for text output.

## ASR imperfection

Hindi transcription may not be exact.

Captions inherit ASR limitations.

## Unsupported script validation

The metadata pipeline once produced Tamil script.

The output context did not require Tamil.

Validation was added.

If future product requirements add languages, update validation
deliberately.

## Caption timing

Be careful when converting source timestamps to clip timestamps.

Source time:

``` text
100 seconds
```

Clip starts:

``` text
95 seconds
```

Caption time in Short:

``` text
5 seconds
```

This conversion is a common source of subtitle sync bugs.

------------------------------------------------------------------------

# 36. PORTRAIT VIDEO AND REFRAMING

Gaming footage is usually:

`16:9`

YouTube Shorts are:

`9:16`

The final target is:

`1080x1920`

## The crop problem

Imagine a wide game screen:

``` text
[ LEFT GAME AREA | CENTER ACTION | RIGHT HUD ]
```

A narrow vertical crop cannot show everything.

The application needs to decide what is important.

## Reframing considerations

Check:

-   action location
-   face cam
-   HUD
-   subtitles
-   boss health
-   player character
-   moving target

## Common crop failures

-   subject leaves frame
-   crop jumps rapidly
-   HUD is cut
-   face cam disappears
-   important enemy is off-screen
-   game subtitle is cut

## Any reframing change needs manual review

Numbers alone cannot prove crop quality.

------------------------------------------------------------------------

# 37. PUBLISHING METADATA

Each final Short should receive:

## Hook

A short attention-grabbing line.

Example:

``` text
OMG! Seriously?!
```

## Title

A suggested YouTube Short title.

Verified example:

``` text
Rage Boss Fight Moment!
```

## Description

A suggested video description.

## Hashtags

Verified example style:

``` text
#Gaming #HindiGaming #Reaction #Rage #FunnyFails #Shorts
```

## Thumbnail prompt

A creative instruction for later thumbnail generation.

Historical channel branding preferences include:

-   use Sunny's real face when a real face reference is provided to the
    image workflow
-   never change facial identity
-   black hoodie by default
-   expression should match the video mood
-   blue/black gaming branding

The PressStartAI repository creates a thumbnail prompt.

It does not automatically possess Sunny's face reference unless a future
image workflow receives it.

------------------------------------------------------------------------

# 38. RECOMMENDED FUTURE PRODUCT WORK

## First-run diagnostics

A very useful future feature would be:

``` bat
python -m src.cli --diagnose
```

It should check:

-   Windows
-   Python
-   RAM
-   CPU
-   GPU
-   NPU
-   FFmpeg
-   Ollama
-   Gemma model
-   OpenVINO
-   Qwen import
-   Silero import
-   OpenCV
-   SoundFile
-   disk space

Example:

``` text
[PASS] Windows 11
[PASS] Python 3.12.10
[PASS] 32 GB RAM
[PASS] FFmpeg
[PASS] Ollama
[PASS] gemma3:4b
[PASS] OpenVINO CPU
[PASS] OpenVINO GPU
[PASS] OpenVINO NPU
```

It should also create a JSON diagnostic report.

## Windows graphical interface

Future UI could allow:

1.  choose video
2.  click Analyze
3.  watch progress
4.  review highlights
5.  preview Shorts
6.  edit title/description
7.  approve output

## Resumable runs

If a two-hour video fails near the end, the application should ideally
resume from completed stages.

## Cancellation

Users should be able to stop processing safely.

## Output review screen

Show:

-   Short preview
-   score
-   AI confidence
-   category
-   hook
-   title
-   description
-   hashtags

## Better cross-game validation

Build a test library covering different game types.

------------------------------------------------------------------------

# 39. RECOMMENDED ENGINEERING IMPROVEMENTS

These are not statements that the current core is broken.

They are maturity improvements.

## Formal test suite

Expand `tests/`.

## Continuous integration

Automatically run safe non-model tests on GitHub changes.

Heavy AI/video tests may need a separate strategy.

## Dependency separation

Create clear production and development dependency lists.

## Documentation split

Recommended:

``` text
docs/
├── ARCHITECTURE.md
├── HARDWARE_COMPATIBILITY.md
├── INSTALLATION.md
├── TROUBLESHOOTING.md
├── MODEL_DECISIONS.md
├── PERFORMANCE_BASELINE.md
├── OUTPUT_SCHEMA.md
└── RELEASE_CHECKLIST.md
```

## License

The public repository should deliberately choose a software license.

## Changelog

Add:

``` text
CHANGELOG.md
```

## Structured logs

Machine-readable logs would improve support.

## Diagnostic report

A diagnostic JSON file would make remote support and AI-assisted
debugging easier.

------------------------------------------------------------------------

# 40. RELEASE CHECKLIST

Before calling a new version ready:

## Source

-   [ ] Correct branch
-   [ ] Git working tree reviewed
-   [ ] No accidental generated media
-   [ ] No secrets
-   [ ] Version updated if required

## Environment

-   [ ] Python version recorded
-   [ ] Ollama version recorded
-   [ ] Gemma model recorded
-   [ ] Requirements recorded
-   [ ] Hardware recorded

## Verification

-   [ ] `python -m pip check`
-   [ ] critical component verification
-   [ ] ASR verification
-   [ ] visual AI verification
-   [ ] full CLI run

## Final Short

-   [ ] MP4 exists
-   [ ] MP4 opens
-   [ ] audio works
-   [ ] 1080x1920
-   [ ] crop is acceptable
-   [ ] captions exist
-   [ ] captions are synchronized
-   [ ] captions are readable

## Metadata

-   [ ] hook present
-   [ ] title present
-   [ ] description present
-   [ ] hashtags present
-   [ ] thumbnail prompt present
-   [ ] supported script validation passed

## Performance

-   [ ] stage timings reviewed
-   [ ] no unexpected major regression

## Documentation

-   [ ] manual updated
-   [ ] AI maintainer documentation updated
-   [ ] changelog updated if present

------------------------------------------------------------------------

# 41. MAINTAINER QUICK REFERENCE

## Project folder

``` text
C:\AI Projects\PressStartAI
```

## Activate environment

``` bat
.venv\Scripts\activate.bat
```

## Run application

``` bat
python -m src.cli "FULL_VIDEO_PATH"
```

## Check dependencies

``` bat
python -m pip check
```

## Check OpenVINO

``` bat
python -c "from openvino import Core; core = Core(); print(core.available_devices)"
```

## Check FFmpeg

``` bat
ffmpeg -version
```

## Check Ollama

``` bat
ollama --version
ollama list
```

## Required verified Ollama model

``` text
gemma3:4b
```

## Main ASR

``` text
Qwen/Qwen3-ASR-0.6B
```

## Verified Python

``` text
3.12.10
```

## Verified hardware

``` text
Intel Core Ultra 7 155H
32 GB RAM
Intel Arc integrated graphics
Intel AI Boost NPU
Windows 11 Pro
```

## Git checks

``` bat
git status
git diff
git log --oneline -10
```

------------------------------------------------------------------------

# 42. GLOSSARY

## AI

Artificial Intelligence.

## ASR

Automatic Speech Recognition.

Converts spoken audio into text.

## Candidate

A possible highlight.

## Caption burn-in

Rendering subtitle text directly into the video image.

## CLI

Command-Line Interface.

## Codec

A technology used to encode/decode audio or video.

Examples:

-   H.264
-   AAC

## CPU

Central Processing Unit.

The main general-purpose processor.

## CUDA

NVIDIA's GPU computing platform.

PressStartAI does not currently require CUDA.

## Dataclass

A Python structure commonly used to store related values.

## FFmpeg

A powerful media processing application.

## FPS

Frames per second.

## GPU

Graphics Processing Unit.

## Heuristic

A practical rule or scoring method.

It is not necessarily a trained AI model.

## Highlight

A selected interesting gaming moment.

## Hinglish

A mixture of Hindi and English.

## Hugging Face

A platform/ecosystem commonly used for AI models.

## iGPU

Integrated GPU.

A graphics processor integrated into the system architecture.

## Inference

Running an already trained AI model.

## JSON

A structured text data format.

## Multimodal

Using several types of information.

## NPU

Neural Processing Unit.

Hardware designed for AI workloads.

## Ollama

A local AI model runner.

## OpenCV

A computer vision and image/video processing library.

## OpenVINO

Intel's AI inference toolkit.

## Pipeline

A sequence of processing stages.

## PySceneDetect

A library used to detect video scene changes.

## PyTorch

A machine-learning framework.

## Reframing

Changing which portion of a video remains visible when changing aspect
ratio.

## RMS

A mathematical measurement used here for audio energy.

## Scene

A detected visual section of a video.

## SRT

A subtitle file format.

## Transcript

Text created from spoken audio.

## Unicode

A standard that allows text from many languages, including Hindi.

## VAD

Voice Activity Detection.

Finds likely speech regions.

## VLM

Vision-Language Model.

An AI model that can reason about visual and text information.

------------------------------------------------------------------------

# 43. FINAL MAINTENANCE PRINCIPLES

If you remember only a few things from this manual, remember these:

1.  **Check the hardware before installing on a new computer.**
2.  **The verified reference machine is an Intel Core Ultra 7 155H
    Windows 11 laptop with 32 GB RAM, Intel Arc graphics, and Intel AI
    Boost NPU.**
3.  **Use Python 3.12.x unless you are deliberately porting the
    project.**
4.  **The project does not require NVIDIA or CUDA.**
5.  **The application is designed to run AI locally.**
6.  **Qwen3-ASR-0.6B is the current primary speech recognition model.**
7.  **Silero VAD finds speech before ASR.**
8.  **SoundFile replaced a failed Torchaudio/TorchCodec audio-loading
    path.**
9.  **Speech chunk size affects ASR language detection.**
10. **Do not return to tiny speech fragments without testing.**
11. **Whisper was not reliable enough as the primary Hindi/Hinglish ASR
    for the development fixture.**
12. **FunASR returned Chinese for Hindi speech during testing.**
13. **Demucs did not reliably isolate all of Sunny's commentary.**
14. **Transcript segments are mapped to the scene with maximum time
    overlap.**
15. **Motion and mixed-audio intensity are cheap first-pass signals.**
16. **Expensive local AI reasoning happens after candidate
    shortlisting.**
17. **Visual AI was historically the biggest bottleneck and was
    optimized.**
18. **Do not repeatedly reload or cold-start the visual AI model per
    candidate.**
19. **Raw Ollama output must be sanitized, parsed, and validated.**
20. **A final Short is not complete when publishing metadata is empty.**
21. **Language/script validation exists because a real AI output
    contained unwanted Tamil text.**
22. **The original Returnal clip is a test fixture, not production
    logic.**
23. **Never hard-code its timestamps, transcript, rank, or score.**
24. **Use pipeline timings to find performance problems.**
25. **Use focused verification scripts before running the complete
    pipeline.**
26. **Run the complete CLI after changes that can affect final output.**
27. **Watch the generated video manually.**
28. **Be careful when changing shared data models.**
29. **Do not randomly upgrade the AI dependency stack.**
30. **Keep generated videos, model caches, and private media out of the
    public repository.**
31. **The core pipeline is functionally complete; future UI and
    productization work are separate phases.**
32. **Maintain the project one logical, verified change at a time.**

------------------------------------------------------------------------

# Final Summary

PressStartAI is a local gaming-video intelligence and YouTube Shorts
generation system.

It takes gameplay footage and progressively reduces a large video into a
small number of high-value moments.

It combines:

-   video loading
-   audio extraction
-   human speech detection
-   speech chunk merging
-   local Hindi/Hinglish/English speech recognition
-   visual scene detection
-   speech-to-scene mapping
-   motion analysis
-   audio energy analysis
-   highlight scoring
-   candidate selection
-   overlap resolution
-   clip generation
-   commentary AI reasoning
-   visual AI reasoning
-   multimodal AI decision-making
-   final highlight approval
-   portrait Short rendering
-   intelligent reframing
-   captions
-   SRT subtitles
-   caption burn-in
-   hook generation
-   title generation
-   description generation
-   hashtag generation
-   thumbnail prompt generation
-   organized output packages
-   pipeline performance timings

The system works because of a series of deliberate technical decisions
made after real failures were observed.

The safest way to maintain PressStartAI is:

> **Understand the stage you are changing, understand what depends on
> it, make one logical change, run the smallest useful verification, run
> downstream verification, and finally test the real end-to-end
> application when the change can affect the final Short.**

This document should be updated whenever the architecture, supported
hardware, AI models, installation process, output structure, or major
troubleshooting knowledge changes.

**End of PressStartAI Human Maintenance and Development Manual.**
---

# PART II — DEEP TECHNICAL SOURCE-CODE REFERENCE

> **Why this part exists**
>
> The first part of this manual explains PressStartAI in plain English.
>
> This second part explains the code from a maintainer's technical point of view.
>
> For every production area, it explains:
>
> - the file name
> - whether the file is part of the real production CLI path or is older/bootstrap/experimental code
> - the classes and functions in the file
> - every important argument
> - the return value
> - the data objects the file consumes
> - the data objects the file creates
> - which later stage depends on the output
> - important failure cases
> - what a maintainer must check before changing the file
>
> **Repository snapshot used for this section:** public `main` branch reviewed on 15 July 2026 together with the final PressStartAI development handoff.
>
> **Important integrity alert:** the public repository currently does not contain most expected `src/models/*.py` files even though current `src/services/*.py` files import them. The `.gitignore` contains the broad pattern `models/`. The verified local development build used many model files that are documented in the development handoff. Therefore:
>
> 1. the local verified build and the public clone are not presently identical;
> 2. a fresh public clone can fail with `ModuleNotFoundError: No module named 'src.models....'`;
> 3. a maintainer must fix repository tracking before treating GitHub as a reproducible clean-install source;
> 4. this manual documents the expected model contracts from the verified development history so those files can be audited/recovered;
> 5. never invent missing model fields from memory—compare the local working tree and Git history before restoring files.
>
> The likely Git cause is the broad ignore rule:
>
> ```gitignore
> models/
> ```
>
> A Git ignore pattern containing a directory name without a leading `/` can affect a matching directory below the repository root. A safer intent for only the root AI model cache would normally be expressed using a root-specific pattern such as:
>
> ```gitignore
> /models/
> ```
>
> Do not change this blindly. First run `git check-ignore -v src\models\<file>.py` on the verified local project and compare `git ls-files src/models`.

---

# 44. WHICH ENTRY POINT IS THE REAL APPLICATION?

PressStartAI currently has more than one entry-looking file.

This can easily confuse a new maintainer.

## 44.1 `main.py` — early application bootstrap

Current purpose:

```text
main.py
  ↓
Application()
  ↓
Application.run()
```

Current functions:

### `main()`

**Arguments:** none.

**Returns:** nothing.

**What it does:**

1. creates an `Application` object;
2. calls `app.run()`.

Current high-level code relationship:

```python
from src.core.app import Application

def main():
    app = Application()
    app.run()
```

### `if __name__ == "__main__":`

This standard Python condition means:

> Run `main()` only when this file is executed directly.

### Maintenance warning

This is **not the verified production video-processing CLI path**.

The real end-to-end command used in final verification is:

```bat
python -m src.cli "VIDEO_FILE"
```

Do not add production highlight stages to `main.py` unless the architecture is intentionally being unified.

---

# 45. `src/core/app.py` — EARLY/BOOTSTRAP APPLICATION WRAPPER

## Status

**Bootstrap/legacy-style path, not the final production CLI orchestrator.**

## Imports

```python
Config
setup_logger
Pipeline
```

## Class: `Application`

This class packages three early application concepts:

- configuration
- logging
- a generic `Pipeline`

## `Application.__init__(self)`

### Arguments

Only `self`.

### Creates

```python
self.config = Config()
self.logger = setup_logger()
self.pipeline = Pipeline()
```

### Why each object exists

#### `self.config`

Loads YAML application configuration.

#### `self.logger`

Creates the configured PressStartAI logger.

#### `self.pipeline`

Creates the generic `src.core.pipeline.Pipeline`.

### Important technical observation

The current `Pipeline` class in `src/core/pipeline.py` is only a stub that prints:

```text
Pipeline initialized.
```

Therefore `Application` is not the path that executed the 100% complete highlight-to-Short workflow.

## `Application.run(self)`

### Arguments

Only `self`.

### Returns

Nothing.

### Steps

1. writes the log message `PressStartAI Started`;
2. calls `self.pipeline.run()`.

### Change impact

Changing this file currently affects direct execution through `main.py`.

It does not automatically change the verified `python -m src.cli` workflow.

### Before changing

Ask:

> Am I trying to change the real highlight pipeline, or only the older application wrapper?

For real highlight processing, inspect `src/cli.py` and `src/services/highlight_pipeline.py`.

---

# 46. `src/core/config.py` — YAML CONFIGURATION LOADER

## Class: `Config`

Purpose:

Load `config/config.yaml` and provide nested key lookup.

## `Config.__init__(self) -> None`

### Arguments

Only `self`.

### Local variable: `config_path`

```python
Path("config/config.yaml")
```

This is a **relative path**.

That means the current working directory matters.

Normal expectation:

```text
C:\AI Projects\PressStartAI
```

### Processing

```python
with config_path.open("r", encoding="utf-8") as f:
    self.data = yaml.safe_load(f)
```

### `yaml.safe_load`

Reads YAML and converts it to Python values such as:

- dictionaries
- strings
- numbers
- booleans

`safe_load` is preferred over the unsafe generic YAML loader.

### Created attribute

```python
self.data
```

Expected type in practice:

```python
dict
```

### Failure cases

- `config/config.yaml` does not exist
- wrong working directory
- invalid YAML syntax
- permission denied

## `Config.get(self, *keys)`

### Arguments

#### `*keys`

A variable number of nested mapping keys.

Example:

```python
config.get("application", "name")
```

Conceptually performs:

```python
self.data["application"]["name"]
```

### Internal variable: `value`

Starts as:

```python
self.data
```

Then repeatedly moves deeper:

```python
for key in keys:
    value = value[key]
```

### Returns

The final nested value.

### Important behavior

There is no default value.

There is no missing-key protection.

A missing key raises `KeyError`.

### Change guidance

If changing this to support defaults, do not silently change existing error behavior without checking every caller.

Example future API:

```python
get("application", "name", default="PressStartAI")
```

would require a deliberate signature design because `*keys` currently consumes all positional arguments.

---

# 47. `src/core/logger.py` — LOGGING CONFIGURATION

## Function: `setup_logger() -> logging.Logger`

Purpose:

Create the PressStartAI logging environment.

## Arguments

None.

## Step 1: Create logs directory

```python
logs_dir = Path("logs")
logs_dir.mkdir(parents=True, exist_ok=True)
```

### `parents=True`

Create parent directories when necessary.

### `exist_ok=True`

Do not fail if the directory already exists.

## Step 2: Find logging YAML

```python
config_file = Path("config") / "logging.yaml"
```

Equivalent path:

```text
config/logging.yaml
```

## Step 3: Read YAML

```python
yaml.safe_load(file)
```

## Step 4: Configure Python logging

```python
logging.config.dictConfig(config)
```

The logging YAML currently defines:

- a standard formatter
- console handler
- file handler
- root logging settings

The log file is:

```text
logs/pressstartai.log
```

## Step 5: Return named logger

```python
logging.getLogger("PressStartAI")
```

## Returns

A `logging.Logger`.

## Failure cases

- YAML missing
- invalid logging configuration
- log directory permission issue
- file handler cannot open output

## Change impact

Changing formatter or levels can affect support/debugging.

Do not remove debug file logging only because console output looks noisy.

---

# 48. `src/core/pipeline.py` — GENERIC STUB PIPELINE

## Status

**Not the complete highlight pipeline.**

## Class: `Pipeline`

## `Pipeline.__init__(self)`

Current body:

```python
pass
```

No attributes are initialized.

## `Pipeline.run(self)`

Current behavior:

```python
print("Pipeline initialized.")
```

## Maintainer warning

The existence of this class can mislead a contributor into believing this is the production pipeline.

The actual verified orchestration is performed by:

```text
src/services/highlight_pipeline.py
```

and called by:

```text
src/cli.py
```

## Recommended future cleanup

One of the following should eventually be chosen:

### Option A

Remove the obsolete bootstrap pipeline and make `main.py` call the production CLI/application service.

### Option B

Turn `src.core.pipeline.Pipeline` into the official top-level orchestrator and make `HighlightPipeline` a sub-pipeline.

### Option C

Clearly label this file as legacy/bootstrap.

Do not maintain two competing production orchestrators.

---

# 49. `src/exceptions/pipeline_execution_error.py`

## Class: `PipelineExecutionError(RuntimeError)`

Purpose:

Wrap a failure with the name of the pipeline stage that failed.

This makes an error such as:

```text
FileNotFoundError
```

more useful:

```text
Extracting audio: source file does not exist
```

## Constructor

```python
__init__(
    self,
    stage: str,
    message: str,
) -> None
```

## Argument: `stage`

Human-readable pipeline stage name.

Examples:

```text
Loading video
Extracting audio
Transcribing commentary
Building final YouTube Short packages
```

## Argument: `message`

Technical error message.

## Attribute

```python
self.stage
```

The CLI uses this to print the failure stage separately.

## Parent exception message

The constructor calls:

```python
super().__init__(f"{stage}: {message}")
```

Therefore `str(error)` contains the stage and message.

## `__cause__`

The pipeline stage runner may raise this error `from` the original exception.

The CLI checks:

```python
error.__cause__ or error
```

This allows it to report the original exception type.

## Change impact

Do not remove the `stage` attribute unless `src/cli.py` is also changed.

---

# 50. `src/cli.py` — REAL VERIFIED COMMAND-LINE ENTRY POINT

## Status

**Production entry path used in final end-to-end verification.**

Normal command:

```bat
python -m src.cli "C:\path\to\video.mp4"
```

## Imports and responsibilities

### `argparse`

Command-line argument parsing.

### `Path`

Windows/path handling.

### `PipelineExecutionError`

Stage-aware exception.

### `PipelineError`

Display-friendly structured error model.

### `PipelineProgress`

Progress callback data.

### `HighlightPipeline`

Actual end-to-end processing pipeline.

### `PipelineRunPathBuilder`

Creates unique working/output run folders.

## Function: `parse_arguments() -> argparse.Namespace`

Creates an `ArgumentParser`.

### Positional argument: `video_file`

Required.

Help text:

```text
Path to the source gaming video.
```

Example:

```bat
python -m src.cli "C:\Videos\gameplay.mp4"
```

### Optional argument: `--working-folder`

Default:

```python
None
```

Purpose:

Override temporary/working output folder.

When omitted, a unique run folder is generated.

Example:

```bat
python -m src.cli "C:\Videos\game.mp4" --working-folder "D:\PSAIWork"
```

### Optional argument: `--output-folder`

Default:

```python
None
```

Purpose:

Override final output folder.

### Returns

`argparse.Namespace`.

Expected attributes:

```python
arguments.video_file
arguments.working_folder
arguments.output_folder
```

## Function: `print_progress(progress: PipelineProgress) -> None`

### Argument: `progress`

A `PipelineProgress` data object.

Expected fields:

```text
step
total_steps
message
```

### Output format

```text
[5/27] Transcribing commentary...
```

### Returns

Nothing.

## Function: `print_pipeline_error(error: PipelineError) -> None`

### Argument: `error`

Structured pipeline error.

Expected fields:

```text
stage
message
exception_type
```

### Prints

A formatted error block.

### Returns

Nothing.

## Function: `main() -> None`

This is the actual CLI coordinator.

### Step 1: Parse arguments

```python
arguments = parse_arguments()
```

### Step 2: Convert source path

```python
video_file = Path(arguments.video_file)
```

Note that it does not immediately call `.resolve()`.

### Step 3: Build unique run paths

```python
path_builder = PipelineRunPathBuilder()
run_paths = path_builder.build(video_file=str(video_file))
```

Expected `run_paths` fields:

```text
run_id
working_folder
output_folder
```

### Step 4: Apply CLI overrides

```python
working_folder = arguments.working_folder or run_paths.working_folder
output_folder = arguments.output_folder or run_paths.output_folder
```

Meaning:

- use explicit user path if supplied;
- otherwise use automatically generated run paths.

### Step 5: Create production pipeline

```python
pipeline = HighlightPipeline()
```

### Step 6: Run pipeline

```python
result = pipeline.run(
    video_file=str(video_file),
    working_folder=working_folder,
    output_folder=output_folder,
    progress_callback=print_progress,
)
```

#### `video_file`

Source gaming video.

#### `working_folder`

Temporary/intermediate run files.

#### `output_folder`

Final output.

#### `progress_callback`

Function called by the pipeline to report stage progress.

### Step 7: Handle stage-aware failure

```python
except PipelineExecutionError as error:
```

It creates a `PipelineError`.

The reported underlying exception is:

```python
error.__cause__ or error
```

### Step 8: Handle unexpected startup/top-level failure

```python
except Exception as error:
```

Stage is shown as:

```text
Starting pipeline
```

### Step 9: Print `PipelineResult`

Expected result fields used by the CLI:

```text
source_video_file
video_duration_seconds
highlight_count
exported_file_count
short_package_count
total_duration_seconds
short_packages
stage_timings
```

### Step 10: Print each `ShortPackage`

Expected package properties:

```text
rank
final_video_file
subtitle_file
category
confidence
metadata
```

Expected metadata:

```text
hook
title
description
hashtags
thumbnail_prompt
```

### Step 11: Print timings

For every `PipelineStageTiming`:

```python
timing.stage
timing.duration_seconds
```

## Most important change rule for `cli.py`

Keep orchestration thin.

Do not put:

- motion algorithms
- FFmpeg filters
- ASR inference
- scoring formulas

directly into the CLI.

The CLI should parse input, invoke services, and present results.

---

# 51. `src/models/pipeline_run_paths.py`

## Status

Present in public repository.

## Dataclass: `PipelineRunPaths`

Decorator:

```python
@dataclass(slots=True, frozen=True)
```

### `slots=True`

Prevents arbitrary new attributes and reduces per-object overhead.

### `frozen=True`

Makes the dataclass immutable after creation.

## Fields

### `run_id: str`

Unique identifier for one processing run.

### `working_folder: str`

Temporary/intermediate processing folder.

### `output_folder: str`

Final run output folder.

## Used by

`PipelineRunPathBuilder` and `src/cli.py`.

## Change impact

If fields are renamed, update:

- path builder
- CLI
- any diagnostics
- tests/verification scripts

---

# 52. `src/models/pipeline_stage_timing.py`

## Dataclass: `PipelineStageTiming`

Fields:

### `stage: str`

Human-readable stage name.

### `duration_seconds: float`

Elapsed stage duration.

## Used by

- `PipelineStageRunner`
- `PipelineResult`
- CLI timing display

## Design reason

Timing is data instead of only console text.

This allows future:

- GUI timing views
- JSON diagnostics
- performance regression comparison

---

# 53. EXPECTED MODEL LAYER — REPOSITORY TRACKING ALERT

The verified development history used the following model modules.

Most are currently imported by public service files but are missing from the public `src/models` directory.

This section documents their expected role and known contracts.

## 53.1 `src/models/asr_segment.py`

Expected dataclass:

```python
ASRSegment
```

Fields:

### `start_seconds: float`

Start time on original source video timeline.

### `end_seconds: float`

End time on source timeline.

### `language: str`

ASR-reported language.

### `text: str`

Recognized text.

Used by:

- `TranscriptionPipeline`
- `SceneTranscriptMapper`
- `SceneAnalysis`

---

## 53.2 `src/models/speech_chunk.py`

Expected dataclass:

```python
SpeechChunk
```

Fields:

### `file_path: str`

Exported WAV file.

### `start_seconds: float`

Original source timeline start.

### `end_seconds: float`

Original source timeline end.

Used by:

- `SpeechChunkExtractor`
- Qwen transcription pipeline

---

## 53.3 `src/models/scene.py`

Expected dataclass:

```python
Scene
```

Fields:

```python
start_seconds: float
end_seconds: float
```

Property:

### `duration_seconds -> float`

Returns:

```python
end_seconds - start_seconds
```

Used by:

- scene detection
- transcript mapping
- motion analysis
- audio analysis
- feature extraction

---

## 53.4 `src/models/scene_analysis.py`

Expected dataclass fields:

```python
scene: Scene
transcript_segments: list[ASRSegment]
```

Property:

### `transcript_text -> str`

Joins non-empty segment text with spaces.

Important:

This object represents **one scene plus speech assigned to that scene**.

---

## 53.5 `src/models/motion_features.py`

Expected fields:

```python
scene_start_seconds: float
scene_end_seconds: float
average_motion_score: float
maximum_motion_score: float
```

---

## 53.6 `src/models/audio_features.py`

Expected fields:

```python
scene_start_seconds: float
scene_end_seconds: float
average_rms: float
maximum_rms: float
```

---

## 53.7 `src/models/highlight_features.py`

Expected fields:

```python
scene_start_seconds: float
scene_end_seconds: float
scene_duration_seconds: float
transcript_text: str
has_speech: bool
speech_character_count: int
speech_word_count: int
average_motion_score: float
maximum_motion_score: float
average_audio_rms: float
maximum_audio_rms: float
```

This is the combined low-cost feature vector for one scene.

---

## 53.8 `src/models/highlight_score.py`

Expected fields:

```python
features: HighlightFeatures
speech_score: float
motion_score: float
audio_score: float
final_score: float
```

The original raw `HighlightFeatures` remain available through `features`.

---

## 53.9 `src/models/highlight_candidate.py`

Expected fields:

```python
start_seconds: float
end_seconds: float
rank: int
score: HighlightScore
```

Property:

```python
duration_seconds
```

returns:

```python
end_seconds - start_seconds
```

The development implementation stored the full `HighlightScore`, not only a numeric score.

This is why downstream `GeneratedHighlight` can expose transcript and heuristic data through the candidate/score relationship.

---

## 53.10 `src/models/generated_highlight.py`

Purpose:

Represent a physically generated candidate MP4 linked to the candidate that created it.

Known design:

```python
file_path: str
candidate: HighlightCandidate
```

Expected convenience properties from development use include:

```text
rank
start_seconds
end_seconds
duration_seconds
final_score
transcript_text
```

These properties delegate to `candidate` and `candidate.score.features`.

Used by:

- commentary reasoner
- frame extractor
- visual reasoner
- analysis combiner
- final highlight combiner

---

## 53.11 `src/models/highlight_reasoning.py`

Purpose:

Structured result from commentary AI reasoning.

Known fields used by downstream code:

```text
rank
is_interesting
category
reason
confidence
```

`HighlightAnalysisCombiner` matches this model by `rank`.

---

## 53.12 `src/models/analyzed_highlight.py`

Purpose:

Combine:

```text
GeneratedHighlight
+
HighlightReasoning
```

Known constructor relationship:

```python
AnalyzedHighlight(
    highlight=highlight,
    reasoning=reasoning,
)
```

Known convenience properties used by fusion reasoning:

```text
rank
is_interesting
category
confidence
reason
transcript_text
final_score
```

The point of this wrapper is to avoid passing two matching objects around separately.

---

## 53.13 `src/models/visual_reasoning.py`

Known fields:

```text
rank
visual_event
action_level
danger_level
looks_interesting
reason
confidence
```

Expected level values:

```text
low
medium
high
```

---

## 53.14 `src/models/highlight_fusion.py`

Purpose:

Final multimodal AI decision.

Known fields from `HighlightFusionReasoner` construction:

```text
rank
keep_highlight
category
event_summary
commentary_category
visual_event
action_level
danger_level
final_confidence
reason
```

Used by:

- `FinalHighlightSelector`
- `FinalHighlightCombiner`

---

## 53.15 `src/models/final_highlight.py`

Known exact development contract:

```python
highlight: GeneratedHighlight
fusion: HighlightFusion
```

Properties:

### `file_path`

Delegates to `highlight.file_path`.

### `rank`

Delegates to generated highlight.

### `start_seconds`

Source-video start.

### `end_seconds`

Source-video end.

### `duration_seconds`

Highlight duration.

### `transcript_text`

Approximate transcript.

### `heuristic_score`

Returns generated highlight final heuristic score.

### `category`

Final fused category.

### `event_summary`

Fused event description.

### `commentary_category`

Commentary AI category.

### `visual_event`

Visual AI event description.

### `action_level`

Visual action classification.

### `danger_level`

Visual danger classification.

### `confidence`

Final fusion confidence.

### `reason`

Final AI reason.

This model is heavily consumed by the export and final Short pipeline.

Changing it has wide impact.

---

## 53.16 `src/models/caption_segment.py`

Expected fields:

```python
start_seconds: float
end_seconds: float
text: str
```

Used by:

- `CaptionSegmentBuilder`
- `SRTWriter`

Times are relative to the final Short, not the original source timeline.

---

## 53.17 `src/models/rendered_short.py`

Known constructor use:

```python
RenderedShort(
    file_path=str(output_file),
    highlight=highlight,
    width=1080,
    height=1920,
)
```

Expected fields:

```text
file_path
highlight
width
height
```

Likely convenience properties delegate rank/category information through the final highlight.

---

## 53.18 `src/models/short_metadata.py`

Known constructor fields:

```text
rank
hook
title
description
hashtags
thumbnail_prompt
```

### `hashtags`

A list of strings.

Current validation expects every hashtag to start with `#`.

---

## 53.19 `src/models/short_package.py`

Known constructor:

```python
ShortPackage(
    rendered_short=rendered_short,
    final_video_file=final_video_file,
    subtitle_file=subtitle_file,
    metadata=metadata,
)
```

Expected convenience properties used by CLI:

```text
rank
category
confidence
```

The package is the public result object for one completed Short.

---

## 53.20 `src/models/pipeline_progress.py`

Known fields used by CLI:

```text
step
total_steps
message
```

---

## 53.21 `src/models/pipeline_error.py`

Known fields used by CLI:

```text
stage
message
exception_type
```

---

## 53.22 `src/models/pipeline_result.py`

Known fields used by CLI:

```text
source_video_file
video_duration_seconds
final_highlights / highlight_count
exported_files / exported_file_count
short_packages / short_package_count
stage_timings
total_duration_seconds
```

The exact implementation should be recovered from the verified local repository.

Do not guess property names when restoring the public repository.

---

## 53.23 `src/models/video_info.py`

Fields constructed by `VideoLoader`:

```text
file_path
file_name
duration_seconds
width
height
fps
video_codec
audio_codec
video_bitrate
audio_bitrate
file_size
rotation
```

---

## 53.24 `src/models/transcript.py`

Historical Whisper branch model.

Known classes:

### `TranscriptSegment`

Fields constructed by `TranscriptService`:

```text
start
end
text
avg_logprob
no_speech_probability
```

### `Transcript`

Fields:

```text
language
duration
segments
```

This is part of the rejected/legacy Whisper path, not the Qwen primary ASR pipeline.

---

# 54. `src/services/video_loader.py`

## Class: `VideoLoader`

## Method: `load(self, video_path: str) -> VideoInfo`

### Argument: `video_path`

Path to source media.

### Step 1: Convert to `Path`

```python
path = Path(video_path)
```

### Step 2: Existence check

```python
if not path.exists():
    raise FileNotFoundError(video_path)
```

Technical note:

It checks existence, not `is_file()`.

A directory path would pass this check but later FFprobe would fail.

### Step 3: Probe media

```python
probe = ffmpeg.probe(str(path))
```

This invokes FFprobe through the FFmpeg environment.

### Step 4: Select first video stream

```python
next(
    s for s in probe["streams"]
    if s["codec_type"] == "video"
)
```

Failure:

`StopIteration` if no video stream exists.

### Step 5: Find optional audio stream

```python
next(..., {})
```

If there is no audio stream, an empty dictionary is used.

### Step 6: Calculate FPS

Reads:

```python
video_stream["r_frame_rate"]
```

Expected form:

```text
30000/1001
30/1
```

It splits on `/` and divides numerator by denominator.

Potential edge case:

denominator zero or unusual FFprobe rate format.

### Returns `VideoInfo`

Maps FFprobe values into a stable internal contract.

### Change impact

Every pipeline run starts here.

If the duration or FPS calculation changes, scene/motion/timestamp behavior can change.

---

# 55. `src/services/audio_extractor.py`

## Class: `AudioExtractor`

## Method

```python
extract(
    self,
    input_video: str,
    output_audio: str,
    sample_rate: int = 16000,
) -> str
```

## `input_video`

Source video path.

## `output_audio`

Target WAV path.

Example:

```text
<working folder>/audio.wav
```

## `sample_rate`

Default:

```text
16000 Hz
```

This is the verified ASR/VAD analysis rate.

## Output folder creation

```python
output_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)
```

## FFmpeg settings

```text
ac=1
ar=sample_rate
vn=None
acodec=pcm_s16le
```

### `ac=1`

Mono.

### `ar=16000`

16 kHz by default.

### `vn=None`

No video stream in output.

### `pcm_s16le`

16-bit little-endian PCM WAV audio.

## Returns

String path to output audio.

## Important failure behavior

`ffmpeg.run(..., quiet=True)` can raise an FFmpeg exception.

The method does not independently verify that output file exists after FFmpeg completes.

---

# 56. `src/services/voice_activity_detector.py`

## Class: `VoiceActivityDetector`

Purpose:

Find likely human speech.

## Constructor

```python
__init__(self) -> None
```

Loads the Silero VAD model:

```python
self.model = load_silero_vad()
```

### Performance note

Creating this object loads a model.

Do not recreate it in a tight loop unnecessarily.

## Method

```python
detect(
    self,
    audio_file: str,
) -> list[dict[str, Any]]
```

## `audio_file`

Expected analysis WAV.

## Audio loading

```python
sf.read(
    audio_file,
    dtype="float32",
    always_2d=False,
)
```

Returns:

```text
audio
sample_rate
```

## Stereo handling

If:

```python
audio.ndim > 1
```

channels are averaged:

```python
np.mean(audio, axis=1)
```

## Type normalization

```python
np.asarray(audio, dtype=np.float32)
```

## Silero parameters

```text
threshold = 0.5
min_speech_duration_ms = 250
min_silence_duration_ms = 700
speech_pad_ms = 400
return_seconds = False
```

## `return_seconds=False`

Silero returns sample indexes such as:

```python
{"start": 58400, "end": 91616}
```

not seconds.

`SpeechChunkExtractor` converts samples to seconds later.

## Returns

List of dictionaries.

Each dictionary is expected to contain:

```text
start
end
```

## Do not change casually

Chunking and ASR quality depend on these boundaries.

---

# 57. `src/services/speech_chunk_extractor.py`

## Class: `SpeechChunkExtractor`

Purpose:

Merge nearby VAD segments and write WAV chunks.

## Method

```python
extract(
    self,
    input_audio: str,
    speech_segments: list[dict[str, Any]],
    output_folder: str,
    merge_gap_seconds: float = 2.0,
    maximum_chunk_seconds: float = 20.0,
) -> list[SpeechChunk]
```

## Arguments

### `input_audio`

Full analysis audio.

### `speech_segments`

Silero output using sample indexes.

Expected item:

```python
{
    "start": int,
    "end": int,
}
```

### `output_folder`

Folder for:

```text
speech_001.wav
speech_002.wav
...
```

### `merge_gap_seconds`

Default:

```text
2.0
```

If the next speech begins within this gap, it may be merged.

### `maximum_chunk_seconds`

Default:

```text
20.0
```

A proposed merge cannot exceed this duration.

## Existing output cleanup

Deletes:

```text
speech_*.wav
```

inside the supplied output folder.

Important:

Never point `output_folder` at a folder containing unrelated files with matching names.

## `_merge_segments(...)`

Arguments:

```text
speech_segments
sample_rate
merge_gap_seconds
maximum_chunk_seconds
```

### Conversion to samples

```python
merge_gap_samples = int(
    merge_gap_seconds * sample_rate
)
```

### Merge decision

```python
gap <= merge_gap_samples
and
proposed_duration <= maximum_chunk_samples
```

Both conditions must be true.

## Generated `SpeechChunk`

For each merged segment:

```text
file_path
start_seconds
end_seconds
```

Source timeline conversion:

```python
start_sample / sample_rate
end_sample / sample_rate
```

## Historical importance

This component fixed random ASR language detection caused by tiny chunks.

---

# 58. `src/services/asr/base_asr.py`

## Class: `BaseASR(ABC)`

An abstract interface.

`ABC` means abstract base class.

Purpose:

Define a common contract for speech recognition engines.

## Abstract method

```python
transcribe(
    self,
    audio_file: str,
) -> Any
```

## Argument

Path to one audio file.

## Why `@abstractmethod`

A subclass is expected to implement `transcribe`.

Example:

```python
class QwenASR(BaseASR):
    def transcribe(...):
        ...
```

## Technical weakness

Return type is currently `Any`.

The Qwen implementation actually returns `ASRResult`.

A future cleanup could make the interface typed with a protocol/shared result model.

---

# 59. `src/services/asr/qwen_asr.py`

## Local dataclass: `ASRResult`

Fields:

```text
language: str
text: str
audio_file: str
```

Note:

This model is defined inside the service file, unlike most project data models.

## Class: `QwenASR(BaseASR)`

## Constant

```python
MODEL_NAME = "Qwen/Qwen3-ASR-0.6B"
```

## Constructor

```python
__init__(self) -> None
```

### SSL trust integration

```python
truststore.inject_into_ssl()
```

This was added in the environment where certificate/model-download behavior mattered.

### Model creation

```python
Qwen3ASRModel.from_pretrained(
    MODEL_NAME,
    dtype=torch.float32,
    device_map="cpu",
    max_inference_batch_size=1,
    max_new_tokens=256,
)
```

#### `dtype=torch.float32`

Full 32-bit floating-point inference.

#### `device_map="cpu"`

The current ASR path is explicitly CPU-oriented.

#### `max_inference_batch_size=1`

One item per inference batch.

#### `max_new_tokens=256`

Maximum generated transcription token budget.

## Method

```python
transcribe(
    self,
    audio_file: str,
) -> ASRResult
```

### File validation

Uses:

```python
Path(audio_file).is_file()
```

### Model call

```python
self.model.transcribe(
    audio=str(audio_path),
    language=None,
)
```

### `language=None`

Automatic language detection.

Historical note:

Automatic detection only became stable after speech chunks were merged.

### Empty result behavior

Returns:

```python
ASRResult(
    language="unknown",
    text="",
    audio_file=...
)
```

It does not raise merely because no text was recognized.

### Non-empty result

Only the first result is used:

```python
result = results[0]
```

## Change impact

Replacing this model affects:

- transcription
- scene text
- captions
- commentary reasoning
- metadata quality

---

# 60. `src/services/asr/transcription_pipeline.py`

## Class: `TranscriptionPipeline`

Purpose:

Apply ASR to all `SpeechChunk` objects and restore original source timestamps.

## Constructor

Known design:

```python
self.asr = QwenASR()
```

## Method

```python
transcribe(
    self,
    speech_chunks: list[SpeechChunk],
) -> list[ASRSegment]
```

## `speech_chunks`

Ordered chunks created by `SpeechChunkExtractor`.

## Per chunk

Calls:

```python
self.asr.transcribe(chunk.file_path)
```

## Empty transcript behavior

```python
if not result.text:
    continue
```

No `ASRSegment` is created for empty text.

## Created segment

```python
ASRSegment(
    start_seconds=chunk.start_seconds,
    end_seconds=chunk.end_seconds,
    language=result.language,
    text=result.text,
)
```

Important:

The ASR itself transcribes a standalone WAV beginning at zero.

This pipeline attaches the original source-video start/end from `SpeechChunk`.

---

# 61. `src/services/transcript_engine.py` — LEGACY WHISPER EXPERIMENT

## Status

**Experimental/rejected primary ASR path.**

## Class: `TranscriptEngine`

## Constructor

```python
__init__(
    self,
    model_name="large-v3-turbo",
    device="cpu",
    compute_type="int8",
)
```

### `model_name`

Whisper model identifier.

### `device`

Default CPU.

### `compute_type`

Default int8.

## Creates

```python
WhisperModel(
    model_name,
    device=device,
    compute_type=compute_type,
    download_root="models/cache",
)
```

## Method

```python
transcribe(self, audio_file)
```

Uses:

```text
beam_size=5
vad_filter=False
```

Returns:

```python
info.language, results
```

`results` is a list of dictionaries:

```text
start
end
text
```

## Maintenance rule

Do not confuse this with the production Qwen transcription pipeline.

---

# 62. `src/services/transcript_service.py` — SECOND WHISPER EXPERIMENT

## Status

Legacy/experimental.

## Constructor

Hard-codes:

```text
large-v3-turbo
CPU
int8
models/cache
```

## Method

```python
transcribe(
    self,
    video_path: str,
) -> Transcript
```

Despite the argument name, Whisper can extract/process audio from the provided media path.

## Whisper parameters

```text
language="hi"
beam_size=5
best_of=5
temperature=0.0
condition_on_previous_text=False
vad_filter=True
min_silence_duration_ms=500
word_timestamps=True
```

## Creates `TranscriptSegment`

For every non-empty segment:

```text
start
end
text
avg_logprob
no_speech_probability
```

## Returns `Transcript`

```text
language
duration
segments
```

## Historical verdict

Whisper was rejected as primary Hindi/Hinglish ASR for the verified fixture.

Keep this file clearly marked experimental or remove/archive it in a deliberate cleanup.

---

# 63. `src/services/scene_detector.py`

## Class: `SceneDetector`

## Constructor

```python
__init__(
    self,
    threshold: float = 27.0,
    minimum_scene_length_frames: int = 15,
    minimum_scene_duration_seconds: float = 2.0,
) -> None
```

## `threshold`

PySceneDetect `ContentDetector` sensitivity.

This is not a probability.

Changing it changes how easily visual changes create scene cuts.

## `minimum_scene_length_frames`

Passed to:

```python
ContentDetector(
    min_scene_len=...
)
```

## `minimum_scene_duration_seconds`

Used by PressStartAI's own post-processing merge.

## Method

```python
detect(
    self,
    video_file: str,
) -> list[Scene]
```

### File validation

Requires `is_file()`.

### Scene detection call

```python
detect(
    str(video_path),
    ContentDetector(
        threshold=self.threshold,
        min_scene_len=self.minimum_scene_length_frames,
    ),
    show_progress=False,
)
```

### Converts PySceneDetect timecodes

```python
start_time.get_seconds()
end_time.get_seconds()
```

### Calls `_merge_short_scenes`

Returns merged list.

## `_merge_short_scenes(self, scenes: list[Scene]) -> list[Scene]`

If current accumulated duration is less than the configured minimum, the next scene is merged into it by extending `current_end`.

## Important algorithm behavior

It checks the duration of the current accumulated scene **before** appending it.

This is not the same as independently deleting all scenes shorter than two seconds.

---

# 64. `src/services/scene_transcript_mapper.py`

## Class: `SceneTranscriptMapper`

## Method

```python
map(
    self,
    scenes: list[Scene],
    transcript_segments: list[ASRSegment],
) -> list[SceneAnalysis]
```

## Algorithm

Creates one empty transcript list per scene:

```python
scene_segments = [
    [] for _ in scenes
]
```

For each ASR segment:

```python
best_scene_index = self._find_best_scene(...)
```

If a scene overlaps:

```python
scene_segments[best_scene_index].append(segment)
```

## Returns

One `SceneAnalysis` per input scene.

Therefore:

```text
len(output) == len(scenes)
```

## `_find_best_scene(...) -> int | None`

Arguments:

```text
scenes
segment
```

Overlap formula:

```python
overlap_start = max(
    scene.start_seconds,
    segment.start_seconds,
)

overlap_end = min(
    scene.end_seconds,
    segment.end_seconds,
)

overlap = max(
    0.0,
    overlap_end - overlap_start,
)
```

Only the scene with strictly greater overlap replaces the current best.

## Tie behavior

Because the comparison is:

```python
if overlap > best_overlap
```

not `>=`, the first scene reaching the highest overlap wins a tie.

## Historical reason

This fixed transcript duplication across adjacent scenes.

---

# 65. `src/services/motion_analyzer.py`

## Class: `MotionAnalyzer`

Historical/current design:

```python
__init__(
    self,
    sample_interval_frames: int = 5,
)
```

## `sample_interval_frames`

How frequently a frame is analyzed.

Default:

```text
every 5 frames
```

At 30 FPS, this is roughly six sampled frames per second.

## Method

```python
analyze(
    self,
    video_file: str,
    scenes: list[Scene],
) -> list[MotionFeatures]
```

## Video opening

Uses:

```python
cv2.VideoCapture
```

## FPS

Reads:

```python
cv2.CAP_PROP_FPS
```

FPS <= 0 causes a runtime error.

## Per scene

Calls `_analyze_scene(...)`.

## `_analyze_scene`

Arguments:

```text
capture
fps
scene
```

Converts scene seconds into frame indexes:

```python
int(scene.start_seconds * fps)
int(scene.end_seconds * fps)
```

## Frame preprocessing

For sampled frames:

```python
cv2.cvtColor(
    frame,
    cv2.COLOR_BGR2GRAY,
)
```

Then:

```python
cv2.GaussianBlur(
    gray,
    (5, 5),
    0,
)
```

## Motion calculation

```python
cv2.absdiff(previous_gray, gray)
```

Then:

```python
float(np.mean(difference))
```

## Output

Average and maximum motion score per scene.

## Empty motion behavior

Returns zero scores when no frame comparisons were produced.

---

# 66. `src/services/audio_analyzer.py`

## Class: `AudioAnalyzer`

## Method

```python
analyze(
    self,
    audio_file: str,
    scenes: list[Scene],
) -> list[AudioFeatures]
```

## Audio loading

SoundFile float32.

Stereo is averaged to mono.

## Scene conversion

```python
start_sample = int(
    scene.start_seconds * sample_rate
)
```

Same for end.

## Empty scene audio

Returns:

```text
average_rms = 0.0
maximum_rms = 0.0
```

## `_calculate_rms(audio: np.ndarray) -> float`

Formula:

```python
sqrt(
    mean(
        square(audio)
    )
)
```

Uses float64 for squaring to reduce numeric issues.

## `_calculate_peak_rms(scene_audio, sample_rate) -> float`

Window size:

```python
int(sample_rate * 0.25)
```

Approximately 250 milliseconds.

Calculates RMS for every window and retains the maximum.

## Important semantic warning

This is not voice loudness.

It is mixed gameplay + commentary audio energy.

---

# 67. `src/services/highlight_feature_extractor.py`

## Class: `HighlightFeatureExtractor`

## Method

```python
extract(
    self,
    scene_analyses: list[SceneAnalysis],
    motion_features: list[MotionFeatures],
    audio_features: list[AudioFeatures],
) -> list[HighlightFeatures]
```

## Contract requirement

All three lists must correspond by position.

Example:

```text
index 0 = scene 1
index 1 = scene 2
...
```

## Count validation

If motion count differs:

```text
Scene analysis count does not match motion feature count.
```

If audio count differs:

```text
Scene analysis count does not match audio feature count.
```

## `zip(..., strict=True)`

Python checks that iterable lengths match.

This is an additional safety measure.

## Per scene fields

Creates:

```text
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

## `has_speech`

Calculated from:

```python
bool(transcript_text)
```

This means:

> recognized non-empty transcript exists.

It does not mean VAD necessarily detected no speech.

---

# 68. `src/services/highlight_scorer.py`

## Class: `HighlightScorer`

## Method

```python
score(
    self,
    features: list[HighlightFeatures],
) -> list[HighlightScore]
```

## Empty input

Returns:

```python
[]
```

## Maximum values

Finds:

```text
maximum average motion
maximum speech word count
maximum average audio RMS
```

These are maxima **inside the current video's feature list**.

## Normalization

```python
value / maximum
```

When maximum <= 0:

```text
0.0
```

## Score formula

```python
motion_score * 0.45
+ speech_score * 0.30
+ audio_score * 0.25
```

## Output sorting

Descending final score.

## Important technical consequence

Scores are relative to the current analyzed set.

A quiet video can still have a scene with motion score `1.0` because it is the most active scene in that quiet video.

This is useful but must be considered during cross-video tuning.

---

# 69. `src/services/highlight_selector.py`

## Class: `HighlightSelector`

## Constructor

```python
__init__(
    self,
    maximum_candidates: int = 5,
    minimum_score: float = 0.40,
    padding_before_seconds: float = 3.0,
    padding_after_seconds: float = 3.0,
) -> None
```

## Arguments

### `maximum_candidates`

Maximum eligible ranked scenes considered.

### `minimum_score`

Minimum `HighlightScore.final_score`.

### `padding_before_seconds`

Context added before scene.

### `padding_after_seconds`

Context added after scene.

## Method

```python
select(
    self,
    scores: list[HighlightScore],
    video_duration_seconds: float,
) -> list[HighlightCandidate]
```

## `scores`

Expected to already be in rank order.

The scorer returns descending order.

The selector itself does not sort.

## `video_duration_seconds`

Required for end-boundary clamping.

## Eligibility

```python
score.final_score >= minimum_score
```

## Candidate limit

```python
eligible_scores[:maximum_candidates]
```

## Rank assignment

Uses:

```python
enumerate(..., start=1)
```

Technical note:

This creates a new candidate rank after score filtering.

## Start clamp

```python
max(
    0.0,
    scene_start - padding_before,
)
```

## End clamp

```python
min(
    video_duration_seconds,
    scene_end + padding_after,
)
```

## Returns

`HighlightCandidate` objects.

---

# 70. `src/services/highlight_overlap_resolver.py`

## Class: `HighlightOverlapResolver`

## Constructor

```python
__init__(
    self,
    maximum_overlap_ratio: float = 0.50,
)
```

## Method

```python
resolve(
    self,
    candidates: list[HighlightCandidate],
) -> list[HighlightCandidate]
```

## Algorithm

Candidates are processed in input order.

For each candidate, compare it with already accepted candidates.

If **any** overlap ratio is greater than the configured maximum, reject the new candidate.

## Ordering is important

Higher-ranked candidates must arrive first.

The resolver does not sort.

## `_calculate_overlap_ratio(first, second)`

Overlap duration:

```python
max(
    0.0,
    min(end1, end2) - max(start1, start2)
)
```

Denominator:

```python
min(
    first.duration_seconds,
    second.duration_seconds,
)
```

Therefore ratio means:

> What fraction of the shorter candidate is covered by the overlap?

This is different from intersection-over-union.

## Zero duration

Returns `0.0`.

---

# 71. `src/services/highlight_clip_generator.py`

## Class: `HighlightClipGenerator`

## Method

```python
generate(
    self,
    video_file: str,
    candidates: list[HighlightCandidate],
    output_folder: str,
) -> list[GeneratedHighlight]
```

## Source validation

Requires source `is_file()`.

## Output cleanup

Deletes:

```text
highlight_*.mp4
```

from the supplied candidate clip folder.

## Per candidate output naming

```text
highlight_001.mp4
highlight_002.mp4
...
```

Important:

The numeric file name is enumeration order, not necessarily candidate rank.

The `GeneratedHighlight` retains the candidate and therefore retains the real rank.

## Duration

```python
candidate.end_seconds
- candidate.start_seconds
```

## FFmpeg input trimming

```python
ffmpeg.input(
    video_path,
    ss=candidate.start_seconds,
    t=duration_seconds,
)
```

## Streams

Explicitly passes:

```python
input_stream.video
input_stream.audio
```

## Encoding

```text
video = libx264
audio = aac
preset = fast
movflags = +faststart
```

## Returns

List of `GeneratedHighlight`.

---

# 72. `src/services/highlight_reasoner.py`

## Status

Production commentary AI reasoner in the completed pipeline.

## Purpose

Ask local Gemma to judge transcript/commentary context.

## Model

```text
gemma3:4b
```

## Historical executable behavior

The service had to use the actual Windows Ollama executable because `ollama` was not available on PATH on the development machine.

Known path from development:

```text
C:\Users\SunGupta\AppData\Local\Programs\Ollama\ollama.exe
```

## Expected main method

```python
reason(
    self,
    highlights: list[GeneratedHighlight],
) -> list[HighlightReasoning]
```

or equivalent per-highlight loop according to the verified local source.

## Important parser behavior

The working reasoner was repaired to handle:

- Markdown JSON fences
- ANSI terminal control sequences
- JSON between first `{` and final `}`
- malformed literal line breaks inside JSON strings
- parse failure fallback
- confidence normalization
- boolean normalization

## Maintenance requirement

Inspect the exact verified local file before changing this service because it contains hard-earned defensive parsing logic.

Do not replace parsing with only:

```python
json.loads(process.stdout)
```

---

# 73. `src/services/highlight_analysis_combiner.py`

## Class: `HighlightAnalysisCombiner`

## Method

```python
combine(
    self,
    highlights: list[GeneratedHighlight],
    reasoning_results: list[HighlightReasoning],
) -> list[AnalyzedHighlight]
```

## Matching key

`rank`.

Builds:

```python
reasoning_by_rank = {
    result.rank: result
    for result in reasoning_results
}
```

## Missing reasoning result

The highlight is skipped.

It does not create a blank reasoning object.

## Returns

`AnalyzedHighlight` wrappers.

## Technical risk

Duplicate reasoning ranks overwrite earlier dictionary values.

Rank uniqueness is assumed.

---

# 74. `src/services/highlight_frame_extractor.py`

## Class: `HighlightFrameExtractor`

## Constructor

```python
__init__(
    self,
    frame_count: int = 5,
    maximum_frame_width: int = 768,
) -> None
```

## Validation

Both values must be greater than zero.

## `frame_count`

Maximum number of representative frames.

## `maximum_frame_width`

Frames wider than this are resized down.

Aspect ratio is preserved.

## Method

```python
extract(
    self,
    highlight: GeneratedHighlight,
    output_folder: str,
) -> list[str]
```

## Output prefix

```text
highlight_<rank>_frame_
```

Example:

```text
highlight_001_frame_001.jpg
```

## Existing frame cleanup

Deletes only matching files for the current highlight rank.

## Video read

OpenCV `VideoCapture`.

## `total_frames`

Read using:

```python
CAP_PROP_FRAME_COUNT
```

If <= 0:

```python
[]
```

## `sample_count`

```python
min(
    configured frame_count,
    total_frames,
)
```

## `_calculate_frame_indexes`

For one frame:

middle frame.

For multiple:

evenly spaced between frame 0 and last frame.

Formula:

```python
round(
    index * last_frame_index
    / (sample_count - 1)
)
```

## `_resize_frame`

Only downscales when current width exceeds maximum.

New height:

```python
round(
    frame_height * scale
)
```

## JPEG quality

```text
85
```

## Returns

Paths only for frames successfully read and written.

---

# 75. `src/services/visual_highlight_reasoner.py`

## Class: `VisualHighlightReasoner`

## Constants

```text
MODEL_NAME = gemma3:4b
OLLAMA_API_URL = http://localhost:11434/api/generate
KEEP_ALIVE = 30m
```

## Why API instead of CLI

This service sends HTTP requests directly to the local Ollama server.

## `warm_up(self) -> None`

Sends:

```python
{
    "model": MODEL_NAME,
    "keep_alive": KEEP_ALIVE,
}
```

Purpose:

Load/keep the model available before candidate visual reasoning.

Historical optimization shows why this matters.

## `reason(highlight, frame_files) -> VisualReasoning`

### `highlight`

Generated highlight with rank, transcript, duration, and score.

### `frame_files`

Paths to representative JPEGs.

## Image encoding

Every frame is:

1. validated with `is_file()`;
2. read as bytes;
3. Base64 encoded;
4. converted to ASCII string.

## Ollama request

```text
model
prompt
images
stream = false
format = json
keep_alive = 30m
```

## `_send_request`

HTTP POST.

Timeout:

```text
300 seconds
```

### HTTP error

Raises runtime error including status code and response body.

### URL error

Raises connection runtime error.

## `_build_prompt`

Provides:

- channel context
- style
- rank
- duration
- heuristic score
- approximate transcript
- required visual focus
- exact JSON shape
- allowed level values

## `_parse_response`

Extracts content from first `{` to last `}`.

Returns `{}` on invalid JSON.

## `_normalize_level`

Allowed:

```text
low
medium
high
```

Anything else becomes:

```text
low
```

## `_normalize_boolean`

Handles real booleans and string `"true"`.

## `_normalize_confidence`

Converts to float and clamps:

```text
0.0 to 1.0
```

---

# 76. `src/services/highlight_fusion_reasoner.py`

## Class: `HighlightFusionReasoner`

## Purpose

Combine commentary AI and visual AI.

## Constants

```text
MODEL_NAME = gemma3:4b
OLLAMA_API_URL = http://localhost:11434/api/generate
```

## Method

```python
reason(
    self,
    analyzed_highlight: AnalyzedHighlight,
    visual_reasoning: VisualReasoning,
) -> HighlightFusion
```

## Input relationship

These two objects must refer to the same highlight rank.

The method does not visibly reject rank mismatch.

A future validation could make this explicit.

## Ollama request

```text
stream = false
format = json
timeout = 300 seconds
```

## Prompt inputs

Commentary:

```text
interesting
category
confidence
reason
transcript
```

Visual:

```text
visual event
action level
danger level
looks interesting
visual confidence
visual reason
```

Heuristic:

```text
final score
```

## Allowed final categories

```text
funny
rage
reaction
combat
boss_fight
fail
success
story
unexpected
unknown
```

## Output fields

`HighlightFusion` is created with:

```text
rank
keep_highlight
category
event_summary
commentary_category
visual_event
action_level
danger_level
final_confidence
reason
```

## Important detail

`commentary_category`, `visual_event`, `action_level`, and `danger_level` are copied from existing structured analysis.

The AI response controls:

```text
keep_highlight
category
event_summary
final_confidence
reason
```

## Parser

Same first-`{` / last-`}` defensive approach.

## Confidence

Clamped to `[0, 1]`.

---

# 77. `src/services/final_highlight_selector.py`

## Constructor

```python
__init__(
    self,
    minimum_confidence: float = 0.70,
)
```

## Validation

Must be:

```text
0.0 <= value <= 1.0
```

## Method

```python
select(
    self,
    fusion_results: list[HighlightFusion],
) -> list[HighlightFusion]
```

## Selection conditions

Both:

```python
result.keep_highlight
```

and:

```python
result.final_confidence
>= minimum_confidence
```

## Sorting

Primary:

descending confidence.

Secondary:

ascending rank.

Key:

```python
(
    -result.final_confidence,
    result.rank,
)
```

---

# 78. `src/services/final_highlight_combiner.py`

## Class: `FinalHighlightCombiner`

## Method

```python
combine(
    self,
    highlights: list[GeneratedHighlight],
    approved_results: list[HighlightFusion],
) -> list[FinalHighlight]
```

## Matching

Creates a rank dictionary of generated media.

For every approved fusion result:

```python
highlight = highlights_by_rank.get(
    result.rank
)
```

## Missing clip

The approved result is skipped.

## Returns

`FinalHighlight` objects.

## Important design concept

AI approval and media generation are separate.

This service reconnects the final decision to the actual MP4.

---

# 79. `src/services/final_highlight_exporter.py`

## Class: `FinalHighlightExporter`

## Method

```python
export(
    self,
    highlights: list[FinalHighlight],
    output_folder: str,
) -> list[str]
```

## Creates

```text
<output>/clips
<output>/metadata
```

## Cleanup

Deletes:

```text
clips/highlight_*.mp4
metadata/highlight_*.json
```

## Output numbering

Enumeration starts at one.

Important:

Export filename number is output order, not necessarily original rank.

Rank remains in JSON.

## Clip copy

Uses:

```python
shutil.copy2
```

This preserves file metadata better than basic copy.

## JSON metadata fields

```text
rank
source_start_seconds
source_end_seconds
duration_seconds
heuristic_score
category
event_summary
commentary_category
visual_event
action_level
danger_level
confidence
transcript
reason
clip_file
```

## Unicode

```python
ensure_ascii=False
```

This preserves Hindi text rather than escaping every Unicode code point.

## Returns

List of exported MP4 paths.

It does not return JSON paths.

---

# 80. `src/services/caption_segment_builder.py`

## Class: `CaptionSegmentBuilder`

## Constructor

```python
__init__(
    self,
    maximum_words_per_caption: int = 4,
) -> None
```

## Validation

Must be greater than zero.

## Method

```python
build(
    self,
    highlight: FinalHighlight,
) -> list[CaptionSegment]
```

## Transcript source

```python
highlight.transcript_text.strip()
```

## Empty transcript

Returns:

```python
[]
```

## Word grouping

Splits on whitespace.

Groups at most four words by default.

Example:

```text
one two three four
five six seven
```

## Timing strategy

All caption groups receive equal-duration portions of the final highlight.

```python
highlight.duration_seconds
/
caption_count
```

## Last caption

Forced to end exactly at:

```python
highlight.duration_seconds
```

This prevents floating rounding from leaving a small gap past/before the end.

## Important limitation

This is not word-level ASR synchronization.

Caption timing is evenly distributed.

Future word-timestamp ASR work would require redesigning this service.

---

# 81. `src/services/srt_writer.py`

## Class: `SRTWriter`

## Method

```python
write(
    self,
    captions: list[CaptionSegment],
    output_file: str,
) -> str
```

## Output folder

Created automatically.

## SRT block format

```text
1
00:00:00,000 --> 00:00:02,790
caption text
```

## Caption numbering

Starts at one.

## Empty captions

Writes an empty file.

This is important because `ShortPackageBuilder` still passes the subtitle file to `CaptionRenderer`.

A maintainer should test what FFmpeg subtitles filter does with an empty SRT in all environments.

## `_format_timestamp(seconds: float) -> str`

### Negative value handling

```python
max(0, round(seconds * 1000))
```

Negative time becomes zero.

### Format

```text
HH:MM:SS,mmm
```

Uses comma before milliseconds as required by SRT convention.

---

# 82. `src/services/short_renderer.py`

## Class: `ShortRenderer`

## Constants

```text
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
```

## Method

```python
render(
    self,
    highlight: FinalHighlight,
    output_folder: str,
) -> RenderedShort
```

## Source

```python
highlight.file_path
```

## Output

```text
short_<rank>.mp4
```

## Actual current public FFmpeg filter

```text
scale=1080:1920:force_original_aspect_ratio=increase,
crop=1080:1920
```

## Extremely important technical correction

The current public implementation is a **scale-and-center-crop portrait conversion**.

This file does **not** contain face detection, face tracking, object tracking, or dynamic crop-center movement.

The top-level README currently advertises:

```text
Face tracking
Auto 9:16 reframing
```

but the public `ShortRenderer` source shown on `main` performs static center crop.

A maintainer must not assume intelligent tracking exists in this file.

Possible explanations that must be audited:

1. tracking code exists only in the local untracked build;
2. README feature wording is ahead of implementation;
3. tracking was planned but not integrated.

## Encoding

```text
libx264
preset=medium
crf=18
AAC
192k audio
+faststart
```

## Failure handling

Checks FFmpeg return code.

Raises full stderr in runtime error.

Then verifies output file exists.

## Returns

`RenderedShort`.

---

# 83. `src/services/caption_renderer.py`

## Class: `CaptionRenderer`

## Method

```python
render(
    self,
    video_file: str,
    subtitle_file: str,
    output_file: str,
) -> str
```

## Validates

- video exists
- SRT exists

## Windows subtitle path escaping

Path is converted:

```text
\ → /
```

Then escapes:

```text
: → \:
' → \'
```

This is required because FFmpeg filter syntax interprets these characters.

## Subtitle filter

Current style:

```text
Alignment=2
FontSize=18
Bold=1
Outline=3
Shadow=1
MarginV=220
```

### `Alignment=2`

ASS/SSA-style bottom-center alignment.

### `MarginV=220`

Moves subtitles upward from the bottom.

## Encoding

Video is re-encoded:

```text
libx264
preset=medium
crf=18
```

Audio:

```text
copy
```

The already-rendered Short audio is copied without another audio re-encode.

## Output validation

Checks return code and file existence.

---

# 84. `src/services/ai_text_cleaner.py`

## Class: `AITextCleaner`

Purpose:

Remove cosmetic repeated fragments produced by local AI.

## Regex: `REPEATED_WORD_PATTERN`

Detects adjacent repeated words.

Example:

```text
rage rage
```

becomes:

```text
rage
```

## `REPEATED_PHRASE_PATTERN`

Attempts to detect a repeated phrase of roughly 3–40 characters.

## `DUPLICATED_QUOTE_PATTERN`

Targets duplicated quoted text.

## Method

```python
clean(
    self,
    text: str,
) -> str
```

## Repeated cleaning loop

The cleaner repeats until the text stops changing:

```python
while cleaned != previous
```

This is important because removing one duplicate can expose another duplicate.

## `_remove_partial_word_duplicates`

Example historical artifacts:

```text
pu pulsating
bl black
expres expression
```

The method compares the previous cleaned word and current word.

If the current word is longer and starts with the previous word, it replaces the previous word.

Example:

```text
expres expression
```

becomes:

```text
expression
```

## `_word_core`

Removes leading/trailing non-word characters for comparison.

## Risk

Aggressive text cleanup can alter legitimate repetition.

Examples:

```text
no no no!
go go go!
```

This project currently values cleaning AI metadata more than preserving rhetorical repetition.

Do not automatically reuse this cleaner for user speech captions.

---

# 85. `src/services/short_metadata_generator.py`

## Class: `ShortMetadataGenerator`

## Constants

### `MODEL_NAME`

```text
gemma3:4b
```

### `OLLAMA_EXECUTABLE`

Current public code hard-codes:

```text
C:\Users\SunGupta\AppData\Local\Programs\Ollama\ollama.exe
```

## Critical portability warning

This path is machine/user specific.

A fresh installation under another Windows username can fail.

This is one of the most important installation issues in the current source.

A future fix should discover Ollama using:

1. configured path;
2. `shutil.which("ollama")`;
3. known Windows installation locations;
4. clear error message.

Do not silently assume Sunny's Windows profile path.

### `ANSI_ESCAPE_PATTERN`

Removes terminal escape codes.

### `DISALLOWED_SCRIPT_PATTERN`

Rejects Unicode ranges for:

- Tamil
- Telugu
- Kannada
- Malayalam

### `MAXIMUM_ATTEMPTS`

```text
3
```

## Constructor

Creates:

```python
AITextCleaner()
```

## `generate(highlight) -> ShortMetadata`

For attempts one through three:

1. build prompt;
2. run Ollama CLI;
3. parse output;
4. build metadata;
5. validate;
6. return first valid result.

If all attempts fail:

```python
_build_fallback_metadata(highlight)
```

## Ollama CLI call

```python
[
    OLLAMA_EXECUTABLE,
    "run",
    MODEL_NAME,
]
```

Prompt is sent through subprocess stdin.

## Encoding

```text
utf-8
errors=replace
```

## `check=True`

A non-zero Ollama process exit raises `CalledProcessError`.

## `_build_metadata`

Hashtags must be a list.

Anything else becomes an empty list.

Every string is passed through `AITextCleaner`.

## `_is_valid`

Requires non-empty:

```text
hook
title
description
thumbnail_prompt
```

Requires hashtags.

Requires title <= 70 characters.

Every hashtag must begin with `#`.

Rejects configured disallowed scripts from combined text.

## Important gap

Current script validation does not inspect hashtag text in the combined disallowed-script check.

It only combines hook/title/description/thumbnail prompt.

A future hardening change may include hashtags.

## `_build_fallback_metadata`

Creates deterministic category-based fallback.

Special categories:

```text
rage
reaction
combat
```

Other values use general gaming fallback.

## `_build_prompt`

Arguments:

```text
highlight
attempt
```

On retry (`attempt > 1`), adds explicit invalid-response warning.

The prompt tells the model:

- channel identity
- content style
- event fields
- transcript may be wrong
- allowed languages/scripts
- field rules
- exact JSON shape

## `_parse_response`

1. remove ANSI;
2. find first `{`;
3. find last `}`;
4. repair raw newlines inside JSON strings;
5. `json.loads`;
6. require dictionary.

## `_repair_json_newlines`

Tracks:

```text
inside_string
escaped
```

Literal CR/LF inside a JSON string becomes a space.

This is a specific repair for imperfect local model output.

---

# 86. `src/services/short_package_builder.py`

## Class: `ShortPackageBuilder`

Purpose:

Build everything for one approved highlight.

## Constructor

Creates five concrete dependencies:

```text
ShortRenderer
CaptionSegmentBuilder
SRTWriter
CaptionRenderer
ShortMetadataGenerator
```

## Dependency-injection observation

Unlike `ShortBatchRenderer` and `ShortPackageBatchBuilder`, this constructor does not accept replacements.

Testing this class may require monkeypatching or real services.

A future refactor could allow optional injected dependencies.

## Method

```python
build(
    self,
    highlight: FinalHighlight,
    output_folder: str,
) -> ShortPackage
```

## Short folder

```text
<output>/short_<rank>
```

## Exact sequence

### 1. Render portrait Short

```python
short_renderer.render(...)
```

### 2. Build caption segments

```python
caption_builder.build(highlight)
```

### 3. Write SRT

```python
srt_writer.write(...)
```

Output:

```text
captions.srt
```

### 4. Burn captions

```python
caption_renderer.render(...)
```

Output:

```text
final_short.mp4
```

### 5. Generate publishing metadata

```python
metadata_generator.generate(highlight)
```

### 6. Return `ShortPackage`

Includes:

```text
rendered_short
final_video_file
subtitle_file
metadata
```

## Performance note

The final production timing showed this entire package stage was the largest single stage in the small fixture.

It contains multiple encodes and AI metadata generation.

---

# 87. `src/services/short_package_batch_builder.py`

## Class: `ShortPackageBatchBuilder`

## Constructor

```python
__init__(
    self,
    builder: ShortPackageBuilder | None = None,
) -> None
```

## `builder`

Optional dependency injection.

If `None`:

```python
ShortPackageBuilder()
```

## Method

```python
build(
    self,
    highlights: list[FinalHighlight],
    output_folder: str,
) -> list[ShortPackage]
```

Loops in input order.

No parallelism.

No exception isolation.

If one Short build raises, the batch call stops.

---

# 88. `src/services/short_batch_renderer.py`

## Class: `ShortBatchRenderer`

Purpose:

Render approved highlights to portrait video only.

This is narrower than `ShortPackageBatchBuilder`.

## Constructor

Optional `ShortRenderer`.

## `render(...)`

Arguments:

```text
highlights
output_folder
```

Returns:

```text
list[RenderedShort]
```

## Architectural note

The final package pipeline uses `ShortPackageBuilder`, which itself renders.

Audit whether `ShortBatchRenderer` is still used in the final production path or primarily retained for component verification.

---

# 89. `src/services/pipeline_run_path_builder.py`

## Purpose

Create unique paths for one CLI run.

Known output model:

```python
PipelineRunPaths
```

Expected method:

```python
build(
    self,
    video_file: str,
) -> PipelineRunPaths
```

## Known final run ID example

```text
20260715_205234_1_9b640c0c
```

The format demonstrates a design involving:

- timestamp
- source/video component
- random/unique suffix

## Expected output relationship

```text
output/runs/<run_id>
```

and a unique working path.

## Change rule

Run IDs must be filesystem-safe on Windows.

Do not use `:` in timestamps.

---

# 90. `src/services/pipeline_progress_reporter.py`

## Purpose

Convert stage execution into `PipelineProgress` callback events.

Expected callback contract:

```python
Callable[[PipelineProgress], None]
```

The CLI supplies:

```python
print_progress
```

## Progress object fields

```text
step
total_steps
message
```

## Maintenance requirement

A GUI may later pass a different callback.

Therefore the pipeline should not assume progress always means `print()`.

---

# 91. `src/services/pipeline_stage_runner.py`

## Purpose

Execute one named stage, measure time, report progress, and wrap failures.

Expected core responsibilities:

1. progress notification;
2. start high-resolution/performance timer;
3. call provided stage function;
4. create `PipelineStageTiming`;
5. wrap exceptions in `PipelineExecutionError`.

## Why a stage runner exists

Without it, every pipeline step would repeat:

```python
try:
    start = ...
    result = ...
    timings.append(...)
except Exception as error:
    raise PipelineExecutionError(...)
```

## Change impact

This is cross-cutting infrastructure.

A bug can affect every stage and CLI error reporting.

---

# 92. `src/services/highlight_pipeline.py` — REAL PRODUCTION ORCHESTRATOR

## Status

This is the key application pipeline used by `src/cli.py`.

## Class: `HighlightPipeline`

## Public method

```python
run(
    self,
    video_file: str,
    working_folder: str,
    output_folder: str,
    progress_callback=...,
) -> PipelineResult
```

The exact callback annotation must be confirmed from the local tracked source.

## High-level stage order from the accepted final run

1. Loading video
2. Extracting audio
3. Detecting speech
4. Creating speech chunks
5. Transcribing commentary
6. Detecting scenes
7. Mapping commentary to scenes
8. Analyzing motion
9. Analyzing audio intensity
10. Extracting highlight features
11. Scoring highlight scenes
12. Selecting highlight candidates
13. Resolving highlight overlaps
14. Generating highlight clips
15. Running commentary AI reasoning
16. Combining commentary analysis
17. Extracting representative frames for each candidate
18. Warming up visual AI model
19. Running visual AI reasoning per candidate
20. Fusing multimodal AI decisions per candidate
21. Selecting final approved highlights
22. Linking approved decisions to clips
23. Exporting final highlight package
24. Building final YouTube Short packages

The timing output displays some candidate-specific stages separately.

## `video_file`

Original gaming video.

## `working_folder`

Intermediate artifacts:

- analysis audio
- speech chunks
- candidate clips
- representative frames

Exact subfolder names must be read from the local implementation.

## `output_folder`

Final exported highlight and Short package destination.

## `progress_callback`

Allows the caller to observe stage progress.

## Expected result

`PipelineResult`.

## Maintainer rule

When adding a new expensive stage:

1. give it a clear human-readable stage name;
2. execute it through timing/progress infrastructure;
3. decide where its intermediate files belong;
4. add result data to a model instead of relying only on globals;
5. update pipeline verification;
6. update this manual.

---

# 93. CONFIGURATION FILE TECHNICAL REFERENCE

## `config/config.yaml`

Current public values include:

```yaml
application:
  name: PressStartAI
  version: 0.1.0
  debug: true

processing:
  device: AUTO
  output_resolution: "1080x1920"
  temp_directory: temp
  output_directory: output

video:
  target_fps: 30
  codec: libx264
  bitrate: 8M

ai:
  whisper_model: medium
  vision_model: qwen2.5-vl
  llm_model: gemma3
```

## Critical configuration drift warning

The current production services directly use:

```text
Qwen/Qwen3-ASR-0.6B
gemma3:4b
```

The config still contains:

```text
whisper_model: medium
vision_model: qwen2.5-vl
llm_model: gemma3
```

The public source inspected does not show the main production AI services reading these values.

Therefore `config.yaml` is partly stale or disconnected from actual production service constants.

A maintainer must not assume editing `ai.vision_model` changes the visual model.

## Recommended cleanup

Choose one source of truth:

### Configuration-driven

Inject model names into services.

or

### Code constants

Remove misleading unused config values.

Do not maintain conflicting settings.

---

## `config/logging.yaml`

### `version: 1`

Python logging dictionary schema version.

## Formatter

```text
%(asctime)s
%(levelname)s
%(name)s
%(message)s
```

## Console handler

Class:

```text
logging.StreamHandler
```

Level:

```text
INFO
```

## File handler

Class:

```text
logging.FileHandler
```

File:

```text
logs/pressstartai.log
```

Level:

```text
DEBUG
```

## Root logger

Level:

```text
INFO
```

Handlers:

```text
console
file
```

---

# 94. `.gitignore` — TECHNICAL AND REPOSITORY-INTEGRITY REFERENCE

Current categories:

```text
Python caches
virtual environment
logs
output
temp
AI models
VS Code
pytest
coverage
build
OS files
diagnostics
egg-info
```

## Critical pattern

```gitignore
models/
```

## Why this matters

Current production services import many modules under:

```text
src.models
```

but public GitHub currently shows only:

```text
pipeline_run_paths.py
pipeline_stage_timing.py
```

The broad `models/` rule is a likely reason untracked/new files under `src/models` were never added.

## Required repository audit commands

On the local verified machine:

```bat
git status --ignored
git check-ignore -v src\models\final_highlight.py
git check-ignore -v src\models\highlight_candidate.py
git check-ignore -v src\models\short_package.py
git ls-files src/models
dir src\models
```

## Do not rebuild missing models first

The local computer may still contain the complete files.

Fix tracking from the verified local files whenever possible.

Recreating from documentation should be the last recovery path.

---

# 95. `pyproject.toml`

## Project metadata

```text
name = pressstartai
version = 0.1.0
description = Local AI powered gaming video to YouTube Shorts generator
```

## Python constraint

```text
>=3.12,<3.13
```

## Author

```text
Sunny Gupta
```

## Black

```text
line length = 100
```

## Ruff

```text
line length = 100
```

## Pytest

```text
testpaths = ["tests"]
```

## Technical observation

The public repository does not currently advertise a formal `tests` folder in its top-level tree.

Most verification is under `tools`.

Therefore pytest configuration and actual verification strategy are not fully aligned.

---

# 96. VERIFICATION AND BENCHMARK SCRIPT CATALOG

The `tools` folder is source code too.

These files are generally executable development scripts, not production imports.

Many historically add the repository root to `sys.path` so `src` imports work.

## General rule for every `verify_*.py`

A verification script should answer one narrow question.

It is not a replacement for the production CLI.

Do not copy fixture paths or synthetic values from a verification script into a production service.

## `tools/benchmark_openvino.py`

Purpose:

Measure/inspect OpenVINO device behavior and performance.

Use when changing:

- OpenVINO version
- device routing
- CPU/GPU/NPU strategy

## `tools/benchmark_visual_reasoner.py`

Purpose:

Measure visual AI reasoning time.

Historical importance:

Visual reasoning was once approximately 100 seconds per candidate.

Use after changing:

- number of frames
- frame resolution
- Ollama model
- keep-alive
- visual prompt

## `tools/verify_audio_analyzer.py`

Verifies:

- scene audio slicing
- average RMS
- peak RMS

## `tools/verify_audio_extractor.py`

Verifies FFmpeg audio extraction.

Expected analysis output:

- mono
- 16 kHz by default
- WAV/PCM path

## `tools/verify_caption_renderer.py`

Verifies:

- FFmpeg subtitles filter
- Windows subtitle path escaping
- caption burn-in
- captioned video creation

## `tools/verify_caption_segment_builder.py`

Verifies transcript word grouping and equal-duration caption timing.

Historical verified output split a transcript into four-word groups.

## `tools/verify_final_highlight_combiner.py`

Verifies matching approved fusion decisions to generated clips by rank.

## `tools/verify_final_highlight_exporter.py`

Verifies clip copy and metadata JSON export.

## `tools/verify_final_highlight_selector.py`

Uses synthetic fusion results to confirm:

- `keep_highlight=False` rejects
- low confidence rejects
- final sorting works

## `tools/verify_full_highlight_pipeline.py`

Historical full integration verification.

Use for pipeline integration.

Confirm whether it reflects the latest Short package stages or an earlier pipeline milestone.

## `tools/verify_funasr_hindi.py`

Historical experiment.

FunASR returned Chinese for Hindi commentary.

Do not treat a passing import as production approval.

## `tools/verify_highlight_analysis_combiner.py`

Checks rank-based combination of generated clips and commentary reasoning.

## `tools/verify_highlight_candidates.py`

Historically verifies end-to-end low-cost analysis through:

- scenes
- transcript
- motion
- audio
- scoring
- candidate selection
- overlap resolution

Important historical bug:

It once imported nonexistent `src.services.vad`.

Correct service:

```text
src.services.voice_activity_detector
```

## `tools/verify_highlight_clip_generator.py`

Checks candidate MP4 generation and metadata.

Historical playback investigation confirmed clips contained AAC audio.

## `tools/verify_highlight_features.py`

Checks combined scene feature creation.

## `tools/verify_highlight_frame_extractor.py`

Checks representative JPEG extraction and file generation.

## `tools/verify_highlight_fusion_reasoner.py`

Checks final local AI multimodal decision.

Requires Ollama and `gemma3:4b`.

## `tools/verify_highlight_overlap_resolver.py`

Checks overlap ratio and rejection behavior.

## `tools/verify_highlight_pipeline.py`

Pipeline integration verification.

Compare it with `verify_full_highlight_pipeline.py`; both reflect milestones and may not test identical final scope.

## `tools/verify_highlight_reasoner.py`

Checks commentary AI reasoning and parser behavior.

Requires local Ollama.

## `tools/verify_highlight_scorer.py`

Verifies normalization and 45/30/25 heuristic ranking.

## `tools/verify_highlight_selector.py`

Checks score threshold, candidate limit, padding, and boundary clamping.

## `tools/verify_hindi_whisper.py`

Historical rejected Whisper experiment.

## `tools/verify_motion_analyzer.py`

Checks OpenCV motion features.

## `tools/verify_openvino.py`

Checks available OpenVINO devices.

On original hardware, CPU/GPU/NPU visibility was verified.

## `tools/verify_pipeline_run_path_builder.py`

Checks unique run path generation.

## `tools/verify_pipeline_stage_runner.py`

Checks:

- stage function execution
- timing
- progress
- stage-aware error wrapping

## `tools/verify_qwen_all_chunks.py`

Runs Qwen ASR on all exported speech chunks.

Historical value:

Exposed random language detection on tiny chunks and showed improvement after merge logic.

## `tools/verify_qwen_asr.py`

Direct Qwen model experiment.

## `tools/verify_qwen_asr_service.py`

Checks `QwenASR` service wrapper and `ASRResult`.

## `tools/verify_scene_detector.py`

Checks scene detection and short-scene merge.

## `tools/verify_scene_transcript_mapper.py`

Checks maximum-overlap transcript assignment.

## `tools/verify_short_batch_renderer.py`

Checks rendering multiple approved highlights.

Audit whether this is still part of final package flow or mainly component verification.

## `tools/verify_short_metadata_generator.py`

Checks:

- Ollama metadata generation
- field population
- JSON parsing
- AI text cleanup
- script validation
- fallback behavior

## `tools/verify_short_package_builder.py`

Checks one complete package:

```text
portrait video
captions.srt
captioned final video
publishing metadata
```

## `tools/verify_short_renderer.py`

Checks current static 1080x1920 center-crop renderer.

## `tools/verify_speech_chunks.py`

Checks VAD segment merging and exported speech WAV timestamps.

## `tools/verify_srt_writer.py`

Checks SRT numbering and timestamp formatting.

## `tools/verify_transcript.py`

Historical transcript verification.

Identify whether it exercises Whisper branch or another transcript component before using its result as a production ASR test.

## `tools/verify_transcript_engine.py`

Historical `TranscriptEngine`/Whisper test.

## `tools/verify_transcription_pipeline.py`

Checks Qwen speech chunks to source-timeline `ASRSegment` objects.

## `tools/verify_vad.py`

Checks Silero VAD detection.

Listen to resulting chunks when diagnosing false speech detection.

## `tools/verify_video_loader.py`

Checks FFprobe-based `VideoInfo`.

## `tools/verify_visual_highlight_reasoner.py`

Checks production visual reasoner object and Ollama request path.

## `tools/verify_visual_reasoning.py`

Historical/direct visual reasoning experiment.

May differ from production service verification.

## `tools/verify_whisper.py`

Earliest Whisper experiment.

Historical only.

---

# 97. TECHNICAL CALL GRAPH

This is the most important relationship map for maintainers.

```text
src.cli.main
│
├── parse_arguments
├── PipelineRunPathBuilder.build
└── HighlightPipeline.run
    │
    ├── VideoLoader.load
    │   └── VideoInfo
    │
    ├── AudioExtractor.extract
    │
    ├── VoiceActivityDetector.detect
    │   └── list[{start, end}]
    │
    ├── SpeechChunkExtractor.extract
    │   └── list[SpeechChunk]
    │
    ├── TranscriptionPipeline.transcribe
    │   ├── QwenASR.transcribe
    │   │   └── ASRResult
    │   └── list[ASRSegment]
    │
    ├── SceneDetector.detect
    │   └── list[Scene]
    │
    ├── SceneTranscriptMapper.map
    │   └── list[SceneAnalysis]
    │
    ├── MotionAnalyzer.analyze
    │   └── list[MotionFeatures]
    │
    ├── AudioAnalyzer.analyze
    │   └── list[AudioFeatures]
    │
    ├── HighlightFeatureExtractor.extract
    │   └── list[HighlightFeatures]
    │
    ├── HighlightScorer.score
    │   └── list[HighlightScore]
    │
    ├── HighlightSelector.select
    │   └── list[HighlightCandidate]
    │
    ├── HighlightOverlapResolver.resolve
    │   └── list[HighlightCandidate]
    │
    ├── HighlightClipGenerator.generate
    │   └── list[GeneratedHighlight]
    │
    ├── HighlightReasoner
    │   └── list[HighlightReasoning]
    │
    ├── HighlightAnalysisCombiner.combine
    │   └── list[AnalyzedHighlight]
    │
    ├── HighlightFrameExtractor.extract
    │   └── list[str frame paths]
    │
    ├── VisualHighlightReasoner.warm_up
    │
    ├── VisualHighlightReasoner.reason
    │   └── VisualReasoning
    │
    ├── HighlightFusionReasoner.reason
    │   └── HighlightFusion
    │
    ├── FinalHighlightSelector.select
    │   └── approved HighlightFusion
    │
    ├── FinalHighlightCombiner.combine
    │   └── list[FinalHighlight]
    │
    ├── FinalHighlightExporter.export
    │   └── exported clip paths
    │
    └── ShortPackageBatchBuilder.build
        │
        └── ShortPackageBuilder.build
            ├── ShortRenderer.render
            │   └── RenderedShort
            ├── CaptionSegmentBuilder.build
            │   └── list[CaptionSegment]
            ├── SRTWriter.write
            │   └── captions.srt
            ├── CaptionRenderer.render
            │   └── final_short.mp4
            └── ShortMetadataGenerator.generate
                └── ShortMetadata
```

---

# 98. TECHNICAL DATA FLOW BY TIMELINE TYPE

PressStartAI contains several time coordinate systems.

Confusing them causes serious bugs.

## 98.1 Source-video timeline

Examples:

```text
18.00s → 29.17s
```

Used by:

- Scene
- ASRSegment
- HighlightCandidate
- FinalHighlight source start/end

## 98.2 Speech WAV local timeline

An exported speech WAV begins at its own zero.

Qwen transcribes the WAV.

The `SpeechChunk` stores original source start/end so the transcription pipeline can restore source time.

## 98.3 Generated candidate clip timeline

The clip starts at zero internally.

Its metadata still remembers source start/end.

## 98.4 Final Short timeline

Captions use zero-based time relative to the final Short.

The current `CaptionSegmentBuilder` does not use original ASR word timestamps.

It spreads transcript groups evenly across `highlight.duration_seconds`.

## Maintenance rule

Every timestamp field should be documented as one of:

```text
source-relative
chunk-relative
candidate-relative
short-relative
```

Do not use a generic field named `start` in new cross-stage models without timeline documentation.

---

# 99. TECHNICAL PORTABILITY DEFECTS CURRENTLY VISIBLE

These are not theoretical issues.

They are directly visible in the current public source/config.

## 99.1 Missing tracked model modules

Cause likely related to `models/` ignore pattern.

Effect:

Fresh clone can fail imports.

## 99.2 Hard-coded Ollama executable

`ShortMetadataGenerator` uses Sunny's Windows profile path.

Effect:

Different username/install location can fail.

## 99.3 Stale/disconnected AI config

`config.yaml` names Whisper and Qwen2.5-VL, while production services use Qwen3 ASR and Gemma 3 vision.

Effect:

Maintainer may edit config and see no behavior change.

## 99.4 Two application paths

`main.py` → stub `Pipeline`.

`python -m src.cli` → real `HighlightPipeline`.

Effect:

New contributor can change wrong pipeline.

## 99.5 README feature mismatch

Public README says face tracking.

Current public `ShortRenderer` performs static center crop.

Effect:

A maintainer/user may assume dynamic tracking exists.

## 99.6 Requirements contain rejected experiments

Effect:

Fresh environment is larger and more fragile than necessary.

## 99.7 Formal tests and actual verification differ

`pyproject.toml` points pytest to `tests`.

Most real checks are scripts in `tools`.

---

# 100. HOW TO DOCUMENT A NEW FILE IN THIS MANUAL

Whenever a new production code file is added, append documentation containing:

## File path

Example:

```text
src/services/game_identity_detector.py
```

## Production status

Choose:

```text
production
experimental
legacy
verification-only
benchmark
```

## Responsibility

One sentence.

## Imports

Only important architectural imports.

## Classes

For every class:

- class purpose
- constructor
- constructor arguments
- attributes created

## Methods/functions

For every callable:

```text
signature
each argument
default value
accepted range
return value
raised exceptions
side effects
files created/deleted
external programs/models called
caller
downstream consumer
```

## Algorithm

Explain calculation in plain English and formula where useful.

## Change impact

List downstream stages.

## Verification

Name the exact test/tool.

## Known limitations

Do not hide them.

---

# 101. MAINTAINER SOURCE-CODE AUDIT CHECKLIST

Before changing any source file:

```text
[ ] I know whether this file is production, legacy, or experimental.
[ ] I know which entry path calls it.
[ ] I read every class/function in the file.
[ ] I understand every argument.
[ ] I know the return object.
[ ] I found every repository import of the class/function.
[ ] I found every constructor call for affected models.
[ ] I know the timeline coordinate system used.
[ ] I know whether files are created or deleted.
[ ] I know whether FFmpeg/OpenCV/Ollama/Qwen/Silero is called.
[ ] I know whether the stage is performance-sensitive.
[ ] I identified a focused verification script.
[ ] I know whether full CLI verification is required.
[ ] I checked current Git status.
[ ] I checked whether the file is actually tracked by Git.
```

---

# 102. REPOSITORY RECOVERY PRIORITY FOR A FRESH MAINTAINER

Because the current public repository appears incomplete, use this order before feature development.

## Priority 1 — compare public and local source inventory

On Sunny's verified local machine:

```bat
cd /d "C:\AI Projects\PressStartAI"
dir /s /b src\*.py > local_python_files.txt
git ls-files > tracked_files.txt
git status --ignored
```

## Priority 2 — inspect model ignore behavior

```bat
git check-ignore -v src\models\asr_segment.py
git check-ignore -v src\models\final_highlight.py
git check-ignore -v src\models\short_package.py
```

## Priority 3 — preserve local working files

Do not delete the local directory.

Create a backup before Git cleanup.

## Priority 4 — correct `.gitignore`

Only after confirming cause.

## Priority 5 — add missing source files

Use the verified local files.

## Priority 6 — fresh-clone test

Clone to a different folder.

Create new venv.

Install requirements.

Run import verification.

## Priority 7 — run production CLI

Only after fresh clone imports pass.

## Priority 8 — continue new feature development

A public repository that cannot reproduce the local working build is a higher-priority maintenance problem than adding a UI.

---

# 103. FINAL TECHNICAL MANUAL NOTE

The plain-English first half of this document remains intentionally preserved.

This technical half adds the maintainer-level detail that was missing.

The most important factual distinction discovered during this documentation pass is:

> **The final development handoff records a working, complete local core pipeline, but the current public `main` branch visibly imports many `src.models` modules that are not present in the public `src/models` directory.**

That issue must be resolved before the public repository can honestly be treated as a clean, reproducible installation source.

Until then:

- use the verified local working directory as the code authority for missing model files;
- use this manual to understand the intended contracts;
- use Git history and `git check-ignore` to recover tracking;
- do not invent production model code from scratch unless the local working source is truly lost.

**End of deep technical source-code reference.**
