from src.utils.logger import get_logger


def test_logger():
    logger = get_logger("test")

    logger.info("Logger test successful")

    assert logger.name == "test"