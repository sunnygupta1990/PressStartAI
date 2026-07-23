"""Independent command-line interface for PressStartAI thumbnail generation."""

from datetime import datetime
from dataclasses import replace
from enum import Enum
from pathlib import Path
import re
from typing import Any

from src.thumbnail_generator.models.video_request import (
    VideoMode,
    VideoRequest,
    VideoRequestError,
)
from src.thumbnail_generator.services.internet_research_service import (
    GameResearch,
    research_video_context_safe,
)
from src.thumbnail_generator.services.background_removal_service import (
    BackgroundRemovalError,
    CreatorCutout,
    remove_creator_backgrounds,
)
from src.thumbnail_generator.services.creator_asset_service import (
    CreatorAsset,
    CreatorAssetError,
    load_creator_assets,
)
from src.thumbnail_generator.services.frame_extraction_service import (
    ExtractedFrame,
    FrameExtractionError,
    extract_candidate_frames,
)
from src.thumbnail_generator.services.frame_scoring_service import (
    FrameScore,
    FrameScoringError,
    score_extracted_frames,
)
from src.thumbnail_generator.services.moment_scanner_service import (
    MomentCandidate,
    MomentScannerError,
    scan_candidate_moments,
)
from src.thumbnail_generator.services.profile_service import (
    ProfileServiceError,
    get_profile,
    list_profile_choices,
)
from src.thumbnail_generator.services.thumbnail_composition_service import (
    ComposedThumbnail,
    ThumbnailCompositionError,
    ThumbnailVariant,
    compose_thumbnails,
)
from src.thumbnail_generator.services.video_analysis_service import (
    VideoAnalysisError,
    VideoMetadata,
    analyze_video,
)
from src.thumbnail_generator.services.youtube_package_service import (
    SavedYouTubePackage,
    YouTubePackageError,
    generate_youtube_package,
    save_youtube_package,
)


class MenuChoice(str, Enum):
    """Available main-menu choices."""

    FULL_GAMEPLAY = "1"
    EXISTING_HIGHLIGHT = "2"
    CHANNEL_PROFILES = "3"
    EXIT = "4"


def display_header() -> None:
    """Display the application header."""

    print()
    print("=" * 60)
    print("PRESSSTARTAI THUMBNAIL GENERATOR")
    print("=" * 60)


def display_main_menu() -> None:
    """Display the available workflows."""

    display_header()
    print()
    print("1. Full Gameplay Video")
    print("2. Existing Highlight Video")
    print("3. Channel Profiles")
    print("4. Exit")
    print()
    print("-" * 60)


def pause() -> None:
    """Wait for the user before returning to the menu."""

    input("\nPress ENTER to return to the main menu...")


def prompt_required_text(label: str) -> str:
    """Prompt until the user enters a non-empty value."""

    while True:
        value = input(f"{label}: ").strip()

        if value:
            return value

        print(f"{label} is required.")


def prompt_video_path() -> Path:
    """Prompt for a video file path."""

    raw_path = prompt_required_text("Video file path")
    cleaned_path = raw_path.strip().strip('"').strip("'")
    return Path(cleaned_path)


def select_channel_profile() -> dict[str, Any] | None:
    """Prompt the user to select one configured channel profile."""

    try:
        profiles = list_profile_choices()
    except ProfileServiceError as error:
        print(f"\nUnable to load channel profiles: {error}")
        return None

    print("\nSelect Channel Profile")
    print("-" * 60)

    for index, (_, channel_name) in enumerate(profiles, start=1):
        print(f"{index}. {channel_name}")

    print("0. Cancel")

    while True:
        choice = input("\nEnter your choice: ").strip()

        if choice == "0":
            return None

        try:
            selected_index = int(choice) - 1
        except ValueError:
            print("Please enter a valid number.")
            continue

        if not 0 <= selected_index < len(profiles):
            print(f"Please enter a number from 0 to {len(profiles)}.")
            continue

        profile_key, _ = profiles[selected_index]

        try:
            return get_profile(profile_key)
        except ProfileServiceError as error:
            print(f"\nUnable to load the selected profile: {error}")
            return None


def display_selected_profile(profile: dict[str, Any]) -> None:
    """Display the selected channel profile."""

    print()
    print(f"Selected channel: {profile['channel_name']}")
    print(f"Language: {profile['preferred_language']}")
    print(f"Audience: {profile['target_audience']}")


