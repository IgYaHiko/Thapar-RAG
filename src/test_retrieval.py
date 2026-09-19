from src.rag_chain_utils import retrieve

for q in [
    "minimum attendance for end semester exams",
    "hostel gate timing",
    "library location",
]:
    print(f"\n❓ {q}")
    print("-" * 60)
    results = retrieve(q, k=5)
    if not results:
        print("  ❌ No results above min_score threshold")
    for r in results:
        print(f"  {r['score']:.3f}  {r['source'][:80]}")
        print(f"        {r['text'][:100]}...")