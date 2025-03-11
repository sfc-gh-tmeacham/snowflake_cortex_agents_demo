def remove_duplicate_headers(text: str) -> str:
    """
    Remove duplicate header lines from text.
    
    A header is any line starting with '#' (after stripping leading whitespace).
    For any header that appears more than 3 times in the text (ignoring differences
    in surrounding whitespace or extra '#' characters), only the second occurrence is kept.
    Headers that occur 3 times or less are left unchanged.
    
    Args:
        text: The input text containing header lines.
    
    Returns:
        A new string with duplicate headers removed, keeping only the second occurrence
        for headers that appear more than 3 times.
    """
    # Split text into lines.
    lines = text.splitlines()
    
    # Count each header occurrence (normalized by stripping leading '#' and whitespace)
    header_counts = {}
    for line in lines:
        if line.lstrip().startswith('#'):
            normalized = line.lstrip().lstrip('#').strip()
            header_counts[normalized] = header_counts.get(normalized, 0) + 1

    # Rebuild the text, but for headers that occur more than 3 times, only output the second occurrence.
    seen = {}
    output_lines = []
    for line in lines:
        if line.lstrip().startswith('#'):
            normalized = line.lstrip().lstrip('#').strip()
            if header_counts[normalized] > 3:
                seen[normalized] = seen.get(normalized, 0) + 1
                # Only keep the second occurrence.
                if seen[normalized] == 2:
                    output_lines.append(line)
                # Else: skip this header occurrence.
            else:
                output_lines.append(line)
        else:
            output_lines.append(line)
    
    return "\n".join(output_lines)