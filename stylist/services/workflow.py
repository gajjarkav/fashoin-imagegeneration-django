from .gemini import GeminiService
from .azure_openai import AzureOpenAIService
from .image_router import ImageRouter
import logging

logger = logging.getLogger("stylist")

class WorkflowService:

    def __init__(self):
        self.gemini = GeminiService()
        self.azure = AzureOpenAIService()
        self.image_router = ImageRouter()

    def run_analysis(self, upload):
        try:
            return self.gemini.analyze_clothing(upload.original_image.path)
        except Exception as e:
            logger.warning(f"Gemini failed during analysis ({e}). Falling back to Azure OpenAI.")
            return self.azure.analyze_clothing(upload.original_image.path)

    def run_style_planner(self, analysis_json):
        try:
            return self.gemini.generate_style_plan(analysis_json)
        except Exception as e:
            logger.warning(f"Gemini failed during style planning ({e}). Falling back to Azure OpenAI.")
            return self.azure.generate_style_plan(analysis_json)

    def run_refinement(
        self,
        upload,
        recommendation_json,
        user_prompt,
    ):
        # 1. Ask the analyzer to generate the refined JSON plan (Gemini -> Azure fallback)
        try:
            updated_plan = self.gemini.generate_refined_plan(recommendation_json, user_prompt)
        except Exception as e:
            logger.warning(f"Gemini failed during plan refinement ({e}). Falling back to Azure OpenAI.")
            updated_plan = self.azure.generate_refined_plan(recommendation_json, user_prompt)
        
        # 2. Ask the configured image router to apply the image edit (FLUX)
        return self.image_router.provider.refine_outfit(
            upload.original_image.path,
            updated_plan,
            user_prompt,
        )