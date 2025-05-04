from transformers import pipeline
import logging

zero_shot_classifier = pipeline("zero-shot-classification", model="MoritzLaurer/ModernBERT-large-zeroshot-v2.0") # facebook/bart-large-mnli 

CATEGORY = [
    "natural language processing",
    "computer vision",
    "audio processing",
    "time series forecasting",
    "data science",
    "image classification",
    "text classification",
    "reinforcement learning",
    "bioinformatics",
    "non-AI competition"
]

def is_ai_related(title, desc):
    """
    title + desc로 AI 관련 여부 제로샷 분류
    """
    text = f"{title}. {desc}"
    result = zero_shot_classifier(text, CATEGORY)
    top_label = result["labels"][0]
    score = result["scores"][0]
    
    logging.info(f"Top-3 분류 결과 for {title}:")
    for label, score in zip(result["labels"][:3], result["scores"][:3]):
        logging.info(f"  → {label} ({score:.2f})")
    
    return top_label != "non-AI competition"


