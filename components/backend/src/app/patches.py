import logging
import httpx

logger = logging.getLogger(__name__)

def apply_gradio_upload_patch():
    """
    Forces a global timeout on ALL httpx requests.
    This fixes the issue where gradio_client uses internal client instances
    that ignore module-level patches.
    """
    # Check if already patched to avoid recursion/double-patching
    if getattr(httpx.Client, "_is_patched", False):
        return

    # Save the original method
    _original_request = httpx.Client.request

    def _patched_request(self, method, url, **kwargs):
        # 1. Force a long timeout for everything (10 minutes)
        if "timeout" not in kwargs:
            kwargs["timeout"] = 600.0

        # 2. Call the original method
        return _original_request(self, method, url, **kwargs)

    # Apply the patch to the Class itself
    httpx.Client.request = _patched_request
    httpx.Client._is_patched = True

    logger.info("Nuclear Monkey Patch applied: All httpx.Client requests now have 600s timeout.")
