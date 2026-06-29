import os
import sys
import json
import shutil
from datetime import datetime
from modules.constants import (
    STYLE_MAPPING,
    SCENE_MAPPING,
    CHARACTER_TYPE_HINTS,
    COLOR_MOOD_MAPPING,
    BACKGROUND_TYPE_MAPPING,
    NEGATIVE_PROMPT,
    GRID_CONFIG,
    DEFAULT_GRID_SIZE,
)

def build_static_prompt(character, style_desc, expressions, reference_image="", background_type="transparent", grid_size=None):
    grid_size = grid_size or DEFAULT_GRID_SIZE
    config = GRID_CONFIG.get(grid_size, GRID_CONFIG[DEFAULT_GRID_SIZE])
    rows = config["rows"]
    cols = config["cols"]
    total_frames = config["total_frames"]
    layout_desc = config["layout_desc"]
    
    background_desc = BACKGROUND_TYPE_MAPPING.get(background_type, BACKGROUND_TYPE_MAPPING["transparent"])
    prompt_lines = [
        f"A character sticker sheet featuring exactly {total_frames} different expressions arranged in a {layout_desc} on a single seamless canvas. Do NOT draw any grid lines.",
        "",
        f"CRITICAL: You MUST draw exactly {total_frames} ({['NINE', 'SIXTEEN'][grid_size == 16]}) character poses in this single image, arranged in a {layout_desc}. Each cell contains one sticker with a different expression.",
        "",
        f"Character: {character}",
        f"Art Style: {style_desc}",
        "",
        "=== CRITICAL LAYOUT REQUIREMENTS ===",
        f"1. CANVAS: Perfect square (1:1 aspect ratio, 1024x1024 pixels total), logically divided into {layout_desc}={total_frames} equal areas, but visually completely seamless.",
        "2. SCENE ALIGNMENT: Each area is a separate camera view. The character should be naturally framed within its area. Do NOT rigidly force the character to the exact mathematical center if the pose (e.g., sitting vs standing) dictates otherwise. Keep a consistent baseline floor.",
        "3. SIZE: Character (including all limbs, hair, accessories) must stay within 70% of each area, leaving at least 15% safe margin on ALL FOUR sides to prevent cutting off during slicing.",
        "4. NO OVERLAP: Absolutely no character parts, hair, limbs, shadows, or text may cross into adjacent areas. Each area is completely independent.",
        "5. ABSOLUTELY NO BORDERS: No visible borders, frames, grid lines, dividers, or dividing boxes between characters. The characters must float on a single, uninterrupted, perfectly clean background.",
        "",
        f"Background: {background_desc}",
    ]
    if reference_image:
        prompt_lines.append(f"Character Reference: Use the provided reference image to accurately draw the exact same character (same shape, colors, features, and overall design) across all {total_frames} frames.")

    prompt_lines.append("")
    prompt_lines.append(f"=== EXPRESSIONS ({rows} rows × {cols} columns, each centered in its cell) ===")
    for i, exp in enumerate(expressions):
        if i >= total_frames: break
        t = exp.get('text', '')
        if not t.strip(): t = "WOW!"
        prompt_lines.append(f"Cell {i+1}: Action: {exp.get('action', '')}. Text overlay: \"{t}\" - use highly creative typography matching the emotion. Pick vibrant text colors and distinct bold outlines. TEXT GROUPING: Keep all letters tightly grouped together as a single block without scattering. Position it playfully inside this cell's boundaries without cutting off.")

    prompt_lines.append("")
    prompt_lines.append("=== NEGATIVE CONSTRAINTS (STRICTLY AVOID) ===")
    prompt_lines.append(NEGATIVE_PROMPT)

    return "\n".join(prompt_lines)

