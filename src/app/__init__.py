from .app import build_app

def main() -> None:
  demo = build_app()
  demo.launch(server_name='0.0.0.0', server_port=7860)

__all__ = ["main"]
