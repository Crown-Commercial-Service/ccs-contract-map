from src.core.classification_v3 import contract_mapper_v3
from src.core.classification_v5 import  HeuristicClassifier


def keywords_and_llm(description):
    classifier = HeuristicClassifier()
    result, score  = classifier.classify(description)

    if score >= 15:
        print("Keywords chosen this was the heuristic score", score)
        return result, score
    else:
        print("RAG chosen")
        result, reason = contract_mapper_v3(description)
        return result, None