def build_animated_prompt(character, style_desc, action, text_overlay, reference_image="", background_type="transparent", grid_size=None):
    grid_size = grid_size or DEFAULT_GRID_SIZE
    config = GRID_CONFIG.get(grid_size, GRID_CONFIG[DEFAULT_GRID_SIZE])
    rows = config["rows"]
    cols = config["cols"]
    total_frames = config["total_frames"]
    layout_desc = config["layout_desc"]
    
    background_desc = BACKGROUND_TYPE_MAPPING.get(background_type, BACKGROUND_TYPE_MAPPING["transparent"])
    if not text_overlay or not str(text_overlay).strip():
        text_overlay = f"{str(action).split()[0].upper()}!"

    prompt_lines = [
        f"A {total_frames}-frame animation sprite sheet arranged in {rows} rows and {cols} columns on a single seamless canvas. Do NOT draw any grid lines.",
        "",
        f"CRITICAL: You MUST draw exactly {total_frames} ({['NINE', 'SIXTEEN'][grid_size == 16]}) character poses in this single image, arranged in a {layout_desc}. Each cell contains one frame of the animation.",
        "",
        f"IMPORTANT: These {total_frames} frames will be sliced and played sequentially as a GIF animation. Each frame MUST show the character at a DIFFERENT moment of the action, with progressive changes. Do NOT draw {total_frames} identical poses - each frame should advance the animation slightly.",
        "",
        f"Character: {character}",
        f"Art Style: {style_desc}",
        f"Animation: A smooth {total_frames}-frame sequence of '{action}'.",
        "",
        "=== CRITICAL LAYOUT REQUIREMENTS ===",
        f"1. CANVAS: Perfect square (1:1 aspect ratio, 1024x1024 pixels total), logically divided into exactly {layout_desc}={total_frames} equal areas, but visually completely seamless.",
        "2. ANIMATION SPACE: Treat each area as a consistent fixed camera framing a fixed ground plane. The character must move NATURALLY within this space.",
        "3. NATURAL VERTICAL MOVEMENT: Crucially, if the action involves jumping, flying, or raising up, the character's body MUST be drawn physically higher within that specific frame's area compared to a standing frame. Do NOT artificially lock the character's center of mass to the center of every frame, otherwise the animation will not show vertical displacement.",
        "4. SIZE LIMIT: Character (including all limbs, hair, accessories, and motion effects) must stay within 70% of each area. This means at least 15% empty background margin on ALL FOUR sides of every area.",
        "5. NO OVERLAP: No character parts, hair, limbs, shadows, text, or motion lines may cross the invisible boundary into adjacent areas.",
        "6. ABSOLUTELY NO BORDERS: No visible borders, frames, grid lines, dividers, or dividing boxes between frames. The sequence must be drawn on a single, uninterrupted, perfectly clean background.",
        f"7. CONSISTENT BASELINE: Maintain a consistent imaginary floor level across all {total_frames} areas, so physical movements look correct when the frames are played sequentially as a GIF.",
        "",
        f"Background: {background_desc}",
        "",
        f"=== TEXT REQUIREMENT (MANDATORY) ===",
        f"Text content: \"{text_overlay}\"",
        "",
        f"CRITICAL: You MUST draw this text in EVERY SINGLE ONE of the {total_frames} frames. This is a sticker, and text is essential.",
        "",
        "Text styling requirements:",
        f"- Draw the text in ALL {total_frames} frames without exception",
        "- Use highly creative, dynamic typography that perfectly matches the emotion and action of the character",
        "- TEXT COLOR & VARIATION: Vary the font color, style, size, tilt, and weight (e.g., jagged for screaming, bouncy for happy) across the frames to create a natural bouncy animation effect",
        "- Ensure text colors and bold outlines are vibrant and readable",
        "- TEXT GROUPING: Keep all letters of the word tightly grouped together as a single cohesive block. Do NOT scatter individual letters apart. The text should move and bounce naturally as one unit.",
        "- Position dynamically and playfully around the character (e.g., floating or slanted) but keep it fully inside the frame boundaries",
        "- Do NOT let text cover the character's face",
        "",
        "=== NEGATIVE CONSTRAINTS (STRICTLY AVOID) ===",
        NEGATIVE_PROMPT,
    ]

    if reference_image:
        prompt_lines.insert(8, f"Character Reference: Use the provided reference image to accurately draw the exact same character (same shape, colors, features, and overall design) across all frames.")

    return "\n".join(prompt_lines)

