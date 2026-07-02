from .gemini import GeminiService
from .image_router import ImageRouter


class WorkflowService:

    def __init__(self):

        self.gemini = GeminiService()
        self.image_router = ImageRouter()

    def run_analysis(self, upload):
        return self.gemini.analyze_clothing(
            upload.original_image.path,
        )

    def run_style_planner(self, analysis_json):
        return self.gemini.generate_style_plan(
            analysis_json,
        )

    def run_refinement(
        self,
        upload,
        recommendation_json,
        user_prompt,
    ):
        return self.gemini.refine_outfit(
            upload.original_image.path,
            recommendation_json,
            user_prompt,
        )