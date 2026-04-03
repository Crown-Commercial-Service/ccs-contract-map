from src.core.classification_v2 import contract_mapper_v2  # Assuming this is async or has run_sync
from src.core.classification_v5 import HeuristicClassifier


async def keywords_and_llm(description: str):
    # 1. Initialize and run the fast Synchronous Classifier
    classifier = HeuristicClassifier()
    result, score = classifier.classify(description)

    # 2. Check the threshold
    if result and score >= 15:
        print(f"✅ Keywords chosen. Heuristic score: {score}")
        return result, f"Heuristic Match (Score: {score})"

    # 3. Fallback to the Asynchronous LLM/RAG
    print(f"❌ Score {score} below threshold. Falling back to RAG...")

    # If contract_mapper_v3 is async, use await.
    # If it uses PydanticAI's .run_sync(), you can call it directly.
    result = await contract_mapper_v2(description)

    return result, "LLM was used"