import gradio as gr
import markdown
import asyncio
from deep_research_agent import run_deep_research

def run_research(prompt, progress=gr.Progress()):
    """Stable research function with Serper.dev"""

    if not prompt or len(prompt.strip()) < 5:
        return "<div style='color:#EF4444;padding:20px;'>❌ Please enter a valid question</div>"

    try:
        def update_progress(msg):
            progress(0, desc=msg)

        # Run stable research
        result = asyncio.run(run_deep_research(prompt))
        
        # Check success
        if result.get("status") != "success":
             return f"""
            <div style='background:#7F1D1D;color:#FCA5A5;padding:20px;border-radius:8px;'>
                <h2>❌ Research Failed</h2>
                <p>Unknown error occurred</p>
            </div>
            """

        report = result["report"]
        duration = result["duration"]
        plan = result["plan"]

        md = """
<style>
body { background:#0F172A; color:#E2E8F0; font-family: 'Inter', sans-serif; }
.card {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 24px;
    border: 1px solid #334155;
}
.card h2 { color:#60A5FA; border-bottom:1px solid #334155; padding-bottom:8px; }
pre { white-space:pre-wrap; line-height:1.7; }
.stat { color:#94A3B8; }
</style>
"""

        md += f"""
<div class="card">
<h2>{report["title"]}</h2>
<p style="font-size:1.1em;line-height:1.7;">{report["summary"]}</p>
<p class="stat">Confidence: {report["confidence"]}</p>
</div>
"""

        md += "<div class='card'><h2>📌 Key Findings</h2><ul>"
        for f in report["findings"]:
            md += f"<li>{f}</li>"
        md += "</ul></div>"

        detailed_html = markdown.markdown(report["detailed"])
        md += f"""
<div class="card">
<h2>📘 Detailed Analysis</h2>
<div class="detailed-content">
{detailed_html}
</div>
</div>
<style>
.detailed-content {{
    line-height: 1.6;
    font-size: 1.1em;
}}
.detailed-content h1, .detailed-content h2, .detailed-content h3 {{
    color: #60A5FA;
    margin-top: 20px;
}}
.detailed-content p {{
    margin-bottom: 15px;
}}
.detailed-content ul, .detailed-content ol {{
    margin-bottom: 15px;
    padding-left: 20px;
}}
.detailed-content li {{
    margin-bottom: 5px;
}}
</style>
"""

        md += f"""
<div class="card">
<h2>📊 Metrics</h2>
<p class="stat">Duration: {duration}s</p>
<p class="stat">Search Queries: {len(plan['searches'])}</p>
</div>
"""

        return md

    except Exception as e:
        return f"""
        <div style='background:#7F1D1D;color:#FCA5A5;padding:20px;border-radius:8px;'>
            <h2>❌ Error</h2>
            <p>{str(e)}</p>
        </div>
        """

# ============================
# UI
# ============================

with gr.Blocks() as demo:
    gr.HTML("""
    <div style='text-align:center;padding:40px'>
        <h1 style='color:#60A5FA;font-size:3em;'>🔬 TMP AI Research Agent</h1>
        <p style='color:#CBD5E1;'>Ask anything — explanation, comparison, or deep research</p>
    </div>
    """)

    inp = gr.Textbox(
        lines=3,
        label="Question",
        placeholder="e.g. What is Retrieval-Augmented Generation?"
    )

    btn = gr.Button("🚀 Run", variant="primary")
    out = gr.HTML()

    btn.click(run_research, inputs=inp, outputs=out)

if __name__ == "__main__":
    demo.queue(max_size=20)
    demo.launch(show_error=True)