def collect_video_request(
    profile: dict[str, Any],
    video_mode: VideoMode,
) -> VideoRequest | None:
    """Collect and validate one video request."""

    print("\nVideo Details")
    print("-" * 60)

    video_path = prompt_video_path()
    game_name = prompt_required_text("Game name")
    video_type = prompt_required_text(
        "Video type, for example walkthrough, funny moments, or challenge"
    )
    episode_topic = prompt_required_text("Episode or topic")

    try:
        return VideoRequest(
            profile_key=str(profile["profile_key"]),
            channel_name=str(profile["channel_name"]),
            video_mode=video_mode,
            video_path=video_path,
            game_name=game_name,
            video_type=video_type,
            episode_topic=episode_topic,
        )
    except VideoRequestError as error:
        print(f"\nUnable to create video request: {error}")
        return None


def display_video_request(request: VideoRequest) -> None:
    """Display a confirmed video request."""

    mode_name = request.video_mode.value.replace("_", " ").title()

    print("\nRequest Confirmed")
    print("-" * 60)
    print(f"Channel: {request.channel_name}")
    print(f"Mode: {mode_name}")
    print(f"Video: {request.video_path}")
    print(f"Game: {request.game_name}")
    print(f"Video type: {request.video_type}")
    print(f"Episode/topic: {request.episode_topic}")


def display_video_metadata(metadata: VideoMetadata) -> None:
    """Display analyzed video metadata."""

    audio_status = "Yes" if metadata.has_audio else "No"

    print("\nVideo Analysis")
    print("-" * 60)
    print(f"Duration: {metadata.duration_text}")
    print(f"Resolution: {metadata.resolution_text}")
    print(f"Frame rate: {metadata.frame_rate:.2f} FPS")
    print(f"Codec: {metadata.video_codec.upper()}")
    print(f"Audio: {audio_status}")


def display_moment_candidates(
    candidates: list[MomentCandidate],
) -> None:
    """Display selected gameplay moments."""

    print("\nGameplay Moment Candidates")
    print("-" * 60)

    for candidate in candidates:
        print(
            f"{candidate.sequence}. "
            f"{candidate.timestamp_text} "
            f"({candidate.source.replace('_', ' ')})"
        )


def display_extracted_frames(
    frames: list[ExtractedFrame],
    output_directory: Path,
) -> None:
    """Display extracted frame results."""

    print("\nCandidate Frames Extracted")
    print("-" * 60)

    for frame in frames:
        print(
            f"{frame.candidate.sequence}. "
            f"{frame.timestamp_text} -> "
            f"{frame.image_path.name}"
        )

    print(f"\nSaved to: {output_directory}")


def display_frame_scores(scores: list[FrameScore]) -> None:
    """Display ranked visual-scoring results."""

    print("\nVisual Frame Ranking")
    print("-" * 60)

    for score in scores:
        print(f"{score.rank}. {score.image_path.name}")
        print(
            f"   Total: {score.total_score:.2f} | "
            f"Brightness: {score.brightness_score:.2f} | "
            f"Contrast: {score.contrast_score:.2f} | "
            f"Sharpness: {score.sharpness_score:.2f} | "
            f"Color: {score.color_score:.2f} | "
            f"Detail: {score.detail_score:.2f}"
        )

    best_score = scores[0]

    print()
    print(
        f"Best candidate: {best_score.image_path.name} "
        f"({best_score.total_score:.2f}/100)"
    )


def display_creator_assets(
    assets: list[CreatorAsset],
) -> None:
    """Display loaded creator-photo assets."""

    print("\nCreator Photos")
    print("-" * 60)

    for index, asset in enumerate(assets, start=1):
        transparency = "Yes" if asset.has_transparency else "No"
        print(
            f"{index}. {asset.image_path.name} | "
            f"{asset.resolution_text} | "
            f"{asset.image_format} | "
            f"Transparency: {transparency}"
        )


def display_creator_cutouts(
    cutouts: list[CreatorCutout],
    output_directory: Path,
) -> None:
    """Display generated creator cutouts."""

    print("\nCreator Cutouts")
    print("-" * 60)

    for index, cutout in enumerate(cutouts, start=1):
        print(
            f"{index}. {cutout.image_path.name} | "
            f"{cutout.resolution_text}"
        )

    print(f"\nSaved to: {output_directory}")


