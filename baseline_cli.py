#!/usr/bin/env python3
"""
FieldFix - Baseline CLI (No RAG / Zero Context)
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.llm import LLMClient

def main():
    print("=" * 65)
    print("⚡ FieldFix Baseline CLI (Zero-Context LLM) ⚡")
    print("Type your question below or type 'exit' / 'quit' to end.")
    print("=" * 65)
    
    system_prompt = "You are FieldFix, a copilot for Amperia field technicians."
    llm = LLMClient()
    
    while True:
        try:
            query = input("\n[Technician Query] > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("Exiting baseline CLI. Goodbye!")
                break
                
            print(f"\nQuerying {llm.model} ({llm.provider})...")
            res = llm.generate(system_prompt=system_prompt, user_prompt=query, temperature=0.0)
            
            print("\n" + "-" * 50)
            print("🤖 [FieldFix Baseline Response]:")
            print(res["text"])
            print("-" * 50)
            print(f"📊 Latency: {res['latency_ms']}ms | Tokens: {res['total_tokens']}")
            
        except KeyboardInterrupt:
            print("\nExiting baseline CLI. Goodbye!")
            break
        except Exception as e:
            print(f"\n[Error] {str(e)}")

if __name__ == "__main__":
    main()
