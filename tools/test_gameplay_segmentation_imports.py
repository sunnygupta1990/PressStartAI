
def test_gameplay_segmentation_imports():
    from src.gameplay_segmentation.pipeline import GameplaySegmentationPipeline
    from src.gameplay_segmentation.models import ClipCandidate
    assert GameplaySegmentationPipeline is not None
    assert ClipCandidate is not None
