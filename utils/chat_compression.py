
def compress_chat(history, max_messages=5):
    relevant = history[-max_messages:]
    lines = []
    for msg in relevant:
        lines.append(f"User: {msg['user']}\nBot: {msg['bot']}")
    return "\n".join(lines)