def build_transform_photo_prompt(style_preset, additional_description=""):
    style_desc = STYLE_MAPPING.get(style_preset, STYLE_MAPPING["2D_KAWAII"])

    style_specific_instructions = {
        "2D_KAWAII": "Convert to cute chibi proportions: big head small body (1:2 ratio), large expressive eyes, rounded features.",
        "2D_ANIME_COOL": "Convert to cool anime style: sharp features, stylish proportions, dynamic pose potential.",
        "3D_CLAY": "Convert to 3D clay/figurine style: soft rounded forms, toy-like appearance, smooth surfaces.",
        "3D_PIXAR": "Convert to Pixar-style 3D character: expressive features, smooth animation-ready design.",
        "PIXEL_ART": "Convert to pixel art style: simplified features suitable for low-res rendering, clear silhouette.",
        "CHINESE_INK": "Convert to Chinese ink painting style: elegant brush strokes, minimal colors, artistic interpretation.",
        "WATERCOLOR": "Convert to watercolor illustration style: soft edges, gentle colors, artistic hand-painted look.",
        "LINE_ART": "Convert to simple line art: clean outlines, minimal detail, clear recognizable features.",
        "CARTOON_WEST": "Convert to Western cartoon style: exaggerated proportions, bold shapes, expressive design.",
        "CHIBI_SD": "Convert to super deformed chibi: extremely large head, tiny body, maximum cuteness.",
        "MEME_STYLE": "Convert to internet meme style: exaggerated expressions, bold lines, funny and expressive.",
    }

    style_transform = style_specific_instructions.get(style_preset, style_specific_instructions["2D_KAWAII"])

    prompt = f"""TASK: Transform the MAIN PERSON in this photo into a {style_desc} character reference image.

STEP 1 - IDENTIFY THE MAIN PERSON:
Look at the photo and identify the main person/character. Focus on the most prominent person if there are multiple people.

STEP 2 - PRESERVE KEY FEATURES (EXTREMELY IMPORTANT):
You MUST keep the character looking as close to the original person as possible while adapting the art style:
- EXACT Hair: Keep the exact same hairstyle, length, and hair color.
- EXACT Clothing: Keep the exact same clothing (style, color, and visible details). Do NOT invent new outfits.
- EXACT Palette: Use the same color palette as the original photo.
- Facial Features: Preserve the face shape, eye shape, and any distinctive features (glasses, accessories, etc.).
- Do not add random accessories or change the subject's gender/age.

STEP 3 - STYLE TRANSFORMATION:
{style_transform}

STEP 4 - OUTPUT REQUIREMENTS:
- SINGLE CHARACTER ONLY (the main person you identified)
- Portrait/close-up showing head and shoulders
- Front-facing, neutral expression
- Clean solid WHITE background (#FFFFFF)
- Square aspect ratio (1:1)
- NO text, NO watermarks, NO extra elements
- High quality, suitable as a reference image

{f"Additional notes: {additional_description}" if additional_description else ""}

This will be used as a character reference for generating stickers - it must be a clean, single-character image."""
    return prompt

def build_character_reference_prompt(character_prompt, style_preset):
    style_desc = STYLE_MAPPING.get(style_preset, STYLE_MAPPING["2D_KAWAII"])

    prompt = f"""Character Design Reference Sheet - A clear, well-lit front-view portrait of a single character for use as a design reference.

Character Description: {character_prompt}

Art Style: {style_desc}

IMPORTANT Requirements:
- Full body or upper body portrait, clearly showing the character's face, hair, outfit, and distinguishing features
- Neutral standing pose, no action or movement
- Clean solid white background (#FFFFFF)
- Well-lit, clearly visible details
- High quality, suitable as a reference for generating more images of this same character
- The character should have a simple, pleasant expression
- Output resolution: 512x512 pixels, square aspect ratio

This image will be used as a reference to maintain character consistency across multiple generated images."""
    return prompt

def build_meta_text_prompt(set_name, char_name, scene_theme, character_prompt, expressions):
    exp_list_text = "\n".join([f"{i+1}. 动作描述: {e.get('action', '')} | 图片文字: {e.get('text', '')}" for i, e in enumerate(expressions)])
    
    char_name_intro = f"The mascot character is named '{char_name}'. " if char_name else ""
    char_name_task1_hint = f" Mention the character name '{char_name}' naturally in the text." if char_name else ""

    text_prompt = f"""You are a professional WeChat sticker pack operator and copywriter.
I have a sticker pack named '{set_name}'. {char_name_intro}Theme: '{scene_theme}'.
Character Design: {character_prompt}

TASK 1: Write an engaging and creative description/story for this sticker pack. Max 80 Chinese characters. Make it fun and appealing to users.{char_name_task1_hint}
TASK 2: I have {len(expressions)} expressions in this pack. Based on the action and text, create a concise "meaning tag" for each one.
CRITICAL RULE: Each meaning MUST be strictly MAXIMUM 4 CHINESE CHARACTERS. For example: "打招呼", "开心", "谢谢老板", "委屈巴巴".
TASK 3: Select exactly 1 or 2 "Sticker Styles" (表情风格) from this exact list: [日常, 软萌可爱, 二次元, 长辈风, 搞笑, 丧/佛系, 魔性鬼畜, 恶搞, 简笔画, 赛博朋克, 蒸汽波, 像素, 暗黑, 复古]
TASK 4: Select exactly 1 "Sticker Theme" (表情主题) from this exact list: [万能通用, 网络热点, 节日, 考试/学习, 工作/职场, 情侣, 毕业, 刷屏, 红包相关, 游戏, 运动/健身, 怼人/斗图, 群聊必备, 节气, 邀约/约起来, 励志鼓舞]

Expressions:
{exp_list_text}

Output MUST be valid JSON with this exact structure:
{{
  "description": "your 80-char story here",
  "meanings": ["meaning1", "meaning2", ...],
  "styles": ["selected_style1", "selected_style2"],
  "theme": "selected_theme"
}}
Ensure the 'meanings' array has exactly {len(expressions)} items.
"""
    return text_prompt

