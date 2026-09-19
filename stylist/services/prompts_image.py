"""
Prompt templates for outfit image generation / editing.

WHY THIS FILE WAS REWRITTEN
---------------------------
The old IMAGE_SYSTEM_PROMPT told the image model:

    "The uploaded clothing item MUST remain unchanged.
     Never modify: color, logo, print, graphics, text, fabric, texture.
     The clothing item must be exactly the same as the uploaded image."

Instruction-following editors (Gemini "Nano Banana" gemini-2.5-flash-image,
FLUX Kontext / FLUX 2 Pro img2img, Pruna p-image-edit ...) take that
literally: the safest edit that satisfies "change nothing" is to return the
input photo untouched (at most swapping the background). That is exactly the
behaviour reported in the bug: every "generated" image looks like the input.

On top of that the styling plan was injected as raw JSON. Diffusion models
(SD3 img2img) do not understand JSON or instructions - they rendered the
listed items ("white sneakers", ...) as floating props in the background
instead of putting them on the person (also visible in the bug screenshots).

The prompts below are written as explicit EDIT INSTRUCTIONS:
  * keep identity + the hero garment,
  * but re-frame to full body,
  * MAKE THE PERSON WEAR every new item,
  * and replace the background.
"""


def _as_text(value) -> str:
    """Render a plan field (string or list) as plain text."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v).strip() for v in value if str(v).strip())
    return str(value).strip()


def build_outfit_edit_prompt(styling_plan: dict) -> str:
    """
    Prompt for instruction-following image editors.

    Accepts one outfit dict from the style planner:
    {theme, bottom, footwear, accessories, bag, jewelry, reason}
    """
    plan = styling_plan or {}

    bottom = _as_text(plan.get("bottom")) or "smart casual trousers"
    footwear = _as_text(plan.get("footwear")) or "clean minimalist sneakers"
    accessories = _as_text(plan.get("accessories")) or "a simple wrist watch"
    bag = _as_text(plan.get("bag"))
    jewelry = _as_text(plan.get("jewelry"))
    theme = _as_text(plan.get("theme")) or "casual"
    reason = _as_text(plan.get("reason"))

    worn = [
        f"- Bottom (worn on the legs): {bottom}",
        f"- Footwear (worn on the feet): {footwear}",
        f"- Accessories (worn/used by the person): {accessories}",
    ]
    if bag:
        worn.append(f"- Bag (carried by the person): {bag}")
    if jewelry:
        worn.append(f"- Jewelry (worn by the person): {jewelry}")

    worn_block = "\n".join(worn)

    return f"""You are a professional fashion photographer retouching a client's photo.

The attached photo shows a person wearing one garment (the "hero garment").

Edit this photo and follow EVERY step:

1. SAME PERSON - identical face, hair, skin tone, expression and pose.
2. SAME HERO GARMENT - the top the person already wears keeps its exact colour, print, logo, fabric and shape.
3. RE-FRAME TO FULL BODY - zoom out / extend the canvas so the person is visible head-to-toe in a 3:4 portrait. Do NOT crop at the waist.
4. DRESS THE PERSON head-to-toe. Every item below must be WORN or carried by the person, never lying or floating in the scene:
{worn_block}
5. NEW BACKGROUND - completely replace the original background with a realistic scene that matches the theme "{theme}".
6. LOOK - photorealistic editorial fashion photograph, natural proportions, correct anatomy, feet planted on the ground, professional lighting, sharp focus.

Negative: do not keep the original background, do not leave shoes or clothing next to the person, no floating objects, no extra people, no watermark.

Styling note: {reason}"""


def build_outfit_caption(styling_plan: dict) -> str:
    """
    Flat descriptive caption for plain diffusion img2img models (SD3/SDXL).

    These models ignore instructions and JSON, so we describe the TARGET
    image in one sentence instead.
    """
    plan = styling_plan or {}

    bottom = _as_text(plan.get("bottom")) or "smart casual trousers"
    footwear = _as_text(plan.get("footwear")) or "clean minimalist sneakers"
    accessories = _as_text(plan.get("accessories"))
    theme = _as_text(plan.get("theme")) or "casual"

    caption = (
        "Full-body photorealistic editorial fashion photograph, 3:4 portrait, "
        "of the same person wearing the same top as in the reference image, "
        f"styled head-to-toe with {bottom}, {footwear}"
    )
    if accessories:
        caption += f", {accessories}"
    caption += (
        f", standing in a realistic {theme} setting, professional lighting, "
        "correct anatomy, sharp focus, high detail"
    )
    return caption
