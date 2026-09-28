"""
Prompt templates for outfit image generation / editing.

There are two prompt builders:

  build_outfit_edit_prompt  -- for Gemini instruction-following editors.
  build_flux_prompt         -- for Azure FLUX.2-pro (descriptive caption only).

Why two styles?
---------------
Gemini's image editor understands step-by-step edit instructions.
FLUX.2-pro is a diffusion model; it generates images from descriptive
captions. Sending instruction-style text ("Edit this photo and follow EVERY
step", "Do NOT crop", "Negative:") to FLUX also triggers Azure's RAI
content-safety filter (BingBlockList_Prompt) because the framing resembles
prompt-injection / jailbreak patterns.

The FLUX prompt must be:
  * A positive, descriptive caption of the TARGET image.
  * No imperative commands, no negations, no numbered steps.
  * Short enough to stay within Azure's token budget.
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


def build_flux_prompt(styling_plan: dict) -> str:
    """
    Ultra-minimal fashion-only caption for Azure FLUX.2-pro.

    Rules:
    - NO person/identity references ("same person", "reference image",
      "person's face") — these trigger Azure's BingBlockList identity filter.
    - NO imperative commands — triggers jailbreak filter.
    - ONLY describe the clothing and scene in positive fashion-editorial terms.
    """
    plan = styling_plan or {}

    bottom      = _as_text(plan.get("bottom"))      or "casual trousers"
    footwear    = _as_text(plan.get("footwear"))    or "sneakers"
    accessories = _as_text(plan.get("accessories"))
    bag         = _as_text(plan.get("bag"))
    jewelry     = _as_text(plan.get("jewelry"))
    theme       = _as_text(plan.get("theme"))       or "casual"

    items = [bottom, footwear]
    if accessories:
        items.append(accessories)
    if bag:
        items.append(bag)
    if jewelry:
        items.append(jewelry)
    items_str = ", ".join(i for i in items if i)

    return (
        f"Fashion editorial photo, "
        f"full body outfit: {items_str}, "
        f"{theme} style, "
        f"photorealistic, studio lighting, sharp focus."
    )
