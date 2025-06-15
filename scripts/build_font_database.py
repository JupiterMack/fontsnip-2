# scripts/build_font_database.py

"""
Standalone script to pre-compute the font feature database for FontSnip.

This script performs the following steps:
1.  Locates all .ttf and .otf font files on the system using `find_system_fonts`.
2.  For each font file, it renders a standard set of characters ('a-z', 'A-Z', '0-9')
    into in-memory images using the Pillow library.
3.  For each rendered character image, it runs the `extract_features` function,
    which is the same feature extraction logic used by the main application.
4.  It computes an average feature vector for each font based on its rendered characters.
5.  The final database, a dictionary mapping font file paths to their average
    feature vectors, is saved to 'font_features.pkl' in the project root directory.

This pre-computation is essential for the performance of the main application, as it
avoids the need to render and analyze fonts on-the-fly during a matching operation.

To run this script:
    python scripts/build_font_database.py
"""

import os
import sys
import pickle
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- Add project root to sys.path to allow for imports from src ---
# This allows the script to be run from any directory and still find the 'src' package.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# --- End of path modification ---

try:
    from src.utils.font_utils import find_system_fonts
    from src.matching.feature_extractor import extract_features
except ImportError as e:
    print(f"Error: Failed to import necessary modules from 'src'.\n"
          f"Please ensure the script is run from the project's root directory or that "
          f"the 'src' directory is in your PYTHONPATH.\nDetails: {e}")
    sys.exit(1)


# --- Constants ---

# The set of characters to render for each font to generate its feature vector.
# A more comprehensive set might yield better results but will take longer to process.
CHARACTER_SET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# The point size to render the font at. This should be a reasonably high resolution
# to capture detail, similar to what the upscaled captured image would look like.
FONT_SIZE = 48

# The size of the canvas to render each character on. Must be large enough to fit
# the character without clipping.
IMAGE_WIDTH, IMAGE_HEIGHT = 64, 64

# The name of the output file that will store the compiled font database.
# It will be saved in the project's root directory.
OUTPUT_DB_PATH = os.path.join(PROJECT_ROOT, "font_features.pkl")


def render_character_image(font_path, character, font_size):
    """
    Renders a single character using a given font file and returns it as a
    binary NumPy array.

    The output image is a white glyph on a black background, mimicking the
    output of the main application's preprocessing pipeline.

    Args:
        font_path (str): The absolute path to the .ttf or .otf font file.
        character (str): The single character to render.
        font_size (int): The point size to use for rendering.

    Returns:
        np.ndarray: A 2D NumPy array representing the binary image of the
                    character, or None if the character could not be rendered.
    """
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        # Pillow cannot handle this font file (e.g., it's corrupted).
        return None

    # Create a black, grayscale canvas.
    image = Image.new("L", (IMAGE_WIDTH, IMAGE_HEIGHT), "black")
    draw = ImageDraw.Draw(image)

    # Get the bounding box of the character to center it on the canvas.
    try:
        # Use getbbox for Pillow >= 10.0.0, getsize is deprecated
        if hasattr(font, 'getbbox'):
            bbox = font.getbbox(character)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            # Position to draw the character
            x = (IMAGE_WIDTH - text_width) / 2 - bbox[0]
            y = (IMAGE_HEIGHT - text_height) / 2 - bbox[1]
        else:  # Fallback for older Pillow versions
            text_width, text_height = draw.textsize(character, font=font)
            x = (IMAGE_WIDTH - text_width) / 2
            y = (IMAGE_HEIGHT - text_height) / 2

    except Exception:
        # Some fonts may not support certain characters or have glyph errors.
        return None

    # Draw the character in white.
    draw.text((x, y), character, font=font, fill="white")

    # Convert the Pillow image to a NumPy array.
    # The array will have values 0 (black) and 255 (white).
    return np.array(image)


def build_font_database():
    """
    Finds all system fonts, renders a standard set of characters for each,
    extracts features, and saves the aggregated data to a pickle file.
    """
    print("--- FontSnip: Font Database Builder ---")
    print(f"Characters to be rendered per font: '{CHARACTER_SET}'")
    print(f"Rendering at font size: {FONT_SIZE}pt")
    print("-" * 40)

    font_paths = find_system_fonts()
    if not font_paths:
        print("\nError: No system fonts found. Please check your system's font directories.")
        sys.exit(1)

    total_fonts = len(font_paths)
    print(f"Found {total_fonts} font files to process.")

    font_database = {}
    processed_count = 0
    skipped_count = 0

    for i, font_path in enumerate(font_paths):
        font_name = os.path.basename(font_path)
        progress = f"[{i+1}/{total_fonts}]"
        print(f"\n{progress} Processing: {font_name}")

        char_features_list = []
        for char in CHARACTER_SET:
            # 1. Render the character to an image (NumPy array)
            char_image = render_character_image(font_path, char, FONT_SIZE)

            if char_image is None or np.sum(char_image) == 0:
                # Skip if rendering failed or produced a blank image
                continue

            # 2. Extract features from the rendered image
            # The feature extractor expects a binary image (0s and 255s), which we have.
            feature_vector = extract_features(char_image)

            if feature_vector is not None:
                char_features_list.append(feature_vector)

        # 3. Average the feature vectors for the entire font
        if char_features_list:
            # Convert list of vectors to a 2D NumPy array and compute the mean along axis 0
            # This creates a single, average feature vector for the font.
            average_feature_vector = np.mean(char_features_list, axis=0)
            font_database[font_path] = average_feature_vector
            processed_count += 1
            print(f"  -> Successfully generated feature vector from {len(char_features_list)} characters.")
        else:
            skipped_count += 1
            print(f"  -> Skipped. Could not extract any valid character features.")

    print("\n" + "=" * 40)
    print("Font database build complete.")
    print(f"Successfully processed: {processed_count} fonts")
    print(f"Skipped / Failed:     {skipped_count} fonts")
    print(f"Total:                {total_fonts} fonts")
    print("=" * 40)

    if not font_database:
        print("\nError: The final database is empty. No fonts could be processed.")
        sys.exit(1)

    # 4. Save the compiled database to a file
    try:
        with open(OUTPUT_DB_PATH, "wb") as f:
            pickle.dump(font_database, f)
        print(f"\nDatabase successfully saved to: {OUTPUT_DB_PATH}")
    except Exception as e:
        print(f"\nError: Failed to save the database file. Reason: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_font_database()
```