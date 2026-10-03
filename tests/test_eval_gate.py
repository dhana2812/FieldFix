import os
import json
import pytest

def test_eval_benchmark_integrity():
    """
    Step 10 Evaluation Harness Integrity Gate:
    Verifies that eval_set.json contains at least 10 questions with valid required facts.
    """
    eval_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "eval_set.json")
    assert os.path.exists(eval_file), "eval_set.json benchmark file must exist"
    
    with open(eval_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert isinstance(data, list)
    assert len(data) >= 10, f"Benchmark must have at least 10 questions, found {len(data)}"
    
    total_facts = 0
    for idx, item in enumerate(data, 1):
        assert "id" in item, f"Item {idx} missing 'id'"
        assert "question" in item, f"Item {idx} missing 'question'"
        assert "required_facts" in item, f"Item {idx} missing 'required_facts'"
        assert len(item["required_facts"]) > 0, f"Item {item['id']} has empty required_facts"
        total_facts += len(item["required_facts"])
        
    assert total_facts >= 20, f"Benchmark must have >= 20 total facts, found {total_facts}"

def test_fact_recall_matching_logic():
    """Verifies case-insensitive string matching logic for required facts."""
    retrieved_content = (
        "Amperia DC-150 Fast Charger Technical Manual. "
        "SiC Power modules carry a 5 Years (60 Months) warranty. "
        "Liquid-cooled CCS2 charging cables carry 2 Years warranty."
    )
    
    required_facts = ["5 Years", "60 Months", "2 Years", "Non-Existent Fact"]
    
    hits = [fact for fact in required_facts if fact.lower() in retrieved_content.lower()]
    assert len(hits) == 3
    assert "Non-Existent Fact" not in hits
