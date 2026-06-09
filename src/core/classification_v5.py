import json
import re
from pathlib import Path

path = Path(__file__).parents[2] / "semantic_anchors.json"


class HeuristicClassifier:
    def __init__(self, registry_path: Path = None):
        self.registry_path = registry_path
        if registry_path is None:
            self.registry_path = path
        self.registry = self._load_registry()
        #precompile
        self.compiled_registry = self._precompile_registry()

    def _load_registry(self):
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _precompile_registry(self):
        """This does the Regex and scoring once rather than doing after each iteration."""
        compiled = {}
        for category, keywords in self.registry.items():
            primary_list = keywords[0]
            secondary_list = keywords[1]

            # Map strings to a tuple: (compiled_regex_object, points_to_award)
            compiled_primary = []
            for word in primary_list:
                pattern = re.compile(rf"\b{re.escape(word.lower())}\b")
                points = 50 if word.lower().startswith("rm") else 5
                compiled_primary.append((pattern, points))

            compiled_secondary = [
                re.compile(rf"\b{re.escape(word.lower())}\b") for word in secondary_list
            ]

            compiled[category] = (compiled_primary, compiled_secondary)
        return compiled

    def classify(self, description: str, threshold: int = 15, margin: int = 6):
        """
        Scores the description against each category.
        Primary match = 3 points
        Secondary match = 1 point
        """
        if not description:
            return None, 0

        desc_lower = description.lower()
        category_scores = {}

        # Loop through our pre-compiled patterns instantly in-memory
        for category, (primary_patterns, secondary_patterns) in self.compiled_registry.items():
            score = 0

            # Check Pre-compiled Primary Keywords
            for pattern, points in primary_patterns:
                if pattern.search(desc_lower):
                    score += points

            # Check Pre-compiled Secondary Keywords
            for pattern in secondary_patterns:
                if pattern.search(desc_lower):
                    score += 1

            category_scores[category] = score

        if not category_scores or sum(category_scores.values()) == 0:
            return None, 0

        # 3. Rank results to find the winner and the runner-up
        sorted_results = sorted(
            category_scores.items(), key=lambda x: x[1], reverse=True
        )

        best_cat, best_score = sorted_results[0]
        second_score = sorted_results[1][1] if len(sorted_results) > 1 else 0

        # --- CONFIDENCE LOGIC ---

        # Rule A: Must meet minimum threshold
        if best_score < threshold:
            return None, best_score

        # Rule B: Margin of Victory
        # If the gap between 1st and 2nd place is too small, it's ambiguous.
        if (best_score - second_score) < margin:
            # We return None so the async loop falls back to the LLM
            print(
                f"Ambiguity detected ({best_cat} {best_score} vs {second_score}). Forcing LLM."
            )
            return None, best_score

        return best_cat, best_score




# # --- Example Usage ---
# if __name__ == "__main__":
#     # Point to your generated JSON
#     path_new = Path(__file__).parents[2] / "semantic_anchors.json"
#     classifier = HeuristicClassifier(path_new)
#
#     test_description = "Pool water recovery systems and rainwater harvesting"
#
#     label, score = classifier.classify(test_description)
#
#     if label:
#         print(f"✅ Classified as: {label} (Score: {score})")
#     else:
#         print(f"❌ No confident match found. Fallback to RAG needed. (Best Score: {score})")
