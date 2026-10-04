from __future__ import annotations

import argparse
import json
import shutil

from src.gameplay_segmentation.pipeline import GameplaySegmentationPipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PressStartAI standalone gameplay semantic clip segmentation."
    )
    parser.add_argument("video", nargs="?", help="Input gameplay MP4.")
    parser.add_argument("--output", default="output/gameplay_segments")
    parser.add_argument("--shared-analysis", default=None,
                        help="Optional PressStartAI shared-analysis JSON artifact.")
    parser.add_argument("--vision-model", default="gemma3:4b")
    parser.add_argument("--scan-interval", type=float, default=2.0)
    parser.add_argument("--analysis-window", type=float, default=10.0)
    parser.add_argument("--analysis-stride", type=float, default=8.0)
    parser.add_argument("--frame-interval", type=float, default=2.0)
    parser.add_argument(
        "--max-ai-windows", type=int, default=0,
        help="Maximum semantic AI windows; 0 uses adaptive coverage (recommended)."
    )
    parser.add_argument(
        "--ai-workers", type=int, default=1,
        help="Reserved for future Ollama concurrency; current safe mode is one persistent worker."
    )
    parser.add_argument("--cpu-workers", type=int, default=12,
                        help="CPU workers for preprocessing/candidate/export work (1-16).")

    cache_group = parser.add_mutually_exclusive_group()
    cache_group.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the persistent cache for the supplied video.",
    )
    cache_group.add_argument(
        "--clear-all-cache",
        action="store_true",
        help="Clear all gameplay-segmentation caches under the output root.",
    )
    args = parser.parse_args()

    if args.clear_all_cache:
        cache_root = __import__("pathlib").Path(args.output)
        removed = 0
        for source_root in cache_root.glob("*"):
            if not source_root.is_dir():
                continue
            cache_dir = source_root / "_cache"
            if cache_dir.is_dir():
                shutil.rmtree(cache_dir, ignore_errors=True)
                removed += 1
            for run_dir in source_root.glob("run_*"):
                if run_dir.is_dir() and (run_dir / ".incomplete").exists():
                    shutil.rmtree(run_dir, ignore_errors=True)
        print(f"Cleared {removed} cache(s) and incomplete runs under {cache_root.resolve()}")
        return 0

    if not args.video:
        parser.error("video is required unless --clear-all-cache is used.")

    pipeline = GameplaySegmentationPipeline(
        output_root=args.output,
        vision_model=args.vision_model,
        scan_interval_seconds=args.scan_interval,
        analysis_window_seconds=args.analysis_window,
        analysis_stride_seconds=args.analysis_stride,
        frame_interval_seconds=args.frame_interval,
        max_ai_windows=args.max_ai_windows,
        ai_workers=args.ai_workers,
        cpu_workers=args.cpu_workers,
        shared_analysis_path=args.shared_analysis,
    )

    if args.clear_cache:
        path = pipeline.clear_cache(args.video)
        print(f"Cleared cache: {path.resolve()}")
        return 0

    result = pipeline.run(args.video)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
