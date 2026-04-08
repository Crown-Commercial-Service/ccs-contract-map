from src.core.classification_v2 import contract_mapper_v2
from src.core.classification_v5 import HeuristicClassifier

# Initialize ONCE at the module level (Global)
# This loads the JSON into memory only once when the app starts
GLOBAL_CLASSIFIER = HeuristicClassifier()

async def keywords_and_llm(description: str):
    # 1. Use the pre-loaded global classifier
    # We pass the threshold (25) and margin (6) directly to the method
    result, score = GLOBAL_CLASSIFIER.classify(description, threshold=15, margin=6)

    # 2. Check the result
    # If 'result' is None, it means the score was too low OR it was a 'Tie'
    if result:
        print(f"✅ Keywords chosen. Heuristic score: {score}")
        return result, f"Heuristic Match (Score: {score})"

    # 3. Fallback to the Asynchronous LLM/RAG
    # This only happens if result is None (Low score or Ambiguous)
    print(f"❌ Confidence too low (Score: {score}). Falling back to RAG...")

    result_llm = await contract_mapper_v2(description)

    return result_llm, f"LLM used"
# from src.core.classification_v2 import contract_mapper_v2  # Assuming this is async or has run_sync
# from src.core.classification_v5 import HeuristicClassifier
#
#
# async def keywords_and_llm(description: str):
#     # 1. Initialize and run the fast Synchronous Classifier
#     classifier = HeuristicClassifier()
#     result, score = classifier.classify(description)
#
#     # 2. Check the threshold
#     if result and score >= 25:
#         print(f"✅ Keywords chosen. Heuristic score: {score}")
#         return result, f"Heuristic Match (Score: {score})"
#
#     # 3. Fallback to the Asynchronous LLM/RAG
#     print(f"❌ Score {score} below threshold. Falling back to RAG...")
#
#
#     result = await contract_mapper_v2(description)
#
#     return result, "LLM was used"