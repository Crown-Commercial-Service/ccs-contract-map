import json
import re
from pathlib import Path

path = Path(__file__).parents[2] / "semantic_anchors2.json"


class HeuristicClassifier:
    def __init__(self, registry_path: Path = None):
        self.registry_path = registry_path
        if registry_path is None:
            self.registry_path = path
        self.registry = self._load_registry()

    def _load_registry(self):
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

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

        for category, keywords in self.registry.items():
            primary_list = keywords[0]
            secondary_list = keywords[1]

            score = 0

            # Check Primary Keywords (High Signal)
            for word in primary_list:
                # \b ensures we match exact words only
                if re.search(rf"\b{re.escape(word.lower())}\b", desc_lower):
                    if word.lower().startswith("rm"):
                        score += 50  # Instant win
                    else:
                        score += 5

            # Check Secondary Keywords (Supporting Context)
            for word in secondary_list:
                if re.search(rf"\b{re.escape(word.lower())}\b", desc_lower):
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

        # # Find the category with the highest score
        # best_category = max(category_scores, key=category_scores.get)
        # max_score = category_scores[best_category]
        # print(max_score)
        #
        # # Only return a match if it meets your confidence threshold
        # if max_score >= threshold:
        #     return best_category, max_score
        #
        # return None, max_score


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
