from .app import build_app

def main() -> None:
  demo = build_app()
  demo.launch()

__all__ = ["main"]
