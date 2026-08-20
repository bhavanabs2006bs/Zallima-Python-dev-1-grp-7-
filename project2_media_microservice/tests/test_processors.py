import pytest
import os
import tempfile
from PIL import Image
from app.processors.image_processor import ImageProcessor


@pytest.fixture
def sample_image():
    img = Image.new("RGB", (1024, 768), color=(255, 0, 0))
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img.save(f.name, "JPEG")
        yield f.name
    os.unlink(f.name)


def test_resize(sample_image):
    processor = ImageProcessor()
    output = sample_image.replace(".jpg", "_resized.jpg")
    processor.resize(sample_image, output, width=800, height=600)
    assert os.path.exists(output)
    with Image.open(output) as img:
        assert img.size == (800, 600)
    os.unlink(output)


def test_compress(sample_image):
    processor = ImageProcessor()
    output = sample_image.replace(".jpg", "_compressed.jpg")
    processor.compress(sample_image, output, quality=50)
    assert os.path.exists(output)
    os.unlink(output)


def test_thumbnail(sample_image):
    processor = ImageProcessor()
    output = sample_image.replace(".jpg", "_thumb.jpg")
    processor.create_thumbnail(sample_image, output, size=(200, 200))
    assert os.path.exists(output)
    os.unlink(output)
