"""
Test category text wrapping at 18 characters
"""

def wrap_category_text(text: str, max_length: int = 18) -> str:
    """
    Wrap category text to fit within max_length per line.
    Breaks on word boundaries to avoid splitting words.

    Args:
        text: Text to wrap
        max_length: Maximum characters per line (default 18)

    Returns:
        Text with newlines inserted at appropriate positions
    """
    if len(text) <= max_length:
        return text

    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        # Check if adding this word would exceed the limit
        word_length = len(word)
        space_length = 1 if current_line else 0  # Space before word (if not first word)

        # Wrap if adding this word would make line >= max_length (18 or more chars)
        if current_line and current_length + space_length + word_length >= max_length:
            # Start new line
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = word_length
        else:
            # Word fits on current line
            current_line.append(word)
            current_length += space_length + word_length

    # Add remaining words
    if current_line:
        lines.append(' '.join(current_line))

    return '\n'.join(lines)


# Test cases from the screenshot
test_categories = [
    "FRESH POULTRY PI",           # 17 chars - should NOT wrap
    "CANNED PROTEIN CONDIMENTS PASTA SOUP",  # 37 chars - should wrap
    "PRODUCE AND FLORAL",          # 19 chars - should wrap
    "BRANDED DELI PI",             # 16 chars - should NOT wrap
    "EXTREME VALUE GIFT CARDS",   # 25 chars - should wrap
    "FROZEN FOODS",                # 13 chars - should NOT wrap
    "COOLER",                      # 6 chars - should NOT wrap
    "PLANNING SOLUTIONS",          # 19 chars - should wrap
    "SODA",                        # 4 chars - should NOT wrap
    "AUDIO",                       # 5 chars - should NOT wrap
]

print("Testing Category Text Wrapping (18 char max per line)")
print("=" * 60)

for category in test_categories:
    wrapped = wrap_category_text(category, max_length=18)
    lines = wrapped.split('\n')

    print(f"\nOriginal: '{category}' ({len(category)} chars)")
    print(f"Wrapped:")
    for i, line in enumerate(lines, 1):
        print(f"  Line {i}: '{line}' ({len(line)} chars)")
        if len(line) > 18:
            print(f"    [FAIL] Line exceeds 18 characters!")

# Specific test case from screenshot
print("\n" + "=" * 60)
print("Testing specific examples from screenshot:")
print("=" * 60)

examples = {
    "CANNED PROTEIN CONDIMENTS PASTA SOUP": "CANNED PROTEIN\nCONDIMENTS PASTA\nSOUP",
    "EXTREME VALUE GIFT CARDS": "EXTREME VALUE GIFT\nCARDS",
    "PRODUCE AND FLORAL": "PRODUCE AND\nFLORAL",
}

all_pass = True
for original, expected in examples.items():
    result = wrap_category_text(original, max_length=18)
    if result == expected:
        print(f"[PASS] '{original}' wrapped correctly")
        print(f"       Result: {repr(result)}")
    else:
        print(f"[FAIL] '{original}' wrapping mismatch")
        print(f"       Expected: {repr(expected)}")
        print(f"       Got:      {repr(result)}")
        all_pass = False

print("\n" + "=" * 60)
if all_pass:
    print("[SUCCESS] All wrapping tests passed!")
else:
    print("[WARNING] Some tests failed - review logic")
