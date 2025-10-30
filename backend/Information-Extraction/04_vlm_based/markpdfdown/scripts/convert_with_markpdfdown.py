#!/usr/bin/env python3
"""
Simple helper script to call markpdfdown programmatically from outside the package.

Features:
- Accepts input/output paths, page range
- Optionally accepts API keys or an .env file (set before importing the library)
- Ensures environment variables are applied before importing markpdfdown so configuration picks them up

Usage examples:

# Use existing .env in project (recommended)
python scripts/convert_with_markpdfdown.py -i /path/to/doc.pdf -o /path/to/out.md

# Or pass API key on the command line (temporary, not saved to disk)
python scripts/convert_with_markpdfdown.py -i doc.pdf -o out.md --openai-key sk-xxx

# Or specify an env file
python scripts/convert_with_markpdfdown.py -i doc.pdf -o out.md --env-file /path/to/.env
"""

import os
import argparse
from dotenv import load_dotenv


def main():
    parser = argparse.ArgumentParser(description="Call markpdfdown library to convert PDF/image to Markdown")
    parser.add_argument("-i", "--input", required=True, help="Path to input PDF or image file")
    parser.add_argument("-o", "--output", required=True, help="Path to output Markdown file")
    parser.add_argument("--start", type=int, default=1, help="Start page (1-based)")
    parser.add_argument("--end", type=int, default=0, help="End page (0 means last page)")
    parser.add_argument("--openai-key", default=None, help="OpenAI API key (temporary for this run)")
    parser.add_argument("--openrouter-key", default=None, help="OpenRouter API key (temporary for this run)")
    parser.add_argument("--model", default=None, help="Model name to use (overrides MODEL_NAME env var)")
    parser.add_argument("--env-file", default=None, help="Path to a .env file to load before running")

    args = parser.parse_args()

    # Load env file first (if provided) so values are present when markpdfdown imports config
    if args.env_file:
        if os.path.exists(args.env_file):
            load_dotenv(args.env_file, override=True)
        else:
            raise SystemExit(f"Env file not found: {args.env_file}")

    # Apply keys/model to os.environ before importing markpdfdown so config picks them up
    if args.openai_key:
        os.environ["OPENAI_API_KEY"] = args.openai_key
    if args.openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = args.openrouter_key
    if args.model:
        os.environ["MODEL_NAME"] = args.model

    # Import library after env is ready
    try:
        from markpdfdown.main import convert_from_file
    except Exception as e:
        raise SystemExit(f"Failed to import markpdfdown: {e}")

    # Run conversion
    try:
        markdown = convert_from_file(args.input, start_page=args.start, end_page=args.end)
    except Exception as e:
        raise SystemExit(f"Conversion failed: {e}")

    # Write output
    out_dir = os.path.dirname(args.output)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Saved output to: {args.output}")


if __name__ == "__main__":
    main()
