#!/usr/bin/env python3.11
"""
Madhyamaka CLI - Command-line interface for Middle Path analysis

Thin wrapper around madhyamaka service API - facilitates parameter passing
to/from stdio with no additional functionality.

Usage:
    madhyamaka detect eternalism "text to analyze"
    madhyamaka detect nihilism "text to analyze"
    madhyamaka detect middle-path-proximity "text to analyze"
    madhyamaka detect clinging --conversation conversation.json
    madhyamaka transform alternatives "text" --num 5 --stage 3
    madhyamaka transform dependent-origination "text"
    madhyamaka contemplate neti-neti --target self --depth progressive --stage 3
    madhyamaka contemplate two-truths --phenomenon anger
    madhyamaka contemplate dependent-origination --starting-point self
    madhyamaka teach situation --extreme nihilism
    madhyamaka teach list
    madhyamaka health
"""

import sys
import json
import argparse
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, '/Users/tem/humanizer-agent/backend')

from services.madhyamaka import (
    MadhyamakaDetector,
    MadhyamakaTransformer,
    ContemplativePracticeGenerator,
    NAGARJUNA_TEACHINGS
)


def output_json(data: Dict[str, Any]) -> None:
    """Output data as formatted JSON to stdout"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def read_stdin() -> str:
    """Read text from stdin if available"""
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def read_json_file(filepath: str) -> Any:
    """Read and parse JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


# ============================================================================
# DETECT COMMANDS
# ============================================================================

def cmd_detect_eternalism(args: argparse.Namespace) -> None:
    """Detect eternalism/reification in text"""
    text = args.text or read_stdin()
    if not text:
        print("Error: No text provided", file=sys.stderr)
        sys.exit(1)

    detector = MadhyamakaDetector()
    result = detector.detect_eternalism(text)
    output_json(result)


def cmd_detect_nihilism(args: argparse.Namespace) -> None:
    """Detect nihilism/denial of conventional truth"""
    text = args.text or read_stdin()
    if not text:
        print("Error: No text provided", file=sys.stderr)
        sys.exit(1)

    detector = MadhyamakaDetector()
    result = detector.detect_nihilism(text)
    output_json(result)


def cmd_detect_middle_path_proximity(args: argparse.Namespace) -> None:
    """Measure proximity to middle path understanding"""
    text = args.text or read_stdin()
    if not text:
        print("Error: No text provided", file=sys.stderr)
        sys.exit(1)

    detector = MadhyamakaDetector()
    result = detector.detect_middle_path_proximity(text)
    output_json(result)


def cmd_detect_clinging(args: argparse.Namespace) -> None:
    """Detect attachment to views in conversation history"""
    if args.conversation:
        conversation_history = read_json_file(args.conversation)
    elif not sys.stdin.isatty():
        conversation_history = json.loads(read_stdin())
    else:
        print("Error: No conversation history provided", file=sys.stderr)
        print("Provide via --conversation FILE or stdin JSON", file=sys.stderr)
        sys.exit(1)

    detector = MadhyamakaDetector()
    result = detector.detect_clinging(conversation_history)
    output_json(result)


# ============================================================================
# TRANSFORM COMMANDS
# ============================================================================

def cmd_transform_alternatives(args: argparse.Namespace) -> None:
    """Generate middle path alternatives"""
    text = args.text or read_stdin()
    if not text:
        print("Error: No text provided", file=sys.stderr)
        sys.exit(1)

    transformer = MadhyamakaTransformer()
    alternatives = transformer.generate_middle_path_alternatives(
        text=text,
        num_alternatives=args.num,
        user_stage=args.stage
    )

    output_json({
        "original": text,
        "alternatives": alternatives
    })


def cmd_transform_dependent_origination(args: argparse.Namespace) -> None:
    """Reveal dependent origination in text"""
    text = args.text or read_stdin()
    if not text:
        print("Error: No text provided", file=sys.stderr)
        sys.exit(1)

    detector = MadhyamakaDetector()
    eternalism_result = detector.detect_eternalism(text)
    reified_concepts = eternalism_result.get("reified_concepts", [])

    if not reified_concepts:
        output_json({
            "original_statement": text,
            "note": "No strongly reified concepts detected. Text already acknowledges conditionality."
        })
        return

    concept = reified_concepts[0]
    result = {
        "original_statement": text,
        "reified_elements": reified_concepts,
        "dependent_origination_analysis": {
            concept: {
                "concept_depends_on": [
                    {
                        "condition": "Cultural framework",
                        "explanation": f"The concept '{concept}' is defined within specific cultural/linguistic contexts.",
                        "layer": 1
                    },
                    {
                        "condition": "Language creating categories",
                        "explanation": f"'{concept}' is a word that creates the appearance of a discrete thing, when experience is continuous flux.",
                        "layer": 2
                    }
                ],
                "without_these_conditions": f"The phenomenon we call '{concept}' would not be carved out as a distinct category."
            }
        },
        "middle_path_reframing": {
            "text": f"The concept '{concept}' arises dependent on cultural, linguistic, and contextual conditions. It functions conventionally while lacking inherent essence.",
            "what_changed": "Preserved conventional meaning while revealing dependent origination"
        }
    }

    output_json(result)


