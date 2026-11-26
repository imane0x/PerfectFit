"""Command-line chat for quick testing: python chat.py"""
import logging

from src.assistant import get_assistant

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    assistant = get_assistant()
    print("Let's chat! (type 'quit' to exit)")
    while True:
        sentence = input("You: ")
        if sentence.strip().lower() == "quit":
            break
        turn = assistant.ask(sentence)
        print("PerfectFit:", turn.answer)
        for p in turn.products:
            print("  -", p.title, f"({p.id})")
