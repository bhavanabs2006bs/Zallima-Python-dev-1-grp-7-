import os
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ImageProcessor:
    def resize(self, input_path: str, output_path: str, width: int = 800, height: int = 600):
        logger.info(f"Resizing image: {input_path} -> {output_path}")
        with Image.open(input_path) as img:
            img_ratio = img.width / img.height
            target_ratio = width / height
            if img_ratio > target_ratio:
                new_width = width
                new_height = int(width / img_ratio)
            else:
                new_height = height
                new_width = int(height * img_ratio)
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            bg = Image.new("RGB", (width, height), (255, 255, 255))
            offset = ((width - new_width) // 2, (height - new_height) // 2)
            bg.paste(resized, offset)
            bg.save(output_path, quality=95)
        logger.info(f"Image resized to {width}x{height}")

    def compress(self, input_path: str, output_path: str, quality: int = 70):
        logger.info(f"Compressing image: {input_path} -> {output_path}")
        with Image.open(input_path) as img:
            if img.mode == "RGBA":
                img = img.convert("RGB")
            img.save(output_path, "JPEG", quality=quality, optimize=True)
        original_size = os.path.getsize(input_path) if os.path.exists(input_path) else 0
        compressed_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        logger.info(f"Compressed by {ratio:.1f}%")

    def create_thumbnail(self, input_path: str, output_path: str, size: Tuple[int, int] = (200, 200)):
        logger.info(f"Creating thumbnail: {input_path} -> {output_path}")
        with Image.open(input_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(output_path, quality=85)
        logger.info(f"Thumbnail created: {size}")

    def add_watermark(self, input_path: str, output_path: str, text: str = "WATERMARK"):
        logger.info(f"Adding watermark: {input_path} -> {output_path}")
        with Image.open(input_path) as img:
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except IOError:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2
            draw.text((x, y), text, fill=(255, 255, 255, 128), font=font)
            watermarked = Image.alpha_composite(img, overlay)
            watermarked.convert("RGB").save(output_path, quality=95)
        logger.info("Watermark added")