def display_composed_thumbnails(
    thumbnails: list[ComposedThumbnail],
    output_directory: Path,
) -> None:
    """Display final thumbnail output paths."""

    print("\nFinal Thumbnails Generated")
    print("-" * 60)

    for index, thumbnail in enumerate(thumbnails, start=1):
        print(
            f"{index}. {thumbnail.image_path.name}"
        )
        print(
            f"   Caption: {thumbnail.caption}"
        )
        print(
            f"   Gameplay frame score: "
            f"{thumbnail.frame_score.total_score:.2f}/100"
        )

    print(f"\nSaved to: {output_directory}")
def display_game_research(
    research: GameResearch,
) -> None:
    """Display internet research results."""

    print("\nInternet Research")
    print("-" * 60)
    print(
        f"Status: "
        f"{'Online' if research.internet_available else 'Local fallback'}"
    )
    print(f"Supplied game name: {research.supplied_game_name}")
    print(f"Effective game name: {research.effective_game_name}")

    if research.game_name_was_corrected:
        print("Game name correction: Applied")

    if research.terminology:
        print(f"Terminology: {', '.join(research.terminology)}")

    if research.warning:
        print(f"Warning: {research.warning}")
def display_youtube_package(
    saved_package: SavedYouTubePackage,
) -> None:
    """Display generated YouTube metadata files."""

    package = saved_package.package

    print("\nYouTube Upload Package")
    print("-" * 60)
    print(f"Primary title: {package.primary_title}")
    print(f"Alternate titles: {len(package.alternate_titles)}")
    print(f"Hashtags: {' '.join(package.hashtags)}")
    print(f"TXT: {saved_package.text_path}")
    print(f"JSON: {saved_package.json_path}")

