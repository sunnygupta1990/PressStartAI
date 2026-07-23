# src/services/ranking_video_cli.py

"""Desktop dialogs for creating a manually ranked video."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from src.services.ranking_video_service import (
    RankingClip,
    RankingVideoError,
    RankingVideoService,
)


class RankingVideoDialog:
    """Collect ranking-video inputs and invoke the renderer."""

    def run(self) -> None:
        """Run the complete ranking-video dialog workflow."""

        root = self._create_root()

        try:
            selected_files = self._select_video_files(root)

            if not selected_files:
                return

            clips = self._collect_clip_details(
                root=root,
                selected_files=selected_files,
            )

            if clips is None:
                return

            output_path = self._select_output_path(
                root=root,
                first_video=selected_files[0],
            )

            if output_path is None:
                return

            self._render_video(
                root=root,
                clips=clips,
                output_path=output_path,
            )
        finally:
            root.destroy()

    @staticmethod
    def _create_root() -> tk.Tk:
        """Create the hidden topmost Tk root."""

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        return root

    @staticmethod
    def _select_video_files(
        root: tk.Tk,
    ) -> tuple[Path, ...]:
        """Select at least two MP4 source clips."""

        selected_files = filedialog.askopenfilenames(
            parent=root,
            title="Select Ranking Video Clips",
            filetypes=[
                ("MP4 video files", "*.mp4"),
            ],
        )

        paths = tuple(
            Path(file_path).expanduser().resolve()
            for file_path in selected_files
        )

        if paths and len(paths) < 2:
            messagebox.showerror(
                "Not Enough Videos",
                "Select at least two MP4 clips.",
                parent=root,
            )
            return ()

        return paths

    def _collect_clip_details(
        self,
        root: tk.Tk,
        selected_files: tuple[Path, ...],
    ) -> list[RankingClip] | None:
        """Collect one unique rank and label for each selected clip."""

        clips: list[RankingClip] = []
        used_ranks: set[int] = set()

        for index, video_path in enumerate(
            selected_files,
            start=1,
        ):
            rank = self._ask_rank(
                root=root,
                video_path=video_path,
                clip_index=index,
                clip_count=len(selected_files),
                used_ranks=used_ranks,
            )

            if rank is None:
                return None

            description = self._ask_description(
                root=root,
                video_path=video_path,
                rank=rank,
            )

            if description is None:
                return None

            used_ranks.add(rank)

            clips.append(
                RankingClip(
                    video_path=video_path,
                    rank=rank,
                    description=description,
                )
            )

        return clips

    def _ask_rank(
        self,
        root: tk.Tk,
        video_path: Path,
        clip_index: int,
        clip_count: int,
        used_ranks: set[int],
    ) -> int | None:
        """Request a unique positive rank."""

        while True:
            rank = simpledialog.askinteger(
                "Enter Video Rank",
                (
                    f"Video {clip_index} of {clip_count}\n\n"
                    f"{video_path.name}\n\n"
                    "Enter its rank number:"
                ),
                parent=root,
                minvalue=1,
            )

            if rank is None:
                return None

            if rank in used_ranks:
                messagebox.showerror(
                    "Duplicate Rank",
                    f"Rank #{rank} has already been assigned.",
                    parent=root,
                )
                continue

            return rank

    @staticmethod
    def _ask_description(
        root: tk.Tk,
        video_path: Path,
        rank: int,
    ) -> str | None:
        """Request one short, single-word description."""

        while True:
            description = simpledialog.askstring(
                "Enter One-Word Description",
                (
                    f"Rank #{rank}\n"
                    f"{video_path.name}\n\n"
                    "Enter one word describing this clip:"
                ),
                parent=root,
            )

            if description is None:
                return None

            normalized = description.strip()

            if not normalized:
                messagebox.showerror(
                    "Missing Description",
                    "Enter a description.",
                    parent=root,
                )
                continue

            if any(character.isspace() for character in normalized):
                messagebox.showerror(
                    "Invalid Description",
                    "The description must contain exactly one word.",
                    parent=root,
                )
                continue

            if len(normalized) > 24:
                messagebox.showerror(
                    "Description Too Long",
                    "The description cannot exceed 24 characters.",
                    parent=root,
                )
                continue

            return normalized

    @staticmethod
    def _select_output_path(
        root: tk.Tk,
        first_video: Path,
    ) -> Path | None:
        """Choose the final ranking-video output path."""

        selected_path = filedialog.asksaveasfilename(
            parent=root,
            title="Save Ranking Video",
            initialdir=str(first_video.parent),
            initialfile="ranking_video.mp4",
            defaultextension=".mp4",
            filetypes=[
                ("MP4 video files", "*.mp4"),
            ],
        )

        if not selected_path:
            return None

        return Path(selected_path).expanduser().resolve()

    @staticmethod
    def _render_video(
        root: tk.Tk,
        clips: list[RankingClip],
        output_path: Path,
    ) -> None:
        """Render the ranking video and report the result."""

        print()
        print("=" * 60)
        print("CREATE RANKING VIDEO")
        print("=" * 60)
        print(f"Clips  : {len(clips)}")
        print(f"Output : {output_path}")
        print()

        try:
            service = RankingVideoService()
            rendered_path = service.render(
                clips=clips,
                output_path=output_path,
            )
        except RankingVideoError as error:
            print(f"Ranking video failed: {error}")

            messagebox.showerror(
                "Ranking Video Failed",
                str(error),
                parent=root,
            )
            return
        except Exception as error:
            print(f"Ranking video failed: {error}")

            messagebox.showerror(
                "Ranking Video Failed",
                str(error),
                parent=root,
            )
            return

        print()
        print("=" * 60)
        print("RANKING VIDEO COMPLETE")
        print("=" * 60)
        print(f"Output : {rendered_path}")

        messagebox.showinfo(
            "Ranking Video Complete",
            f"Video created successfully:\n\n{rendered_path}",
            parent=root,
        )


def create_ranking_video_from_dialogs() -> None:
    """Open dialogs and create one manually ranked video."""

    RankingVideoDialog().run()