# ============================================================================
# CONTEMPLATE COMMANDS
# ============================================================================

def cmd_contemplate_neti_neti(args: argparse.Namespace) -> None:
    """Generate Neti Neti (not this, not that) practice"""
    contemplative = ContemplativePracticeGenerator()
    practice = contemplative.generate_neti_neti(
        target_concept=args.target,
        user_stage=args.stage,
        depth=args.depth
    )
    output_json(practice)


def cmd_contemplate_two_truths(args: argparse.Namespace) -> None:
    """Generate Two Truths contemplation"""
    contemplative = ContemplativePracticeGenerator()
    practice = contemplative.generate_two_truths_contemplation(
        phenomenon=args.phenomenon,
        user_context=args.context
    )
    output_json(practice)


def cmd_contemplate_dependent_origination(args: argparse.Namespace) -> None:
    """Generate Dependent Origination inquiry practice"""
    contemplative = ContemplativePracticeGenerator()
    practice = contemplative.generate_dependent_origination_inquiry(
        starting_point=args.starting_point,
        trace_backward=not args.no_backward,
        trace_forward=not args.no_forward
    )
    output_json(practice)


# ============================================================================
# TEACH COMMANDS
# ============================================================================

def cmd_teach_situation(args: argparse.Namespace) -> None:
    """Get teaching for specific situation"""
    user_state = {
        "detected_extreme": args.extreme,
        "clinging_detected": args.clinging
    }

    # Select appropriate teaching
    if args.extreme == "nihilism":
        teaching_key = "emptiness_not_nihilism"
        diagnosis = "Mistaking emptiness for nihilism - common misunderstanding"
    elif args.clinging:
        teaching_key = "clinging_to_emptiness"
        diagnosis = "Attachment to views, even correct ones"
    else:
        teaching_key = "dependent_origination"
        diagnosis = "General middle path instruction"

    teaching_data = NAGARJUNA_TEACHINGS[teaching_key]

    result = {
        "teaching": {
            "diagnosis": diagnosis,
            "core_principle": teaching_data["context"],
            "nagarjuna_quote": {
                "text": teaching_data["quote"],
                "source": teaching_data["source"]
            },
            "explanation": {
                "short": teaching_data["explanation"],
                "detailed": teaching_data["explanation"],
                "experiential": "Notice right now: Your experience is happening, even though it's empty of inherent existence. Sounds occur, sensations arise, thoughts appear. They're not nothing - they're just not inherently existing 'things.'"
            },
            "next_step": {
                "practice": "two_truths_contemplation",
                "focus": "Hold both truths together: Things work AND things are empty"
            }
        }
    }

    output_json(result)


def cmd_teach_list(args: argparse.Namespace) -> None:
    """List all available Nagarjuna teachings"""
    output_json({
        "teachings": NAGARJUNA_TEACHINGS,
        "total_count": len(NAGARJUNA_TEACHINGS)
    })


# ============================================================================
# UTILITY COMMANDS
# ============================================================================

def cmd_health(args: argparse.Namespace) -> None:
    """Health check"""
    output_json({
        "status": "healthy",
        "service": "madhyamaka",
        "message": "The middle path neither exists nor does not exist. Yet this CLI responds."
    })