def create_run_output_directory(
    request: VideoRequest,
) -> Path:
    """Create a descriptive root output directory for one run."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    game_slug = slugify(request.game_name)
    topic_slug = slugify(request.episode_topic)
    video_slug = slugify(request.video_path.stem)

    run_name = (
        f"{timestamp}_{game_slug}_{topic_slug}_{video_slug}"
    )

    return (
        Path("output")
        / "thumbnail_generator"
        / request.profile_key
        / run_name
    )


def create_thumbnail_variants(
    request: VideoRequest,
    profile: dict[str, Any],
) -> list[ThumbnailVariant]:
    """Create five adaptive caption and layout variants."""

    language = str(
        profile.get("preferred_language", "English")
    ).lower()

    video_type = request.video_type.lower()
    game_name = request.game_name.upper()
    topic = request.episode_topic.upper()

    if "funny" in video_type:
        captions = (
            "YE KYA HO GAYA?!",
            "SAB ULTA PAD GAYA",
            "BIGGEST FAIL EVER",
            "CONTROL HI NAHI HUA",
            f"{game_name} GONE WRONG",
        )
    elif "challenge" in video_type:
        captions = (
            "CHALLENGE ACCEPTED",
            "KYA MAIN KAR PAUNGA?",
            "THIS WAS IMPOSSIBLE",
            "LAST TRY CLUTCH",
            f"{topic} COMPLETE?",
        )
    elif "walkthrough" in video_type:
        captions = (
            f"{topic} BEGINS",
            "SECRET PATH FOUND",
            "YE AREA DANGEROUS HAI",
            "BOSS KE PAAS PAHUNCH GAYA",
            f"{game_name} FULL ACTION",
        )
    elif "boss" in video_type:
        captions = (
            "BOSS FIGHT START!",
            "YE KITNA TOUGH HAI?!",
            "ONE LAST ATTEMPT",
            "BOSS KO HARA DIYA?",
            "FINAL CLUTCH MOMENT",
        )
    else:
        captions = (
            f"{topic} STARTS NOW",
            "YE KYA MIL GAYA?!",
            "THIS CHANGED EVERYTHING",
            "SABSE DANGEROUS MOMENT",
            f"{game_name} FULL ACTION",
        )

    if "english" in language and "hinglish" not in language:
        captions = tuple(
            _convert_caption_to_english(caption)
            for caption in captions
        )

    return [
        ThumbnailVariant(
            caption=captions[0],
            descriptive_name="strongest_gameplay_reaction",
            creator_side="right",
            gameplay_zoom=1.08,
            creator_scale=0.92,
            darken_strength=82,
        ),
        ThumbnailVariant(
            caption=captions[1],
            descriptive_name="curiosity_creator_left",
            creator_side="left",
            gameplay_zoom=1.04,
            creator_scale=0.88,
            darken_strength=78,
        ),
        ThumbnailVariant(
            caption=captions[2],
            descriptive_name="high_action_creator_right",
            creator_side="right",
            gameplay_zoom=1.12,
            creator_scale=0.86,
            darken_strength=72,
        ),
        ThumbnailVariant(
            caption=captions[3],
            descriptive_name="alternate_reaction_layout",
            creator_side="left",
            gameplay_zoom=1.06,
            creator_scale=0.90,
            darken_strength=80,
        ),
        ThumbnailVariant(
            caption=captions[4],
            descriptive_name="experimental_brand_variant",
            creator_side="right",
            gameplay_zoom=1.02,
            creator_scale=0.84,
            darken_strength=68,
        ),
    ]


def _convert_caption_to_english(caption: str) -> str:
    """Replace common Hinglish phrases with English equivalents."""

    replacements = {
        "YE KYA HO GAYA?!": "WHAT JUST HAPPENED?!",
        "SAB ULTA PAD GAYA": "EVERYTHING WENT WRONG",
        "CONTROL HI NAHI HUA": "I LOST CONTROL",
        "KYA MAIN KAR PAUNGA?": "CAN I COMPLETE THIS?",
        "YE AREA DANGEROUS HAI": "THIS AREA IS DANGEROUS",
        "BOSS KE PAAS PAHUNCH GAYA": "I REACHED THE BOSS",
        "YE KITNA TOUGH HAI?!": "HOW TOUGH IS THIS?!",
        "BOSS KO HARA DIYA?": "DID I BEAT THE BOSS?",
        "YE KYA MIL GAYA?!": "WHAT DID I FIND?!",
        "SABSE DANGEROUS MOMENT": "THE MOST DANGEROUS MOMENT",
    }

    return replacements.get(caption, caption)


def get_logo_settings(
    profile: dict[str, Any],
) -> tuple[bool, Path | None]:
    """Read optional logo settings from a channel profile."""

    logo_settings = profile.get("logo")

    if not isinstance(logo_settings, dict):
        return False, None

    enabled = bool(logo_settings.get("enabled", False))
    raw_path = logo_settings.get("path")

    if not raw_path:
        return enabled, None

    return enabled, Path(str(raw_path))


def slugify(value: str) -> str:
    """Convert text into a safe lowercase filename component."""

    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = normalized.strip("_")

    return normalized or "untitled"


def run_video_workflow(video_mode: VideoMode) -> None:
    """Run the complete local thumbnail-generation workflow."""

    profile = select_channel_profile()

    if profile is None:
        print("\nWorkflow cancelled.")
        pause()
        return

    display_selected_profile(profile)
    request = collect_video_request(profile, video_mode)

    if request is None:
        pause()
        return

    display_video_request(request)
    print("\nResearching current game context...")

    research = research_video_context_safe(
        request=request,
        maximum_results_per_query=5,
    )

    display_game_research(research)

    if research.effective_game_name:
        request = replace(
            request,
            game_name=research.effective_game_name,
        )

    print("\nAnalyzing video...")

    try:
        metadata = analyze_video(request.video_path)
    except VideoAnalysisError as error:
        print(f"\nUnable to analyze video: {error}")
        pause()
        return

    display_video_metadata(metadata)

    print("\nScanning gameplay moments...")

    try:
        candidates = scan_candidate_moments(
            video_path=request.video_path,
            metadata=metadata,
            video_mode=request.video_mode,
            candidate_count=5,
        )
    except MomentScannerError as error:
        print(f"\nUnable to scan gameplay moments: {error}")
        pause()
        return

    display_moment_candidates(candidates)

    run_directory = create_run_output_directory(request)
    candidate_frames_directory = run_directory / "candidate_frames"
    creator_cutouts_directory = run_directory / "creator_cutouts"
    thumbnails_directory = run_directory / "thumbnails"

    print("\nExtracting candidate frames...")

    try:
        frames = extract_candidate_frames(
            video_path=request.video_path,
            candidates=candidates,
            output_directory=candidate_frames_directory,
            width=1280,
            height=720,
        )
    except FrameExtractionError as error:
        print(f"\nUnable to extract candidate frames: {error}")
        pause()
        return

    display_extracted_frames(
        frames,
        candidate_frames_directory,
    )

    print("\nScoring candidate frames...")

    try:
        scores = score_extracted_frames(frames)
    except FrameScoringError as error:
        print(f"\nUnable to score candidate frames: {error}")
        pause()
        return

    display_frame_scores(scores)

    print("\nLoading creator photos...")

    try:
        creator_assets = load_creator_assets(
            Path(str(profile["creator_photos_folder"]))
        )
    except CreatorAssetError as error:
        print(f"\nUnable to load creator photos: {error}")
        pause()
        return

    display_creator_assets(creator_assets)

    print("\nRemoving creator-photo backgrounds...")

    try:
        creator_cutouts = remove_creator_backgrounds(
            assets=creator_assets,
            output_directory=creator_cutouts_directory,
        )
    except BackgroundRemovalError as error:
        print(f"\nUnable to remove creator backgrounds: {error}")
        pause()
        return

    display_creator_cutouts(
        creator_cutouts,
        creator_cutouts_directory,
    )

    variants = create_thumbnail_variants(
        request=request,
        profile=profile,
    )

    logo_enabled, logo_path = get_logo_settings(profile)

    print("\nComposing five thumbnails...")

    try:
        thumbnails = compose_thumbnails(
            frame_scores=scores,
            creator_cutouts=creator_cutouts,
            variants=variants,
            output_directory=thumbnails_directory,
            brand_colors=[
                str(color)
                for color in profile["brand_colors"]
            ],
            logo_path=logo_path,
            logo_enabled=logo_enabled,
            width=1280,
            height=720,
            game_title=request.game_name,
            episode_label=f"PART {request.episode_topic}",
            footer_label=(
                f"{profile['preferred_language']} GAMEPLAY"
            ),
        )

    except ThumbnailCompositionError as error:
        print(f"\nUnable to compose thumbnails: {error}")
        pause()
        return

    display_composed_thumbnails(
        thumbnails,
        thumbnails_directory,
    )
    print("\nGenerating YouTube upload package...")

    try:
        youtube_package = generate_youtube_package(
            request=request,
            profile=profile,
            research=research,
        )
        saved_youtube_package = save_youtube_package(
            package=youtube_package,
            output_directory=run_directory,
        )
    except YouTubePackageError as error:
        print(f"\nUnable to generate YouTube package: {error}")
        pause()
        return

    display_youtube_package(saved_youtube_package)
    print()
    print("=" * 60)
    print("THUMBNAIL GENERATION COMPLETE")
    print("=" * 60)
    print(f"Run folder: {run_directory}")

    pause()


def handle_full_gameplay_mode() -> None:
    """Start the full-gameplay workflow."""

    run_video_workflow(VideoMode.FULL_GAMEPLAY)


def handle_existing_highlight_mode() -> None:
    """Start the existing-highlight workflow."""

    run_video_workflow(VideoMode.EXISTING_HIGHLIGHT)


def handle_channel_profiles() -> None:
    """Display all configured channel profiles."""

    print("\nConfigured Channel Profiles")
    print("-" * 60)

    try:
        profiles = list_profile_choices()
    except ProfileServiceError as error:
        print(f"\nUnable to load channel profiles: {error}")
        pause()
        return

    for index, (_, channel_name) in enumerate(profiles, start=1):
        print(f"{index}. {channel_name}")

    print(f"\nTotal profiles: {len(profiles)}")
    pause()


def main() -> None:
    """Run the thumbnail-generator application."""

    actions = {
        MenuChoice.FULL_GAMEPLAY.value: handle_full_gameplay_mode,
        MenuChoice.EXISTING_HIGHLIGHT.value: handle_existing_highlight_mode,
        MenuChoice.CHANNEL_PROFILES.value: handle_channel_profiles,
    }

    while True:
        display_main_menu()
        choice = input("Enter your choice: ").strip()

        if choice == MenuChoice.EXIT.value:
            print("\nThumbnail Generator closed.")
            return

        action = actions.get(choice)

        if action is None:
            print("\nPlease enter 1, 2, 3, or 4.")
            continue

        action()


if __name__ == "__main__":
    main()