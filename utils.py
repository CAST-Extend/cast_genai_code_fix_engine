from datetime import datetime
import secrets
import string

def get_timestamp():
    """Return a formatted timestamp string."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def generate_unique_alphanumeric(length=24):
    """Generate a secure random alphanumeric string."""
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))

async def log_safe(logger, func_name: str, exception: Exception):
    """Async-safe error logging utility."""
    if logger:
        try:
            await logger.log_error(func_name, exception)
        except Exception as log_err:
            print(f"[Logger Failed] {log_err}")
    print(f"[{func_name}] Error: {exception}")

def replace_lines(app_logger, lines, replacements):
    """
    Replace specific line ranges with replacement lines.

    Args:
        app_logger: Logger object.
        lines (list): Original lines.
        replacements (dict): Dict of {(start, end): [new lines]}.

    Returns:
        list: Modified lines.
    """
    try:
        modified_lines = lines[:]
        for (start, end), replacement_lines in sorted(replacements.items(), reverse=True):
            modified_lines[int(start) - 1:int(end)] = replacement_lines
        return modified_lines
    except Exception as e:
        print(f"An error occurred during replace_lines: {e}")
        if app_logger:
            try:
                app_logger.log_error("replace_lines", e)
            except Exception as log_err:
                print(f"[Logger Failed] {log_err}")
        return lines  # fail-safe fallback
