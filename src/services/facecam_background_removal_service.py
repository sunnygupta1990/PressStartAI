# src/services/facecam_background_removal_service.py

"""Local facecam background removal using Robust Video Matting and OpenVINO."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from openvino import CompiledModel, Core, InferRequest


class FacecamBackgroundRemovalError(RuntimeError):
    """Raised when facecam background removal cannot be completed."""


@dataclass(frozen=True, slots=True)
class MattingFrame:
    """Foreground and alpha data produced for one facecam frame."""

    foreground_bgr: np.ndarray
    alpha: np.ndarray

    def composite_over(
        self,
        background_bgr: np.ndarray,
    ) -> np.ndarray:
        """Composite the extracted person over a BGR background."""

        if not isinstance(background_bgr, np.ndarray):
            raise FacecamBackgroundRemovalError(
                "Background must be a NumPy array."
            )

        if background_bgr.ndim != 3 or background_bgr.shape[2] != 3:
            raise FacecamBackgroundRemovalError(
                "Background must be a three-channel BGR image."
            )

        foreground_height, foreground_width = self.foreground_bgr.shape[:2]

        if background_bgr.shape[:2] != (
            foreground_height,
            foreground_width,
        ):
            background_bgr = cv2.resize(
                background_bgr,
                (foreground_width, foreground_height),
                interpolation=cv2.INTER_AREA,
            )

        alpha_3d = self.alpha[:, :, np.newaxis]

        composite = (
            self.foreground_bgr.astype(np.float32) * alpha_3d
            + background_bgr.astype(np.float32) * (1.0 - alpha_3d)
        )

        return np.clip(composite, 0, 255).astype(np.uint8)


class RvmOpenVinoMattingService:
    """Run Robust Video Matting locally with recurrent temporal state."""

    SOURCE_INPUT = "src"
    RECURRENT_INPUTS = ("r1i", "r2i", "r3i", "r4i")
    DOWNSAMPLE_INPUT = "downsample_ratio"

    FOREGROUND_OUTPUT = "fgr"
    ALPHA_OUTPUT = "pha"
    RECURRENT_OUTPUTS = ("r1o", "r2o", "r3o", "r4o")

    RECURRENT_CHANNELS = (16, 20, 40, 64)

    def __init__(
        self,
        model_path: Path,
        device: str = "CPU",
        downsample_ratio: float = 0.25,
        alpha_threshold: float = 0.0,
        maximum_processing_width: int | None = 1280,
    ) -> None:
        """Load and prepare the OpenVINO RVM model."""

        self._model_path = model_path.expanduser().resolve()
        self._device = device.strip() or "CPU"
        self._downsample_ratio = self._validate_downsample_ratio(
            downsample_ratio
        )
        self._alpha_threshold = self._validate_alpha_threshold(
            alpha_threshold
        )
        self._maximum_processing_width = (
            self._validate_maximum_processing_width(
                maximum_processing_width
            )
        )

        if not self._model_path.exists():
            raise FacecamBackgroundRemovalError(
                f"RVM model was not found: {self._model_path}"
            )

        if not self._model_path.is_file():
            raise FacecamBackgroundRemovalError(
                f"RVM model path is not a file: {self._model_path}"
            )

        try:
            core = Core()
            model = core.read_model(self._model_path)
            self._compiled_model = core.compile_model(
                model,
                self._device,
            )
            self._infer_request = (
                self._compiled_model.create_infer_request()
            )
        except Exception as error:
            raise FacecamBackgroundRemovalError(
                f"Unable to load RVM model on '{self._device}': {error}"
            ) from error

        self._validate_model_interface(self._compiled_model)
        self._recurrent_state = self._create_initial_recurrent_state()

    @property
    def device(self) -> str:
        """Return the configured OpenVINO inference device."""

        return self._device

    @property
    def downsample_ratio(self) -> float:
        """Return the configured RVM downsample ratio."""

        return self._downsample_ratio

    def reset(self) -> None:
        """Reset temporal state before processing a new video."""

        self._recurrent_state = self._create_initial_recurrent_state()

    def process_frame(
        self,
        frame_bgr: np.ndarray,
    ) -> MattingFrame:
        """Remove the background from one OpenCV BGR frame."""

        self._validate_frame(frame_bgr)

        original_height, original_width = frame_bgr.shape[:2]

        processing_frame = self._resize_for_processing(frame_bgr)
        source_tensor = self._prepare_source_tensor(processing_frame)

        inference_inputs: dict[str, np.ndarray] = {
            self.SOURCE_INPUT: source_tensor,
            self.DOWNSAMPLE_INPUT: np.asarray(
                [self._downsample_ratio],
                dtype=np.float32,
            ),
            **self._recurrent_state,
        }

        try:
            inference_results = self._run_inference(
                inference_inputs
            )
        except Exception as error:
            raise FacecamBackgroundRemovalError(
                f"RVM inference failed: {error}"
            ) from error

        alpha = self._prepare_alpha(
            raw_alpha=inference_results[self.ALPHA_OUTPUT],
            output_width=original_width,
            output_height=original_height,
        )

        foreground_bgr = self._prepare_foreground(
            raw_foreground=inference_results[
                self.FOREGROUND_OUTPUT
            ],
            output_width=original_width,
            output_height=original_height,
        )

        self._recurrent_state = {
            input_name: np.asarray(
                inference_results[output_name],
                dtype=np.float32,
            )
            for input_name, output_name in zip(
                self.RECURRENT_INPUTS,
                self.RECURRENT_OUTPUTS,
                strict=True,
            )
        }

        return MattingFrame(
            foreground_bgr=foreground_bgr,
            alpha=alpha,
        )

    def _run_inference(
        self,
        inputs: dict[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        """Run one inference request and normalize outputs by name."""

        raw_results = self._infer_request.infer(inputs)

        output_names = (
            self.FOREGROUND_OUTPUT,
            self.ALPHA_OUTPUT,
            *self.RECURRENT_OUTPUTS,
        )

        return {
            output_name: np.asarray(
                raw_results[
                    self._compiled_model.output(output_name)
                ]
            )
            for output_name in output_names
        }

    def _resize_for_processing(
        self,
        frame_bgr: np.ndarray,
    ) -> np.ndarray:
        """Reduce very large frames while preserving aspect ratio."""

        if self._maximum_processing_width is None:
            return frame_bgr

        height, width = frame_bgr.shape[:2]

        if width <= self._maximum_processing_width:
            return frame_bgr

        scale = self._maximum_processing_width / width
        resized_height = max(1, round(height * scale))

        return cv2.resize(
            frame_bgr,
            (
                self._maximum_processing_width,
                resized_height,
            ),
            interpolation=cv2.INTER_AREA,
        )

    @staticmethod
    def _prepare_source_tensor(
        frame_bgr: np.ndarray,
    ) -> np.ndarray:
        """Convert an OpenCV BGR frame to normalized RGB NCHW."""

        frame_rgb = cv2.cvtColor(
            frame_bgr,
            cv2.COLOR_BGR2RGB,
        )

        normalized = (
            frame_rgb.astype(np.float32) / 255.0
        )

        return normalized.transpose(2, 0, 1)[np.newaxis, ...]

    def _prepare_alpha(
        self,
        raw_alpha: np.ndarray,
        output_width: int,
        output_height: int,
    ) -> np.ndarray:
        """Convert model alpha output to a resized float mask."""

        alpha = np.asarray(
            raw_alpha,
            dtype=np.float32,
        ).squeeze()

        if alpha.ndim != 2:
            raise FacecamBackgroundRemovalError(
                f"Unexpected alpha output shape: "
                f"{raw_alpha.shape}"
            )

        alpha = np.clip(alpha, 0.0, 1.0)

        alpha = cv2.resize(
            alpha,
            (output_width, output_height),
            interpolation=cv2.INTER_LINEAR,
        )

        if self._alpha_threshold > 0:
            alpha = np.where(
                alpha >= self._alpha_threshold,
                alpha,
                0.0,
            )

        return alpha.astype(np.float32)

    @staticmethod
    def _prepare_foreground(
        raw_foreground: np.ndarray,
        output_width: int,
        output_height: int,
    ) -> np.ndarray:
        """Convert model RGB foreground output into BGR uint8."""

        foreground = np.asarray(
            raw_foreground,
            dtype=np.float32,
        )

        if foreground.ndim != 4:
            raise FacecamBackgroundRemovalError(
                f"Unexpected foreground output shape: "
                f"{raw_foreground.shape}"
            )

        if foreground.shape[0] != 1:
            raise FacecamBackgroundRemovalError(
                "RVM foreground output must have batch size one."
            )

        foreground = foreground[0]

        if foreground.shape[0] != 3:
            raise FacecamBackgroundRemovalError(
                f"Unexpected foreground channel shape: "
                f"{raw_foreground.shape}"
            )

        foreground_rgb = foreground.transpose(1, 2, 0)
        foreground_rgb = np.clip(
            foreground_rgb * 255.0,
            0,
            255,
        ).astype(np.uint8)

        foreground_bgr = cv2.cvtColor(
            foreground_rgb,
            cv2.COLOR_RGB2BGR,
        )

        return cv2.resize(
            foreground_bgr,
            (output_width, output_height),
            interpolation=cv2.INTER_LINEAR,
        )

    def _create_initial_recurrent_state(
        self,
    ) -> dict[str, np.ndarray]:
        """Create zero-filled temporal state tensors."""

        return {
            input_name: np.zeros(
                (1, channels, 1, 1),
                dtype=np.float32,
            )
            for input_name, channels in zip(
                self.RECURRENT_INPUTS,
                self.RECURRENT_CHANNELS,
                strict=True,
            )
        }

    @classmethod
    def _validate_model_interface(
        cls,
        compiled_model: CompiledModel,
    ) -> None:
        """Verify that the loaded model exposes the RVM interface."""

        available_inputs = {
            input_port.get_any_name()
            for input_port in compiled_model.inputs
        }
        available_outputs = {
            output_port.get_any_name()
            for output_port in compiled_model.outputs
        }

        required_inputs = {
            cls.SOURCE_INPUT,
            cls.DOWNSAMPLE_INPUT,
            *cls.RECURRENT_INPUTS,
        }
        required_outputs = {
            cls.FOREGROUND_OUTPUT,
            cls.ALPHA_OUTPUT,
            *cls.RECURRENT_OUTPUTS,
        }

        missing_inputs = required_inputs - available_inputs
        missing_outputs = required_outputs - available_outputs

        if missing_inputs:
            missing_text = ", ".join(sorted(missing_inputs))
            raise FacecamBackgroundRemovalError(
                f"RVM model is missing inputs: {missing_text}"
            )

        if missing_outputs:
            missing_text = ", ".join(sorted(missing_outputs))
            raise FacecamBackgroundRemovalError(
                f"RVM model is missing outputs: {missing_text}"
            )

    @staticmethod
    def _validate_frame(
        frame_bgr: np.ndarray,
    ) -> None:
        """Validate one OpenCV facecam frame."""

        if not isinstance(frame_bgr, np.ndarray):
            raise FacecamBackgroundRemovalError(
                "Facecam frame must be a NumPy array."
            )

        if frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3:
            raise FacecamBackgroundRemovalError(
                "Facecam frame must use three-channel BGR format."
            )

        if frame_bgr.size == 0:
            raise FacecamBackgroundRemovalError(
                "Facecam frame cannot be empty."
            )

    @staticmethod
    def _validate_downsample_ratio(
        value: float,
    ) -> float:
        """Validate the RVM internal downsample ratio."""

        ratio = float(value)

        if not 0.05 <= ratio <= 1.0:
            raise FacecamBackgroundRemovalError(
                "Downsample ratio must be between 0.05 and 1.0."
            )

        return ratio

    @staticmethod
    def _validate_alpha_threshold(
        value: float,
    ) -> float:
        """Validate the optional alpha cleanup threshold."""

        threshold = float(value)

        if not 0.0 <= threshold <= 1.0:
            raise FacecamBackgroundRemovalError(
                "Alpha threshold must be between 0.0 and 1.0."
            )

        return threshold

    @staticmethod
    def _validate_maximum_processing_width(
        value: int | None,
    ) -> int | None:
        """Validate the optional processing-width limit."""

        if value is None:
            return None

        maximum_width = int(value)

        if maximum_width < 64:
            raise FacecamBackgroundRemovalError(
                "Maximum processing width must be at least 64."
            )

        return maximum_width