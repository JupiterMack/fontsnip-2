# src/matching/font_matcher.py

"""
Manages the font matching process.

This module contains the FontMatcher class, which is responsible for:
1. Loading a pre-computed font feature database.
2. Calculating an average feature vector for characters from a user's snip.
3. Comparing this target vector against the database using cosine similarity.
4. Returning a ranked list of the most likely font matches.
"""

import pickle
import os
from typing import List, Dict, Tuple, Optional

import numpy as np

# Define a default path for the font database. This could be made configurable.
# It assumes a 'data' directory at the project root, alongside 'src'.
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'font_features.pkl')


class FontMatcher:
    """
    Compares features from a captured image against a pre-computed font database.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        Initializes the FontMatcher and loads the font feature database.

        Args:
            db_path (str): The path to the pre-computed font features file (.pkl).

        Raises:
            FileNotFoundError: If the database file cannot be found at the given path.
            Exception: For other errors during file loading or processing.
        """
        self.db_path = db_path
        self.font_database: Dict[str, np.ndarray] = self._load_database()

    def _load_database(self) -> Dict[str, np.ndarray]:
        """
        Loads the font feature database from a pickle file.

        The database is expected to be a dictionary mapping font file names (str)
        to their corresponding feature vectors (list or np.ndarray).

        Returns:
            A dictionary with font names as keys and NumPy arrays as feature vectors.
        """
        if not os.path.exists(self.db_path):
            # This is a critical error; the application cannot function without the database.
            # The pre-computation script must be run first.
            raise FileNotFoundError(
                f"Font database not found at '{self.db_path}'. "
                "Please run the database generation script first."
            )

        try:
            with open(self.db_path, 'rb') as f:
                data = pickle.load(f)

            # Convert all feature vectors to NumPy arrays for efficient calculations
            font_database = {name: np.array(features, dtype=np.float32) for name, features in data.items()}
            print(f"Successfully loaded font database with {len(font_database)} fonts.")
            return font_database
        except (pickle.UnpicklingError, EOFError, ImportError, IndexError) as e:
            raise Exception(f"Error loading or parsing the font database file: {e}")

    @staticmethod
    def _calculate_target_vector(character_features: List[np.ndarray]) -> Optional[np.ndarray]:
        """
        Averages the feature vectors of all characters from a snip.

        Args:
            character_features: A list of NumPy arrays, where each array is the
                                feature vector for a single recognized character.

        Returns:
            A single NumPy array representing the average feature vector for the snip,
            or None if the input list is empty.
        """
        if not character_features:
            return None

        # Ensure all vectors have the same length before averaging
        try:
            first_vector_len = len(character_features[0])
            if not all(len(vec) == first_vector_len for vec in character_features):
                # This indicates an issue in the feature extraction pipeline.
                print("Warning: Inconsistent feature vector lengths detected. Filtering.")
                character_features = [vec for vec in character_features if len(vec) == first_vector_len]
                if not character_features:
                    return None
        except IndexError:
            return None # Should not happen if list is not empty, but for safety.

        return np.mean(np.array(character_features), axis=0)

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculates the cosine similarity between two vectors.

        Args:
            vec1: The first vector.
            vec2: The second vector.

        Returns:
            The cosine similarity, a value between -1 and 1. Returns 0.0 if a norm is zero.
        """
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)

        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0

        return float(dot_product / (norm_vec1 * norm_vec2))

    def find_best_matches(self, character_features: List[np.ndarray], top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Finds the top N font matches for a given set of character features.

        Args:
            character_features: A list of feature vectors for characters from the snip.
            top_n: The number of best matches to return.

        Returns:
            A sorted list of tuples, where each tuple contains:
            (font_name: str, similarity_score: float).
            The list is sorted by similarity score in descending order.
            Returns an empty list if no valid characters were provided or no match could be made.
        """
        if not self.font_database:
            print("Warning: Font database is empty. Cannot perform matching.")
            return []

        target_vector = self._calculate_target_vector(character_features)

        if target_vector is None:
            print("Info: No valid character features to create a target vector.")
            return []

        # Ensure target vector has the same dimension as database vectors
        # Get a sample vector from the database to check dimension
        sample_db_vector = next(iter(self.font_database.values()))
        if len(target_vector) != len(sample_db_vector):
            print(f"Error: Target vector dimension ({len(target_vector)}) does not match "
                  f"database vector dimension ({len(sample_db_vector)}).")
            return []

        scores = []
        for font_name, db_vector in self.font_database.items():
            similarity = self._cosine_similarity(target_vector, db_vector)
            scores.append((font_name, similarity))

        # Sort by similarity score (the second element of the tuple) in descending order
        scores.sort(key=lambda item: item[1], reverse=True)

        return scores[:top_n]


if __name__ == '__main__':
    # Example usage and basic test for the FontMatcher class.
    # This requires a dummy 'font_features.pkl' to be created.

    # 1. Create a dummy database for testing
    print("Creating a dummy font database for testing...")
    dummy_db = {
        'Arial.ttf': np.array([0.8, 0.5, 0.2, 0.9]),      # High aspect ratio, low holes
        'Times New Roman.ttf': np.array([0.6, 0.6, 0.8, 0.3]), # Medium aspect, high holes
        'Courier New.ttf': np.array([1.0, 0.4, 0.1, 0.1]),   # Monospaced, very low holes
        'Comic Sans MS.ttf': np.array([0.7, 0.7, 0.7, 0.8]) # A mix
    }

    # Create a dummy data directory if it doesn't exist
    # Assumes this script is run from src/matching/
    dummy_data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    os.makedirs(dummy_data_dir, exist_ok=True)
    dummy_db_path = os.path.join(dummy_data_dir, 'font_features.pkl')

    with open(dummy_db_path, 'wb') as f:
        pickle.dump(dummy_db, f)
    print(f"Dummy database saved to '{dummy_db_path}'")

    # 2. Initialize the matcher
    try:
        matcher = FontMatcher(db_path=dummy_db_path)

        # 3. Simulate features extracted from a snip
        # These features should be very close to Arial's features
        snip_char_features = [
            np.array([0.81, 0.52, 0.19, 0.88]),
            np.array([0.79, 0.48, 0.21, 0.92]),
            np.array([0.80, 0.50, 0.20, 0.90])
        ]

        # 4. Find the best matches
        print("\nFinding matches for a snip resembling 'Arial'...")
        top_matches = matcher.find_best_matches(snip_char_features, top_n=3)

        # 5. Display results
        if top_matches:
            print("Top 3 matches found:")
            for i, (font, score) in enumerate(top_matches):
                print(f"{i+1}. Font: {os.path.basename(font)}, Similarity: {score:.4f}")

            # Check if the top match is Arial as expected
            assert os.path.basename(top_matches[0][0]) == 'Arial.ttf'
            print("\nTest passed: Top match is 'Arial.ttf' as expected.")
        else:
            print("No matches found.")
            print("\nTest failed.")

        # Test with empty features
        print("\nTesting with empty character features...")
        no_matches = matcher.find_best_matches([])
        assert not no_matches
        print("Test passed: Correctly returned no matches for empty input.")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Clean up the dummy file
        if os.path.exists(dummy_db_path):
            os.remove(dummy_db_path)
            print(f"\nCleaned up dummy database file: '{dummy_db_path}'")
```