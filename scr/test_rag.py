from rag.search import search, format_context

def main():
    q = "battery failed after 8 months, is it covered and what do we do?"
    hits = search(q, k=4)
    print("QUERY:", q)
    print("\nHITS:")
    for i, h in enumerate(hits, 1):
        print(f"{i}. score={h.score:.3f} cite={h.cite()}")

    print("\nCONTEXT BLOCK:\n")
    print(format_context(hits))

if __name__ == "__main__":
    main()
