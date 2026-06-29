class ModelConfig:
    DEFAULT_MODE = "openai"
    MIN_IMAGE_PIXELS = 3_686_400
    DEFAULT_SIZE = "2048x2048"
    OPENAI_MODELS = (
        "doubao-seedream-5-lite",
        "doubao-seedream-4-5",
    )
    GEMINI_MODELS = (
        "gemini-3.1-flash-image-preview",
    )
    DEFAULT_MODEL_BY_MODE = {
        "openai": OPENAI_MODELS[0],
        "gemini": GEMINI_MODELS[0],
    }
    SUPPORTED_MODELS_BY_MODE = {
        "openai": set(OPENAI_MODELS),
        "gemini": set(GEMINI_MODELS),
    }
