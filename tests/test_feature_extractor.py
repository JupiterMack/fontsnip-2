# tests/test_feature_extractor.py

"""
Unit tests for the font feature extraction logic in `src/matching/feature_extractor.py`.

This test suite uses pytest and pre-defined sample character images (e.g., a bitmap
of 'O', 'I', 'L', and 'B') to verify that feature vectors (aspect ratio, hole count,
pixel density, etc.) are calculated correctly and robustly.
"""

import pytest
import numpy as np
import cv2

from src.matching.feature_extractor import extract_features, FEATURE_VECTOR_SIZE

# --- Test Data Fixtures ---

@pytest.fixture
def image_o():
    """
    Creates a 20x20 binary image of a hollow square, simulating the letter 'O'.
    White (255) on black (0) background.
    """
    img = np.zeros((20, 20), dtype=np.uint8)
    # Draw a white square border (character)
    cv2.rectangle(img, (3, 3), (16, 16), 255, -1)
    # Carve out the middle (hole)
    cv2.rectangle(img, (6, 6), (13, 13), 0, -1)
    return img

@pytest.fixture
def image_i():
    """
    Creates a 20x10 binary image of a vertical bar, simulating the letter 'I'.
    """
    img = np.zeros((20, 10), dtype=np.uint8)
    # Draw a vertical bar
    cv2.rectangle(img, (4, 2), (5, 17), 255, -1)
    return img

@pytest.fixture
def image_l():
    """
    Creates a 20x15 binary image of an 'L' shape.
    """
    img = np.zeros((20, 15), dtype=np.uint8)
    # Vertical part
    cv2.rectangle(img, (2, 2), (4, 17), 255, -1)
    # Horizontal part
    cv2.rectangle(img, (4, 15), (12, 17), 255, -1)
    return img

@pytest.fixture
def image_b():
    """
    Creates a 30x20 binary image simulating a 'B' with two holes.
    """
    img = np.zeros((30, 20), dtype=np.uint8)
    # Outer shape
    cv2.rectangle(img, (2, 2), (17, 27), 255, -1)
    # Top hole
    cv2.rectangle(img, (5, 5), (14, 11), 0, -1)
    # Bottom hole
    cv2.rectangle(img, (5, 16), (14, 24), 0, -1)
    # Separator
    cv2.rectangle(img, (2, 13), (17, 14), 0, -1)
    return img

@pytest.fixture
def image_all_black():
    """A 10x10 all-black image."""
    return np.zeros((10, 10), dtype=np.uint8)

@pytest.fixture
def image_all_white():
    """A 10x10 all-white image."""
    return np.full((10, 10), 255, dtype=np.uint8)


# --- Test Cases ---

def test_return_type_and_shape(image_o):
    """
    Tests that the feature vector has the correct type and shape.
    """
    features = extract_features(image_o)
    assert isinstance(features, np.ndarray), "Features should be a NumPy array"
    assert features.dtype == np.float64, "Feature vector dtype should be float64"
    assert features.ndim == 1, "Feature vector should be 1-dimensional"
    assert features.shape[0] == FEATURE_VECTOR_SIZE, f"Feature vector should have size {FEATURE_VECTOR_SIZE}"

def test_features_for_o_shape(image_o):
    """
    Validates the calculated features for a symmetrical 'O' shape.
    """
    features = extract_features(image_o)

    # Expected values for the 'O' fixture
    # 1. Aspect Ratio: height=20, width=20 -> 20/20 = 1.0
    expected_aspect_ratio = 1.0

    # 2. Pixel Density:
    h, w = image_o.shape
    white_pixels = np.sum(image_o == 255)
    expected_density = white_pixels / (h * w)

    # 3. Centroid: Should be perfectly centered for a symmetric shape.
    expected_centroid_x = 0.5
    expected_centroid_y = 0.5

    # 4. Hole Count: The 'O' shape has one hole.
    expected_holes = 1.0

    # The feature vector order must match the implementation in feature_extractor.py
    assert np.isclose(features[0], expected_aspect_ratio), "Incorrect aspect ratio for 'O'"
    assert np.isclose(features[1], expected_density), "Incorrect pixel density for 'O'"
    assert np.isclose(features[2], expected_centroid_x, atol=0.05), "Incorrect centroid X for 'O'"
    assert np.isclose(features[3], expected_centroid_y, atol=0.05), "Incorrect centroid Y for 'O'"
    assert np.isclose(features[4], expected_holes), "Incorrect hole count for 'O'"

