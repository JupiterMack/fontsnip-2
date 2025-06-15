# src/processing/__init__.py

"""
Initializes the 'processing' sub-package for the FontSnip application.

This package is responsible for the entire image processing pipeline, which takes the
raw pixel data from a screen capture and prepares it for Optical Character
Recognition (OCR) and subsequent font feature extraction.

The core workflow within this package includes:
1.  **Preprocessing**: Cleaning and enhancing the captured image. This involves
    upscaling for clarity, converting to grayscale, and applying adaptive
    binarization to create a clean black-and-white image suitable for analysis.
    Optional noise reduction steps may also be included.

2.  **OCR**: Using an OCR engine (like easyocr) to detect and recognize
    characters within the preprocessed image. This step extracts not just the
    text but also crucial metadata like bounding boxes and confidence scores for
    each character.

The output of this package is a structured set of recognized characters and their
corresponding image data, which is then passed to the 'matching' package for
feature extraction and font identification.
"""

# To create a simpler API for the rest of the application, key functions
# from modules within this package can be imported here. For example, if the
# main pipeline logic resides in a 'pipeline.py' module, you could expose it like this:
#
# from .pipeline import process_image
#
# This would allow other parts of the code to call `processing.process_image()`
# instead of `processing.pipeline.process_image()`.