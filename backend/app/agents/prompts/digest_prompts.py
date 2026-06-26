from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text()


def get_digest_prompt(content: str, url: str, source_title: str, source_type: str) -> str:
    template = load_prompt("digest_generator_v1.txt")
    return template.format(content=content, url=url, source_title=source_title, source_type=source_type)


def get_tool_extract_prompt(content: str) -> str:
    template = load_prompt("tool_extractor_v1.txt")
    return template.format(content=content)