def test_features_for_i_shape(image_i):
    """
    Validates the calculated features for a tall, thin 'I' shape.
    """
    features = extract_features(image_i)

    # Expected values for the 'I' fixture
    # 1. Aspect Ratio: height=20, width=10 -> 10/20 = 0.5
    h, w = image_i.shape
    expected_aspect_ratio = w / h

    # 2. Pixel Density:
    white_pixels = np.sum(image_i == 255)
    expected_density = white_pixels / (h * w)

    # 3. Centroid: Should be centered.
    expected_centroid_x = 0.5
    expected_centroid_y = 0.5

    # 4. Hole Count: The 'I' shape has no holes.
    expected_holes = 0.0

    assert np.isclose(features[0], expected_aspect_ratio), "Incorrect aspect ratio for 'I'"
    assert np.isclose(features[1], expected_density), "Incorrect pixel density for 'I'"
    assert np.isclose(features[2], expected_centroid_x, atol=0.05), "Incorrect centroid X for 'I'"
    assert np.isclose(features[3], expected_centroid_y, atol=0.05), "Incorrect centroid Y for 'I'"
    assert np.isclose(features[4], expected_holes), "Incorrect hole count for 'I'"

def test_features_for_l_shape(image_l):
    """
    Validates the calculated features for an asymmetrical 'L' shape.
    """
    features = extract_features(image_l)

    # Centroid should not be at (0.5, 0.5)
    centroid_x, centroid_y = features[2], features[3]
    assert not np.isclose(centroid_x, 0.5), "Centroid X should be off-center for 'L'"
    assert not np.isclose(centroid_y, 0.5), "Centroid Y should be off-center for 'L'"

    # Hole Count: The 'L' shape has no holes.
    expected_holes = 0.0
    assert np.isclose(features[4], expected_holes), "Incorrect hole count for 'L'"


def test_hole_count(image_o, image_i, image_b):
    """
    Specifically tests the hole counting feature on various shapes.
    """
    features_o = extract_features(image_o)
    features_i = extract_features(image_i)
    features_b = extract_features(image_b)

    assert np.isclose(features_o[4], 1.0), "Hole count for 'O' should be 1"
    assert np.isclose(features_i[4], 0.0), "Hole count for 'I' should be 0"
    assert np.isclose(features_b[4], 2.0), "Hole count for 'B' should be 2"


def test_edge_case_all_black(image_all_black):
    """
    Tests feature extraction on an all-black image.
    It should not crash and should return a zero vector.
    """
    features = extract_features(image_all_black)

    # Expect a vector of all zeros, as there are no white pixels
    expected_vector = np.zeros(FEATURE_VECTOR_SIZE, dtype=np.float64)

    assert np.array_equal(features, expected_vector), "All-black image should produce a zero vector"

def test_edge_case_all_white(image_all_white):
    """
    Tests feature extraction on an all-white image.
    It should not crash and should return a predictable vector.
    """
    features = extract_features(image_all_white)

    # Expected values
    # 1. Aspect Ratio: 10/10 = 1.0
    expected_aspect_ratio = 1.0

    # 2. Pixel Density: 1.0
    expected_density = 1.0

    # 3. Centroid: Should be centered.
    expected_centroid_x = 0.5
    expected_centroid_y = 0.5

    # 4. Hole Count: No contours, no holes.
    expected_holes = 0.0

    assert np.isclose(features[0], expected_aspect_ratio), "Incorrect aspect ratio for all-white"
    assert np.isclose(features[1], expected_density), "Incorrect pixel density for all-white"
    assert np.isclose(features[2], expected_centroid_x, atol=0.05), "Incorrect centroid X for all-white"
    assert np.isclose(features[3], expected_centroid_y, atol=0.05), "Incorrect centroid Y for all-white"
    assert np.isclose(features[4], expected_holes), "Incorrect hole count for all-white"
```