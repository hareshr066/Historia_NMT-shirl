import sys
import os

# Ensure imports work correctly from the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, Log
from textual.containers import Vertical
from backend.ai.translation.router import TranslationRouter

class ChronoIKSTuiApp(App):
    """A Textual TUI application with full pipeline loading states for ChronoIKS."""
    
    TITLE = "ChronoIKS AI Gateway - Terminal Frontend"
    SUB_TITLE = "Explainable Semantic Translation for Classical Tamil"
    
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    # Minimal dark-theme CSS layout definition
    CSS = """
    #main_container {
        padding: 1;
    }
    
    #tamil_input {
        border: tall $accent;
        margin-bottom: 1;
    }
    
    .panel {
        border: round $primary;
        background: $surface;
        padding: 1;
        margin-bottom: 1;
    }
    
    #output_panel {
        height: 1fr;
        color: $text;
    }
    
    #status_panel {
        height: 8;
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Vertical(id="main_container"):
            # 1. Tamil Input Panel
            yield Input(placeholder="Enter Tamil text here and press Enter...", id="tamil_input")
            
            # 2. Translation Output Panel
            output_panel = Static("Translation result will be displayed here...", id="output_panel", classes="panel")
            output_panel.border_title = "Translation Output"
            yield output_panel
            
            # 3. Status/Live Logs Panel
            status_panel = Log(id="status_panel", classes="panel")
            status_panel.border_title = "Status / Live Logs"
            yield status_panel
            
        yield Footer()

    def log_message(self, message: str) -> None:
        """Helper to write log messages safely to the Log widget from any thread."""
        log_widget = self.query_one("#status_panel", Log)
        try:
            self.call_from_thread(log_widget.write_line, message)
        except RuntimeError:
            # Fallback to direct synchronous execution when called from the main thread
            log_widget.write_line(message)

    def on_mount(self) -> None:
        """Initialize components and the logs on startup."""
        self.augmenter = None
        self.explainer = None
        self.log_message("System Ready. Enter a Tamil sentence to begin.")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission by running the complete translation pipeline in the background."""
        text = event.value.strip()
        if not text:
            return
            
        input_widget = event.input
        input_widget.disabled = True  # Disable input widget to prevent duplicate Enter presses
        
        output_widget = self.query_one("#output_panel", Static)
        output_widget.loading = True  # Show the built-in loading spinner overlay
        output_widget.update("Running translation pipeline (Retrieval -> Translation -> Explanation)...")
        
        # Clear the input value after submission
        event.input.value = ""
        
        # Run the full pipeline in a worker thread to keep the TUI responsive
        def do_pipeline() -> None:
            try:
                import time
                
                # Lazy load components on first run
                if self.augmenter is None or self.explainer is None:
                    self.log_message("Initializing Retrieval and Explanation components...")
                    from backend.ai.retrieval.augment import IKSInputAugmenter
                    from backend.ai.explain.explanation import IKSExplainer
                    self.augmenter = IKSInputAugmenter()
                    self.explainer = IKSExplainer()
                
                # Stage 1: Concept Retrieval
                self.log_message(f"Stage 1: Detecting concepts and retrieving historical meanings for: '{text}'")
                t_start = time.time()
                aug_result = self.augmenter.augment_sentence(text)
                ret_elapsed = (time.time() - t_start) * 1000.0
                concepts_found = len(aug_result.get("details", []))
                self.log_message(f"  -> Retrieval complete in {ret_elapsed:.1f}ms. Found {concepts_found} concept(s).")
                
                # Stage 2: Translation Inference
                self.log_message("Stage 2: Translating tag-augmented text via NMT model router...")
                t_inf_start = time.time()
                translated_text = TranslationRouter.translate(aug_result["augmented"])
                inf_elapsed = (time.time() - t_inf_start) * 1000.0
                self.log_message(f"  -> Inference complete in {inf_elapsed:.1f}ms.")
                
                # Stage 3: Explanation Generation
                self.log_message("Stage 3: Generating cultural context explanation report...")
                t_exp_start = time.time()
                explanation_report = self.explainer.generate_explanation(
                    original_text=text,
                    translation=translated_text,
                    augmentation_details=aug_result["details"]
                )
                exp_elapsed = (time.time() - t_exp_start) * 1000.0
                self.log_message(f"  -> Explanation complete in {exp_elapsed:.1f}ms.")
                
                # Format pipeline results with Rich markup support
                full_display = (
                    f"[bold]Translation:[/bold]\n{translated_text}\n\n"
                    f"----------------------------------------------------------------------\n"
                    f"[bold]Explanation & Concept Analysis:[/bold]\n{explanation_report}"
                )
                
                def update_ui_success() -> None:
                    output_widget.update(full_display)
                    output_widget.loading = False
                    input_widget.disabled = False
                    input_widget.focus()
                
                self.call_from_thread(update_ui_success)
                self.log_message("Pipeline execution completed successfully.")
                
            except Exception as e:
                error_msg = f"Error occurred during pipeline execution:\n{str(e)}"
                
                def update_ui_error() -> None:
                    output_widget.update(error_msg)
                    output_widget.loading = False
                    input_widget.disabled = False
                    input_widget.focus()
                
                self.call_from_thread(update_ui_error)
                self.log_message(f"Pipeline Error: {str(e)}")

        self.run_worker(do_pipeline, thread=True)

if __name__ == "__main__":
    app = ChronoIKSTuiApp()
    app.run()
