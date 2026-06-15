def normalize_text(text: str) -> str:
    return text.strip()


def split_command(raw_text: str) -> tuple[str, str]:
    cleaned_text = normalize_text(raw_text)

    if not cleaned_text:
        return "/empty", ""

    parts = cleaned_text.split(maxsplit=1)
    command = parts[0]
    content = parts[1] if len(parts) > 1 else ""

    if not command.startswith("/"):
        return "/unknown", cleaned_text

    return command, content
