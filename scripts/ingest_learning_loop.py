#!/usr/bin/env python3
"""CLI helper to ingest qualitative Obsidian-style logs and stage memory updates."""

import argparse
import json
import re
from pathlib import Path

# Add project root to path to resolve imports correctly
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event

def parse_obsidian_log(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    
    # Extract frontmatter if any
    frontmatter = {}
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, flags=re.DOTALL)
    if fm_match:
        try:
            # Try to parse frontmatter using simple split if yaml is not available
            fm_text = fm_match.group(1)
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip()] = v.strip().strip('"\'')
        except Exception:
            pass
            
    # Try to find a JSON block in the markdown
    json_match = re.search(r"```json\s*(.*?)\n```", text, flags=re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except Exception:
            pass
            
    # Parse text headers if no JSON block exists
    payload = {
        "title": "",
        "observations": [],
        "lessons": [],
        "staged_memory": {}
    }
    
    title_match = re.search(r"^#\s+(.*)", text)
    if title_match:
        payload["title"] = title_match.group(1).strip()
        
    current_section = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            current_section = line[3:].lower().strip()
            continue
        if line.startswith("- ") and current_section:
            item = line[2:].strip()
            if "observation" in current_section:
                payload["observations"].append(item)
            elif "lesson" in current_section:
                payload["lessons"].append(item)
                
    # Create staged memory payload
    payload["staged_memory"] = {
        "source_log_file": str(path.name),
        "frontmatter": frontmatter,
        "observations": payload["observations"],
        "lessons": payload["lessons"]
    }
    return payload

def main():
    parser = argparse.ArgumentParser(description="Ingest qualitative Obsidian-style logs for memory updates")
    parser.add_argument("log_path", help="Path to the Obsidian qualitative log file")
    parser.add_argument("--actor", default="learning-review", help="Actor running this task")
    args = parser.parse_args()
    
    log_path = Path(args.log_path).resolve()
    if not log_path.exists():
        log_path = (PROJECT_ROOT / args.log_path).resolve()
        if not log_path.exists():
            print(f"Error: Log file not found: {args.log_path}")
            return 1
        
    parsed = parse_obsidian_log(log_path)
    
    # Append the event to events.jsonl
    event = append_event(
        "memory.proposal_staged",
        args.actor,
        object_type="memory_proposal",
        object_id=log_path.name,
        payload=parsed.get("staged_memory", parsed),
        citations=[str(log_path.relative_to(PROJECT_ROOT))]
    )
    
    print(f"Successfully staged memory proposal from {log_path.name}")
    print(f"Staged Event ID: {event['event_id']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
