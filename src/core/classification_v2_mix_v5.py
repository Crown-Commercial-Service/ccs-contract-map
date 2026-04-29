from src.core.classification_v2 import contract_mapper_v2
from src.core.classification_v5 import HeuristicClassifier


GLOBAL_CLASSIFIER = HeuristicClassifier()

async def keywords_and_llm(description: str, threshold: int, margin: int):

    result, score = GLOBAL_CLASSIFIER.classify(description, threshold=threshold, margin=margin)

    # 2. Check the result
    # If 'result' is None, it means the score was too low OR it was a 'Tie'
    if result:
        print(f"✅ Keywords chosen. Heuristic score: {score}")
        return result, f"Heuristic Match (Score: {score})"

    # 3. Fallback to the Asynchronous LLM
    # This only happens if result is None (Low score or Ambiguous due to margin being too close)
    print(f"❌ Confidence too low (Score: {score}). Falling back to LLM...")

    result_llm = await contract_mapper_v2(description)

    return result_llm, f"LLM used"