
def human_readable_size(size_in_bytes):
    """Converts bytes to KB, MB, GB."""
    try:
        size = float(size_in_bytes)
    except (ValueError, TypeError):
        return "-"
        
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"