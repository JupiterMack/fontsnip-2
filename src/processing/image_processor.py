# src/processing/image_processor.py

"""
Implements the image processing pipeline for FontSnip.

This module contains the ImageProcessor class, which is responsible for taking a
raw image capture, preprocessing it for optimal character recognition, and then
running OCR to extract text and bounding box data.
"""

import cv2
import numpy as np
import easyocr
from typing import List, Tuple, Dict, Any

# --- Constants ---
# These values can be moved to a configuration file (e.g., src/config.py)
# for easier user modification.

# Factor by which to upscale the image for better OCR accuracy on small text.
UPSCALE_FACTOR = 3
# Block size for adaptive thresholding. Must be an odd number.
# A larger block size can help with uneven lighting but might miss fine details.
ADAPTIVE_THRESH_BLOCK_SIZE = 15
# Constant subtracted from the mean or weighted mean. Normally, it is positive
# but can be zero or negative as well.
ADAPTIVE_THRESH_C = 4
# Minimum confidence score from OCR to consider a character valid.
OCR_CONFIDENCE_THRESHOLD = 0.60  # 60%
# (Optional) Flag to enable denoising. Can help with noisy images but adds overhead.
ENABLE_DENOISING = False


class ImageProcessor:
    """
    A class that encapsulates the entire image processing and OCR pipeline.

    This class is designed to be instantiated once, as it initializes the
    easyocr.Reader, which can be time-consuming.
    """

    def __init__(self, languages: List[str] = None):
        """
        Initializes the ImageProcessor and the easyocr.Reader.

        Args:
            languages (List[str], optional): A list of language codes for OCR.
                                             Defaults to ['en'].
        """
        if languages is None:
            languages = ['en']
        try:
            # Initialize the OCR reader. This will download the model on first run.
            # We set gpu=False to ensure compatibility on systems without a CUDA-enabled GPU.
            # For users with a compatible GPU, this could be a configurable option for performance.
            self.reader = easyocr.Reader(languages, gpu=False)
            print("EasyOCR reader initialized successfully.")
        except Exception as e:
            print(f"Error initializing EasyOCR reader: {e}")
            # This is a critical failure, the application likely cannot proceed.
            # Consider raising the exception or handling it more gracefully in the main app.
            raise

    def _preprocess(self, image_np: np.ndarray) -> np.ndarray:
        """
        Applies a series of preprocessing steps to the input image to prepare
        it for OCR.

        Args:
            image_np (np.ndarray): The raw BGR image from the screen capture.

        Returns:
            np.ndarray: The preprocessed, binarized (black and white) image.
        """
        # 1. Upscaling
        # Resizing with cubic interpolation improves OCR accuracy, especially for small fonts.
        h, w, _ = image_np.shape
        upscaled_image = cv2.resize(
            image_np,
            (w * UPSCALE_FACTOR, h * UPSCALE_FACTOR),
            interpolation=cv2.INTER_CUBIC
        )

        # 2. Grayscale Conversion
        gray_image = cv2.cvtColor(upscaled_image, cv2.COLOR_BGR2GRAY)

        # 3. (Optional) Noise Reduction
        if ENABLE_DENOISING:
            # This can be effective for noisy sources but adds processing time.
            gray_image = cv2.fastNlMeansDenoising(gray_image, None, h=10, templateWindowSize=7, searchWindowSize=21)

        # 4. Binarization
        # Adaptive thresholding is crucial as it handles variations in background
        # color and lighting within the snip far better than a global threshold.
        # We invert the threshold (THRESH_BINARY_INV) because OCR models often
        # expect black text on a white background.
        binarized_image = cv2.adaptiveThreshold(
            gray_image,
            255,  # Max value
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            ADAPTIVE_THRESH_BLOCK_SIZE,
            ADAPTIVE_THRESH_C
        )

        return binarized_image

    def _run_ocr(self, processed_image: np.ndarray) -> List[Tuple[np.ndarray, str, float]]:
        """
        Runs easyocr on the preprocessed image and filters the results.

        Args:
            processed_image (np.ndarray): The black and white image ready for OCR.

        Returns:
            List[Tuple[np.ndarray, str, float]]: A list of filtered results, where
            each tuple contains (bounding_box, recognized_text, confidence_score).
        """
        # The `detail=1` flag ensures we get bounding boxes and confidence scores.
        # The `paragraph=False` hint can sometimes improve detection of individual characters/words.
        try:
            results = self.reader.readtext(processed_image, detail=1, paragraph=False)
        except Exception as e:
            print(f"An error occurred during OCR processing: {e}")
            return []

        # Filter results based on the confidence threshold
        filtered_results = [
            result for result in results if result[2] >= OCR_CONFIDENCE_THRESHOLD
        ]

        return filtered_results

    def process_image(self, image_np: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Executes the full image processing pipeline.

        Args:
            image_np (np.ndarray): The raw BGR NumPy array of the captured image.

        Returns:
            Tuple[np.ndarray, List[Dict[str, Any]]]:
            - The first element is the final preprocessed (binarized and upscaled)
              image, which is needed for character isolation in the next stage.
            - The second element is a list of dictionaries, where each dictionary
              represents a recognized character and contains its 'bbox', 'text',
              and 'confidence'. The bbox is scaled to the preprocessed image.
        """
        if image_np is None or image_np.size == 0:
            return np.array([]), []

        # Step 1: Preprocess the image
        preprocessed_image = self._preprocess(image_np)

        # Step 2: Run OCR on the preprocessed image
        ocr_results = self._run_ocr(preprocessed_image)

        # Step 3: Format the results for consistency
        # The bounding box from easyocr is [[x1,y1],[x2,y1],[x2,y2],[x1,y2]].
        # We'll return it in this format for now.
        formatted_results = [
            {
                'bbox': result[0],
                'text': result[1],
                'confidence': result[2]
            }
            for result in ocr_results
        ]

        return preprocessed_image, formatted_results


if __name__ == '__main__':
    # This block is for demonstration and testing purposes.
    # It shows how to use the ImageProcessor class.
    print("Running ImageProcessor demonstration...")

    # Create a dummy image for testing.
    # A 100x300 pixel image with some text.
    width, height = 300, 100
    dummy_image = np.full((height, width, 3), 240, dtype=np.uint8)  # Light gray background
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_color = (10, 10, 10)  # Dark gray text
    thickness = 2
    cv2.putText(dummy_image, 'Test Font 123', (10, 60), font, font_scale, font_color, thickness)

    print(f"Created a dummy image of size {dummy_image.shape}")

    # --- Usage Example ---
    try:
        # 1. Initialize the processor (this can be slow the first time)
        processor = ImageProcessor()

        # 2. Process the image
        processed_img, characters = processor.process_image(dummy_image)

        # 3. Display results
        print(f"\nFound {len(characters)} character/word blocks with confidence >= {OCR_CONFIDENCE_THRESHOLD*100}%:")
        for char_data in characters:
            print(
                f"  - Text: '{char_data['text']}', "
                f"Confidence: {char_data['confidence']:.2f}, "
                f"BBox: {char_data['bbox']}"
            )

        # To visualize the output, we can use cv2.imshow
        # Note: cv2.imshow() might not work in all environments (e.g., headless servers)
        # and requires a GUI backend.
        try:
            cv2.imshow('Original Dummy Image', dummy_image)
            # The preprocessed image is inverted (black text on white bg)
            # We can invert it back for display if needed, but we'll show the actual processed one.
            cv2.imshow('Preprocessed for OCR', processed_img)

            # Draw bounding boxes on the original upscaled image for verification
            display_image = cv2.cvtColor(processed_img, cv2.COLOR_GRAY2BGR)
            for char_data in characters:
                # easyocr bbox is a list of 4 points.
                # We need to convert them to integer tuples for drawing.
                box = np.array(char_data['bbox'], dtype=np.int32)
                cv2.polylines(display_image, [box], isClosed=True, color=(0, 255, 0), thickness=1)

            cv2.imshow('OCR Detections', display_image)

            print("\nDisplaying images. Press any key to close.")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except cv2.error as e:
            print(f"\nCould not display images (GUI not available?): {e}")
            print("Demonstration finished.")

    except Exception as e:
        print(f"\nAn error occurred during the demonstration: {e}")
```