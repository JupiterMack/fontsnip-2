# src/matching/feature_extractor.py

"""
Extracts a feature vector from a single character's image (glyph bitmap).

This module provides the core function `extract_features`, which computes a
numerical "fingerprint" for a given character image. This fingerprint is a
vector containing geometric and topological properties of the glyph, which is
later used to compare against a database of known font features.

The features are designed to be scale-invariant and robust to minor variations.
"""

import cv2
import numpy as np
from typing import Tuple

# Define the number of features that will be extracted.
# This is useful for other modules that need to know the vector size.
# 1. Aspect Ratio
# 2. Pixel Density
# 3. Normalized Centroid X
# 4. Normalized Centroid Y
# 5. Number of Holes
# 6. Normalized Contour Perimeter
# 7. Normalized Contour Area
FEATURE_VECTOR_SIZE = 7


def extract_features(char_image: np.ndarray) -> np.ndarray:
    """
    Computes a feature vector for a single character glyph image.

    The input image should be a binarized, single-channel (grayscale) NumPy array,
    where the character is in white (255) and the background is black (0).

    Args:
        char_image (np.ndarray): The binarized image of the character.

    Returns:
        np.ndarray: A 1D NumPy array of size FEATURE_VECTOR_SIZE containing
                    the extracted features. Returns a zero vector if the
                    image is invalid or contains no features.
    """
    # --- 0. Input Validation and Pre-check ---
    if char_image is None or char_image.size == 0:
        return np.zeros(FEATURE_VECTOR_SIZE, dtype=np.float32)

    # Ensure the image is 8-bit single-channel
    if char_image.dtype != np.uint8:
        char_image = char_image.astype(np.uint8)

    h, w = char_image.shape
    if h == 0 or w == 0 or np.count_nonzero(char_image) == 0:
        return np.zeros(FEATURE_VECTOR_SIZE, dtype=np.float32)

    # --- 1. Aspect Ratio ---
    aspect_ratio = w / h

    # --- 2. Pixel Density ---
    total_pixels = h * w
    white_pixels = np.count_nonzero(char_image)
    pixel_density = white_pixels / total_pixels

    # --- 3. Centroid Location ---
    moments = cv2.moments(char_image)
    if moments["m00"] == 0:
        # If there's no mass, centroid is undefined. Place at center.
        norm_centroid_x = 0.5
        norm_centroid_y = 0.5
    else:
        # Center of mass, normalized by image dimensions
        centroid_x = moments["m10"] / moments["m00"]
        centroid_y = moments["m01"] / moments["m00"]
        norm_centroid_x = centroid_x / w
        norm_centroid_y = centroid_y / h

    # --- 4. Contour Analysis (Holes, Perimeter, Area) ---
    # cv2.RETR_CCOMP retrieves all contours and organizes them into a 2-level
    # hierarchy. Top level are external boundaries, second level are holes.
    contours, hierarchy = cv2.findContours(
        char_image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
    )

    num_holes = 0
    total_perimeter = 0
    total_area = 0

    if hierarchy is not None and len(hierarchy) > 0:
        # Count contours that have a parent (i.e., they are holes)
        # hierarchy[0][i][3] is the parent index of contour i
        for i in range(len(hierarchy[0])):
            if hierarchy[0][i][3] != -1:
                num_holes += 1

        # Calculate total perimeter and area for all contours
        for contour in contours:
            total_perimeter += cv2.arcLength(contour, True)
            total_area += cv2.contourArea(contour)

    # Normalize perimeter and area to be scale-invariant
    # Perimeter is normalized by the sum of dimensions, area by total pixels
    norm_total_perimeter = total_perimeter / (h + w) if (h + w) > 0 else 0
    norm_total_area = total_area / total_pixels if total_pixels > 0 else 0

    # --- 5. Assemble Feature Vector ---
    feature_vector = np.array([
        aspect_ratio,
        pixel_density,
        norm_centroid_x,
        norm_centroid_y,
        float(num_holes),  # Cast to float for consistency
        norm_total_perimeter,
        norm_total_area
    ], dtype=np.float32)

    return feature_vector


if __name__ == '__main__':
    # This block is for demonstration and testing purposes.
    # It will not run when the module is imported.

    def create_test_char(char: str, size: Tuple[int, int] = (100, 100)) -> np.ndarray:
        """Creates a sample character image for testing."""
        img = np.zeros(size, dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size, _ = cv2.getTextSize(char, font, 2, 3)
        text_x = (img.shape[1] - text_size[0]) // 2
        text_y = (img.shape[0] + text_size[1]) // 2
        cv2.putText(img, char, (text_x, text_y), font, 2, (255), 3, cv2.LINE_AA)
        return img

    print("--- Testing Feature Extractor ---")

    # Test case 1: Character 'O' (should have 1 hole)
    char_o_img = create_test_char('O')
    features_o = extract_features(char_o_img)
    print(f"\nCharacter 'O' (expecting 1 hole):")
    print(f"Feature Vector (size {len(features_o)}):")
    print(features_o)
    assert len(features_o) == FEATURE_VECTOR_SIZE
    assert int(features_o[4]) == 1, f"Expected 1 hole for 'O', but got {features_o[4]}"
    print("Test Passed: Hole count for 'O' is correct.")

    # Test case 2: Character 'B' (should have 2 holes)
    char_b_img = create_test_char('B')
    features_b = extract_features(char_b_img)
    print(f"\nCharacter 'B' (expecting 2 holes):")
    print(f"Feature Vector (size {len(features_b)}):")
    print(features_b)
    assert len(features_b) == FEATURE_VECTOR_SIZE
    assert int(features_b[4]) == 2, f"Expected 2 holes for 'B', but got {features_b[4]}"
    print("Test Passed: Hole count for 'B' is correct.")

    # Test case 3: Character 'T' (should have 0 holes)
    char_t_img = create_test_char('T')
    features_t = extract_features(char_t_img)
    print(f"\nCharacter 'T' (expecting 0 holes):")
    print(f"Feature Vector (size {len(features_t)}):")
    print(features_t)
    assert len(features_t) == FEATURE_VECTOR_SIZE
    assert int(features_t[4]) == 0, f"Expected 0 holes for 'T', but got {features_t[4]}"
    print("Test Passed: Hole count for 'T' is correct.")

    # Test case 4: Empty image
    empty_img = np.zeros((50, 50), dtype=np.uint8)
    features_empty = extract_features(empty_img)
    print(f"\nEmpty Image:")
    print(f"Feature Vector (size {len(features_empty)}):")
    print(features_empty)
    assert np.all(features_empty == 0)
    print("Test Passed: Empty image returns a zero vector.")

    print("\n--- All Tests Completed ---")