"""Run with: python app.py. For Colab use the included start notebook."""

import argparse
import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr

from agent import OPENING_LINE, RentalAgent, Settings, format_trace, make_client
from rag import format_sources
from rental_tools import initialize_database

GREETING = OPENING_LINE
EMPTY_SOURCES = "Handbook passages appear here when the assistant searches the rental conditions."
EXAMPLES = [
    "What are your opening hours?",
    "Which electric cars are available?",
    "How much is a Toyota Corolla Hybrid for 3 days with GPS?",
    "If I return the car early, will unused days be refunded automatically?",
    "What is the cancellation policy if I cancel 24 hours before pickup?",
    "Can I bring my dog in the rental car?",
    "I want to speak to a member of staff.",
    "Who won the FIFA World Cup in 2014?",
]


def build_app(agent):
    def respond(question, visible_history, api_history):
        result = agent.run(question, api_history)
        visible = list(visible_history or [])
        if question and question.strip():
            visible += [{"role": "user", "content": question},
                        {"role": "assistant", "content": result["answer"]}]
        return "", visible, result["history"], format_trace(result), format_sources(result)

    def clear():
        return "", [{"role": "assistant", "content": GREETING}], [], "No question submitted yet.", EMPTY_SOURCES

    with gr.Blocks(title="ZaenDrive | Midterm Rental Assistant") as demo:
        gr.Markdown("# ZaenDrive\nYour car-rental assistant with answers from our rental handbooks.")
        gr.Markdown("**Fictional coursework demo.** Prices and availability are sample data. "
                    "The app provides quotes and staff contact details; it does not make bookings.")
        api_history = gr.State([])
        with gr.Row():
            with gr.Column(scale=3):
                chat = gr.Chatbot(value=[{"role": "assistant", "content": GREETING}],
                                  label="Customer service", height=480)
                question = gr.Textbox(label="Your question", placeholder="Ask about a car or rental quote…",
                                      lines=2, max_lines=4)
                with gr.Row():
                    send = gr.Button("Send", variant="primary")
                    reset = gr.Button("New conversation")
                gr.Examples(examples=[[q] for q in EXAMPLES], inputs=[question])
            with gr.Column(scale=2):
                gr.Markdown("### Rental handbook sources\nPassages found for the latest question.")
                sources = gr.Markdown(EMPTY_SOURCES)
                with gr.Accordion("Tool details for coursework", open=False):
                    trace = gr.Code(value="No question submitted yet.", language=None,
                                    label="Tool trace", lines=22, interactive=False)
        inputs = [question, chat, api_history]
        outputs = [question, chat, api_history, trace, sources]
        send.click(respond, inputs, outputs, api_name="ask", concurrency_id="agent", concurrency_limit=1)
        question.submit(respond, inputs, outputs, api_name="ask_enter", concurrency_id="agent", concurrency_limit=1)
        reset.click(clear, outputs=outputs, api_name="reset", concurrency_id="agent", concurrency_limit=1)
    return demo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true", help="Create a temporary Gradio public link (e.g. Colab).")
    args = parser.parse_args()
    counts = initialize_database()
    settings = Settings.from_env()
    print(f"Database rebuilt from CSV: {counts}")
    print(f"Model: {settings.model}. Max calls per turn: {settings.max_steps}")
    agent = RentalAgent(make_client(settings), settings)
    build_app(agent).queue().launch(share=args.share, inbrowser=not args.share)


if __name__ == "__main__":
    main()
