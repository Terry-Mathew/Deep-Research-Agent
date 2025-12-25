import gradio as gr
import asyncio
from deep_research_agent import run_deep_research

def run_research(prompt, progress=gr.Progress()):
    """Research function with progress tracking"""
    
    if not prompt or len(prompt.strip()) < 10:
        return "<div style='color:#EF4444;padding:20px;'>❌ Please enter a research topic (at least 10 characters)</div>"
    
    try:
        # Progress callback
        def update_progress(msg):
            progress(0, desc=msg)
        
        # Run research
        result = asyncio.run(run_deep_research(prompt, update_progress))
        
        if result["status"] == "error":
            return f"""
            <div style='background:#7F1D1D;color:#FCA5A5;padding:20px;border-radius:8px;'>
                <h2>❌ Research Failed</h2>
                <p>{result.get('error', 'Unknown error occurred')}</p>
                <p><small>Duration: {result['duration']}s | Cost: ${result['costs']['cost_usd']}</small></p>
            </div>
            """
        
        rep = result["report"]
        plan = result["plan"]
        cost = result["costs"]
        duration = result["duration"]

        md = """
<style>
body { background:#0F172A; color:#E2E8F0; font-family: 'Inter', sans-serif; }
.card {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 24px;
    border: 1px solid #334155;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}
.card h2 { 
    color: #60A5FA; 
    margin-top: 0;
    font-size: 1.5em;
    border-bottom: 2px solid #334155;
    padding-bottom: 12px;
}
.card ul { line-height: 1.8; }
.card li { margin-bottom: 8px; }
.stats {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}
.stat-item {
    background: #1E293B;
    padding: 12px 20px;
    border-radius: 8px;
    border: 1px solid #475569;
}
.stat-label { color: #94A3B8; font-size: 0.9em; }
.stat-value { color: #60A5FA; font-size: 1.3em; font-weight: bold; }
pre {
    background: #0F172A;
    padding: 16px;
    border-radius: 8px;
    border: 1px solid #334155;
    overflow-x: auto;
    line-height: 1.6;
    white-space: pre-wrap;
}
.confidence-high { color: #34D399; }
.confidence-medium { color: #FBBF24; }
.confidence-low { color: #F87171; }
.gr-button { 
    background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%) !important;
    border: none !important;
    color: white !important;
    font-size: 1.1em !important;
    padding: 12px 32px !important;
    border-radius: 8px !important;
    transition: all 0.3s !important;
}
.gr-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(59, 130, 246, 0.4) !important;
}
</style>
"""

        # PLAN
        md += f"""<div class="card">
<h2>🎯 Research Strategy</h2>
<ul>"""
        for i, s in enumerate(plan["searches"], 1):
            md += f"<li><b>Query {i}:</b> {s['query']}<br><small style='color:#94A3B8;'>{s['reason']}</small></li>"
        md += "</ul></div>"

        # SUMMARY
        confidence_class = f"confidence-{rep['confidence'].lower().split()[0]}"
        md += f"""<div class="card">
<h2>{rep['title']}</h2>
<p style='font-size:1.1em;line-height:1.7;'>{rep['summary']}</p>
<p style='margin-top:16px;'><span class='{confidence_class}'>● {rep['confidence']}</span></p>
</div>
"""

        # FINDINGS
        md += """<div class="card"><h2>📌 Key Findings</h2><ul>"""
        for f in rep["findings"]:
            md += f"<li>{f}</li>"
        md += "</ul></div>"

        # DETAILED
        md += f"""<div class="card">
<h2>📘 Detailed Analysis</h2>
<pre>{rep['detailed']}</pre>
</div>
"""

        # METRICS
        md += f"""<div class="card">
<h2>📊 Research Metrics</h2>
<div class="stats">
    <div class="stat-item">
        <div class="stat-label">API Calls</div>
        <div class="stat-value">{cost['api_calls']}</div>
    </div>
    <div class="stat-item">
        <div class="stat-label">Estimated Cost</div>
        <div class="stat-value">${cost['cost_usd']}</div>
    </div>
    <div class="stat-item">
        <div class="stat-label">Duration</div>
        <div class="stat-value">{duration}s</div>
    </div>
    <div class="stat-item">
        <div class="stat-label">Searches</div>
        <div class="stat-value">{len(plan['searches'])}</div>
    </div>
</div>
</div>
"""

        return md

    except Exception as e:
        return f"""
        <div style='background:#7F1D1D;color:#FCA5A5;padding:20px;border-radius:8px;'>
            <h2>❌ Unexpected Error</h2>
            <p>{str(e)}</p>
        </div>
        """


# Create Gradio interface (Gradio 6.x style)
with gr.Blocks() as demo:
    gr.HTML("""
    <div style='text-align:center; padding: 40px 20px;'>
        <h1 style='color:#60A5FA; font-size:3em; margin-bottom:8px;'>🔬 TMP AI Deep Research Agent</h1>
        <p style='color:#CBD5E1; font-size:1.2em;'>AI-powered comprehensive research in seconds</p>
    </div>
    """)

    with gr.Row():
        inp = gr.Textbox(
            lines=3, 
            label="🎯 Research Topic",
            placeholder="E.g., Latest trends in AI agent frameworks for 2025...",
            info="Enter your research question or topic (minimum 10 characters)"
        )
    
    with gr.Row():
        btn = gr.Button("🚀 Start Deep Research", size="lg", variant="primary")
        clear_btn = gr.ClearButton(components=[inp], value="Clear", size="sm")
    
    out = gr.HTML(
        "<div style='text-align:center; padding:60px; color:#64748B;'>Your comprehensive research report will appear here...</div>"
    )

    btn.click(run_research, inputs=inp, outputs=out)
    
    gr.HTML("""
    <div style='text-align:center; padding:20px; color:#64748B; font-size:0.9em;'>
        <p>Powered by OpenAI GPT-4o-mini & DuckDuckGo Search | Built with Gradio</p>
    </div>
    """)

# Launch (theme goes here in Gradio 6.x, not in Blocks())
if __name__ == "__main__":
    demo.queue(max_size=20)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True
    )