def build_banner_prompt(set_name, char_name, character_prompt, scene_theme, description, style_preset):
    style_desc = STYLE_MAPPING.get(style_preset, STYLE_MAPPING["2D_KAWAII"])
    banner_prompt = f"""Design an aesthetic, wide horizontal promotional banner for a sticker pack named '{set_name}'.
Character: '{char_name}'
Character Design: {character_prompt}
Theme Context: {scene_theme} / {description}
Style: {style_desc}. 
Requirement: The composition must be cinematic and horizontal. The character should be interacting with the theme environment. Place the character off-center to leave room for text. Incorporate the text '{set_name}' creatively into the banner. No borders, high masterpiece quality."""
    return banner_prompt

def build_cover_prompt(set_name, char_name, character_prompt, scene_theme, description, style_preset):
    style_desc = STYLE_MAPPING.get(style_preset, STYLE_MAPPING["2D_KAWAII"])
    cover_prompt = f"""Design an eye-catching square cover art for a sticker pack named '{set_name}'.
Character: '{char_name}'
Character Design: {character_prompt}
Theme Context: {scene_theme} / {description}
Style: {style_desc}.
Requirement: Close-up portrait of the character doing an extremely cute or funny pose that represents the '{scene_theme}' theme. The character must be looking directly at the camera. Vibrant, solid or simple background. Perfect square composition. Masterpiece quality."""
    return cover_prompt

def build_prompts_workspace(target_dir):
    json_path = os.path.join(target_dir, "params.json")
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found inside {target_dir}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mode = data.get("mode", "static")
    character = data.get("character_prompt", "")
    style_preset = data.get("style_preset", "2D_KAWAII")
    custom_style = data.get("custom_style", "")
    scene_theme = data.get("scene_theme", "")
    character_type = data.get("character_type", "")
    color_mood = data.get("color_mood", "BRIGHT_VIBRANT")
    reference_image = data.get("reference_image", "")
    background_type = data.get("background_type", "transparent")
    grid_size = data.get("grid_size", DEFAULT_GRID_SIZE)

    grid_config = GRID_CONFIG.get(grid_size, GRID_CONFIG[DEFAULT_GRID_SIZE])

    if reference_image and os.path.isfile(reference_image):
        ref_abs_path = os.path.abspath(reference_image)
        target_dir_abs = os.path.abspath(target_dir)
        if not ref_abs_path.startswith(target_dir_abs + os.sep):
            ref_filename = os.path.basename(reference_image)
            new_ref_path = os.path.join(target_dir, "reference_" + ref_filename)
            shutil.copy2(reference_image, new_ref_path)
            reference_image = os.path.abspath(new_ref_path)

    expressions = data.get("expressions", [])

    if style_preset == "CUSTOM" and custom_style:
        style_desc = custom_style + ", high quality."
    else:
        style_desc = STYLE_MAPPING.get(style_preset, STYLE_MAPPING["2D_KAWAII"])

    if scene_theme and scene_theme in SCENE_MAPPING:
        style_desc += f", {SCENE_MAPPING[scene_theme]}"

    type_hint = ""
    if character_type and character_type in CHARACTER_TYPE_HINTS:
        type_hint = CHARACTER_TYPE_HINTS[character_type]
        character = f"{character}, {type_hint}"

    if color_mood and color_mood in COLOR_MOOD_MAPPING:
        style_desc += f", {COLOR_MOOD_MAPPING[color_mood]}"

    if mode == "static":
        chunk_size = grid_config["chunk_size"]
        chunks = [expressions[i:i + chunk_size] for i in range(0, len(expressions), chunk_size)]
        for i, chunk in enumerate(chunks):
            sub_dir = os.path.join(target_dir, f"static_{i+1:02d}")
            os.makedirs(sub_dir, exist_ok=True)
            prompt_text = build_static_prompt(character, style_desc, chunk, reference_image, background_type, grid_size)
            with open(os.path.join(sub_dir, "prompt.txt"), "w", encoding="utf-8") as f:
                f.write(prompt_text)
    else:
        for i, exp in enumerate(expressions):
            sub_dir = os.path.join(target_dir, f"anim_{i+1:02d}")
            os.makedirs(sub_dir, exist_ok=True)
            action = exp.get("action", "")
            text_overlay = exp.get("text", "")
            prompt_text = build_animated_prompt(character, style_desc, action, text_overlay, reference_image, background_type, grid_size)
            with open(os.path.join(sub_dir, "prompt.txt"), "w", encoding="utf-8") as f:
                f.write(prompt_text)

    print(f"Prompts successfully generated inside {target_dir} (grid_size={grid_size})")
    return target_dir
