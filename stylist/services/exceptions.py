class GeminiServiceError(Exception):
    """Base Gemini exception"""

class ClothingAnalysisError(GeminiServiceError):
    """Clothing analysis"""

class StylePlanningError(GeminiServiceError):
    """Style planner failed"""

class ImageGenerationError(GeminiServiceError):
    """Image generation failed"""

class GeminiUnavailableError(GeminiServiceError):
    """Gemini API rate limit exceeded"""

class GeminiResponseError(GeminiServiceError):
    """Invalid respose returnde by Gemini"""