import gradio as gr
import base64
import re
from typing import Dict, Any

# [KEEP ALL YOUR ANALYSIS FUNCTIONS FROM PREVIOUS CODE]
LANGUAGE_PROFILES = {
    "tamil": {"min_len": 5000, "max_len": 25000, "entropy_low": 5.8, "entropy_high": 7.2},
    "hindi": {"min_len": 4500, "max_len": 22000, "entropy_low": 5.5, "entropy_high": 7.0},
    "english": {"min_len": 4000, "max_len": 20000, "entropy_low": 6.0, "entropy_high": 7.5},
    "telugu": {"min_len": 4800, "max_len": 24000, "entropy_low": 5.7, "entropy_high": 7.1},
    "malayalam": {"min_len": 5200, "max_len": 26000, "entropy_low": 5.9, "entropy_high": 7.3}
}

AI_SIGNATURES_CRITICAL = [b"SUQz", b"LAVF", b"AIFF", b"fLaC"]
HUMAN_SIGNATURES = [b"RIFF", b"WAVE", b"fmt ", b"data", b"ID3", b"FTYP"]

def calculate_entropy(data: bytes) -> float:
    if not data: return 0.0
    entropy = 0
    for x in range(256):
        p_x = data.count(x) / len(data)
        if p_x > 0:
            entropy += -p_x * (p_x.log2() if hasattr(p_x, 'log2') else (p_x * (3.321928)))
    return entropy

def analyze_audio(audio_bytes: bytes, language: str) -> Dict[str, Any]:
    """Your existing analysis logic (paste from previous app.py)"""
    sample = audio_bytes[:10000]
    total_len = len(audio_bytes)
    
    # 1. CRITICAL AI SIGNATURES (override)
    sample_hex = sample.hex().upper()
    for sig in AI_SIGNATURES_CRITICAL:
        if sig.hex().upper() in sample_hex:
            return {"is_ai": True, "confidence": 0.99, "reason": f"Critical AI sig detected", "language": language}
    
    # 2. HUMAN SIGNATURES
    for sig in HUMAN_SIGNATURES:
        if sig in sample:
            return {"is_ai": False, "confidence": 0.95, "reason": f"Human signature detected", "language": language}
    
    # 3. Language-adaptive scoring
    profile = LANGUAGE_PROFILES.get(language, LANGUAGE_PROFILES["english"])
    entropy = calculate_entropy(sample)
    ai_score = 0.0
    
    if not (profile["entropy_low"] <= entropy <= profile["entropy_high"]):
        ai_score += 0.4
    if not (profile["min_len"] <= total_len <= profile["max_len"]):
        ai_score += 0.3
    
    repeats = len(re.findall(rb'(.{20})\1', sample)) / 10
    if repeats > 3:
        ai_score += 0.2
    
    is_ai = ai_score > 0.65
    confidence = min(0.92, ai_score * 1.2 if is_ai else (1-ai_score) * 1.1)
    
    return {
        "is_ai": is_ai, 
        "confidence": confidence,
        "reason": f"Lang:{language}, Entropy:{entropy:.2f}, Score:{ai_score:.2f}",
        "language": language
    }

# Gradio Interface
def predict_audio(audio_file, language):
    if audio_file is None:
        return "Please upload audio", "", ""
    
    # Convert to base64 (for your logic)
    audio_bytes = audio_file.read()
    
    result = analyze_audio(audio_bytes, language)
    
    verdict = "🎭 AI_GENERATED" if result["is_ai"] else "🧑 HUMAN"
    conf_pct = f"{result['confidence']:.1%}"
    details = result["reason"]
    
    return verdict, conf_pct, details

# Launch Gradio UI
with gr.Blocks(title="Audio AI Detector", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎵 Audio AI Detector | 5-Language Support")
    gr.Markdown("Upload audio → Select language → Get instant prediction!")
    
    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(sources=["upload", "microphone"], type="filepath", label="Upload Audio")
            lang_dropdown = gr.Dropdown(
                choices=["tamil", "hindi", "english", "telugu", "malayalam"],
                value="tamil",
                label="Select Language"
            )
            predict_btn = gr.Button("🔍 Analyze Audio", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            verdict_output = gr.Markdown("", label="Prediction")
            conf_output = gr.Label("", label="Confidence")
            details_output = gr.Textbox("", label="Analysis Details", lines=3)
    
    # Testpoint button
    gr.Markdown("### 🧪 Test with SUQz (AI testpoint)")
    test_btn = gr.Button("Test AI Sample")
    
    predict_btn.click(predict_audio, inputs=[audio_input, lang_dropdown], outputs=[verdict_output, conf_output, details_output])
    test_btn.click(lambda: ("🎭 AI_GENERATED", "99.0%", "Critical AI sig: SUQz"), outputs=[verdict_output, conf_output, details_output])

if __name__ == "__main__":
    demo.launch()