# ============================================================================
# ARGUMENT PARSER SETUP
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with all subcommands"""
    parser = argparse.ArgumentParser(
        prog='madhyamaka',
        description='Madhyamaka Middle Path CLI - Buddhist philosophy-based language analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Command category')

    # ========== DETECT ==========
    detect_parser = subparsers.add_parser('detect', help='Detection commands')
    detect_subparsers = detect_parser.add_subparsers(dest='detect_cmd', help='Detection type')

    # detect eternalism
    eternalism_parser = detect_subparsers.add_parser('eternalism', help='Detect reification/absolutist language')
    eternalism_parser.add_argument('text', nargs='?', help='Text to analyze (or provide via stdin)')
    eternalism_parser.set_defaults(func=cmd_detect_eternalism)

    # detect nihilism
    nihilism_parser = detect_subparsers.add_parser('nihilism', help='Detect denial of conventional truth')
    nihilism_parser.add_argument('text', nargs='?', help='Text to analyze (or provide via stdin)')
    nihilism_parser.set_defaults(func=cmd_detect_nihilism)

    # detect middle-path-proximity
    proximity_parser = detect_subparsers.add_parser('middle-path-proximity', help='Measure proximity to middle path')
    proximity_parser.add_argument('text', nargs='?', help='Text to analyze (or provide via stdin)')
    proximity_parser.set_defaults(func=cmd_detect_middle_path_proximity)

    # detect clinging
    clinging_parser = detect_subparsers.add_parser('clinging', help='Detect attachment to views')
    clinging_parser.add_argument('--conversation', '-c', help='JSON file with conversation history')
    clinging_parser.set_defaults(func=cmd_detect_clinging)

    # ========== TRANSFORM ==========
    transform_parser = subparsers.add_parser('transform', help='Transformation commands')
    transform_subparsers = transform_parser.add_subparsers(dest='transform_cmd', help='Transformation type')

    # transform alternatives
    alternatives_parser = transform_subparsers.add_parser('alternatives', help='Generate middle path alternatives')
    alternatives_parser.add_argument('text', nargs='?', help='Text to transform (or provide via stdin)')
    alternatives_parser.add_argument('--num', '-n', type=int, default=5, help='Number of alternatives (default: 5)')
    alternatives_parser.add_argument('--stage', '-s', type=int, default=1, choices=[1,2,3,4,5], help='User journey stage (default: 1)')
    alternatives_parser.set_defaults(func=cmd_transform_alternatives)

    # transform dependent-origination
    dep_orig_parser = transform_subparsers.add_parser('dependent-origination', help='Reveal dependent origination')
    dep_orig_parser.add_argument('text', nargs='?', help='Text to analyze (or provide via stdin)')
    dep_orig_parser.set_defaults(func=cmd_transform_dependent_origination)

    # ========== CONTEMPLATE ==========
    contemplate_parser = subparsers.add_parser('contemplate', help='Contemplative practice commands')
    contemplate_subparsers = contemplate_parser.add_subparsers(dest='contemplate_cmd', help='Practice type')

    # contemplate neti-neti
    neti_parser = contemplate_subparsers.add_parser('neti-neti', help='Generate Neti Neti practice')
    neti_parser.add_argument('--target', '-t', default='self', choices=['self', 'thought', 'emotion', 'consciousness'], help='Concept to investigate (default: self)')
    neti_parser.add_argument('--depth', '-d', default='progressive', choices=['simple', 'progressive', 'deep'], help='Practice depth (default: progressive)')
    neti_parser.add_argument('--stage', '-s', type=int, default=3, choices=[1,2,3,4,5], help='User journey stage (default: 3)')
    neti_parser.set_defaults(func=cmd_contemplate_neti_neti)

    # contemplate two-truths
    two_truths_parser = contemplate_subparsers.add_parser('two-truths', help='Generate Two Truths contemplation')
    two_truths_parser.add_argument('--phenomenon', '-p', default='language', help='Phenomenon to investigate (default: language)')
    two_truths_parser.add_argument('--context', '-c', help='User context (optional)')
    two_truths_parser.set_defaults(func=cmd_contemplate_two_truths)

    # contemplate dependent-origination
    dep_orig_contemplate_parser = contemplate_subparsers.add_parser('dependent-origination', help='Generate Dependent Origination inquiry')
    dep_orig_contemplate_parser.add_argument('--starting-point', '-p', default='self', help='Starting concept (default: self)')
    dep_orig_contemplate_parser.add_argument('--no-backward', action='store_true', help='Skip backward trace')
    dep_orig_contemplate_parser.add_argument('--no-forward', action='store_true', help='Skip forward trace')
    dep_orig_contemplate_parser.set_defaults(func=cmd_contemplate_dependent_origination)

    # ========== TEACH ==========
    teach_parser = subparsers.add_parser('teach', help='Teaching commands')
    teach_subparsers = teach_parser.add_subparsers(dest='teach_cmd', help='Teaching type')

    # teach situation
    situation_parser = teach_subparsers.add_parser('situation', help='Get teaching for situation')
    situation_parser.add_argument('--extreme', '-e', choices=['nihilism', 'eternalism', 'none'], default='none', help='Detected extreme type')
    situation_parser.add_argument('--clinging', '-c', action='store_true', help='Clinging detected')
    situation_parser.set_defaults(func=cmd_teach_situation)

    # teach list
    list_parser = teach_subparsers.add_parser('list', help='List all teachings')
    list_parser.set_defaults(func=cmd_teach_list)

    # ========== UTILITY ==========
    health_parser = subparsers.add_parser('health', help='Health check')
    health_parser.set_defaults(func=cmd_health)

    return parser


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
