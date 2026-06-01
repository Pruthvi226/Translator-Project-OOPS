"""
Grammar correction before translation. Uses language-tool or placeholder.
"""

import logging

logger = logging.getLogger(__name__)


class GrammarModel:
    """
    Corrects grammar in the given text. Uses LanguageTool if available.
    """

    def __init__(self):
        self._tool = None

    def _get_tool(self):
        if self._tool is not None:
            return self._tool
        try:
            import language_tool_python
            self._tool = language_tool_python.LanguageTool("en-US")
            return self._tool
        except Exception as e:
            logger.debug("LanguageTool not available: %s", e)
            return None

    def correct(self, text: str) -> str:
        """
        Apply grammar corrections. Returns corrected text.
        If no grammar tool available, returns original text.
        """
        tool = self._get_tool()
        if tool is None:
            return text
        try:
            corrected = tool.correct(text)
            return corrected
        except Exception as e:
            logger.warning("Grammar correction failed: %s", e)
            return text
