import traceback
import datetime
from utils.logger import get_logger

logger = get_logger("karaparty.error")

def report_error(error: Exception, context: str = None):
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    error_type = type(error).__name__
    tb = traceback.format_exc()

    context_str = context or "No context"

    # Build message
    log_message = (
        f"\n\n"
        f"[{timestamp}] ⚠️ Error occurred\n"
        f"Type: {error_type}\n"
        f"Context: {context_str}\n"
        f"Message: {str(error)}\n"
        f"Traceback:\n{tb}"
        f"\n"
    )

    # Log it to file
    logger.error(log_message)

    # Print a user-friendly error to screen
    print(f"❌ ERROR in context: {context_str}")
    print(f"   → {error_type}: {error}")
