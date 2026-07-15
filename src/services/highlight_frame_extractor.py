from pathlib import Path

import cv2

from src.models.generated_highlight import GeneratedHighlight


class HighlightFrameExtractor:
    """Extract representative frames from generated highlight clips."""

    def __init__(
        self,
        frame_count: int = 5,
    ) -> None:
        self.frame_count = frame_count

    def extract(
        self,
        highlight: GeneratedHighlight,
        output_folder: str,
    ) -> list[str]:
        video_path = Path(highlight.file_path)

        if not video_path.is_file():
            raise FileNotFoundError(
                f"Highlight video does not exist: {video_path}"
            )

        output_path = Path(output_folder)
        output_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        frame_prefix = (
            f"highlight_{highlight.rank:03d}_frame_"
        )

        for old_file in output_path.glob(
            f"{frame_prefix}*.jpg"
        ):
            old_file.unlink()

        capture = cv2.VideoCapture(
            str(video_path)
        )

        if not capture.isOpened():
            raise RuntimeError(
                f"Unable to open highlight video: {video_path}"
            )

        total_frames = int(
            capture.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        if total_frames <= 0:
            capture.release()

            return []

        sample_count = min(
            self.frame_count,
            total_frames,
        )

        frame_indexes = self._calculate_frame_indexes(
            total_frames=total_frames,
            sample_count=sample_count,
        )

        generated_frames: list[str] = []

        try:
            for frame_number, frame_index in enumerate(
                frame_indexes,
                start=1,
            ):
                capture.set(
                    cv2.CAP_PROP_POS_FRAMES,
                    frame_index,
                )

                success, frame = capture.read()

                if not success:
                    continue

                output_file = output_path / (
                    f"{frame_prefix}"
                    f"{frame_number:03d}.jpg"
                )

                written = cv2.imwrite(
                    str(output_file),
                    frame,
                )

                if not written:
                    continue

                generated_frames.append(
                    str(output_file)
                )
        finally:
            capture.release()

        return generated_frames

    @staticmethod
    def _calculate_frame_indexes(
        total_frames: int,
        sample_count: int,
    ) -> list[int]:
        if sample_count <= 0:
            return []

        if sample_count == 1:
            return [
                max(
                    0,
                    total_frames // 2,
                )
            ]

        last_frame_index = total_frames - 1

        return [
            round(
                index
                * last_frame_index
                / (sample_count - 1)
            )
            for index in range(sample_count)
        ]