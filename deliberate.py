#!/usr/bin/env python3
"""
Multi-Model Deliberation CLI

Main entry point for running multi-model deliberation sessions.
"""

import argparse
import asyncio
import sys
from typing import Optional

from config import DeliberationConfig, get_available_models, print_model_status
from orchestrator import DeliberationOrchestrator, DeliberationSession


def print_banner():
    """Print welcome banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          MULTI-MODEL AI DELIBERATION SYSTEM                   ║
║                                                               ║
║  Orchestrating collaborative AI discussions for              ║
║  deeper insights and consensus building                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Model AI Deliberation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple deliberation with default settings
  python deliberate.py "What are the biggest risks in AI development?"
  
  # Specify number of rounds
  python deliberate.py "How can we address climate change?" --rounds 5
  
  # Use specific models only
  python deliberate.py "What is consciousness?" --models gpt4 claude
  
  # Show only summary
  python deliberate.py "Best practices for code review?" --summary-only
  
  # Interactive mode
  python deliberate.py --interactive
  
  # Check model status
  python deliberate.py --status
        """
    )
    
    parser.add_argument(
        "question",
        nargs="?",
        help="Question to deliberate on (required unless --interactive or --status)"
    )
    
    parser.add_argument(
        "-r", "--rounds",
        type=int,
        default=3,
        help="Number of deliberation rounds (default: 3)"
    )
    
    parser.add_argument(
        "-m", "--models",
        nargs="+",
        help="Specific models to use (e.g., gpt4 claude gemini grok)"
    )
    
    parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=0.7,
        help="Temperature for model responses (default: 0.7)"
    )
    
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2000,
        help="Maximum tokens per response (default: 2000)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output including all rounds"
    )
    
    parser.add_argument(
        "-s", "--summary-only",
        action="store_true",
        help="Show only final consensus, skip round-by-round output"
    )
    
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output"
    )
    
    parser.add_argument(
        "--consensus-threshold",
        type=float,
        default=0.75,
        help="Threshold for consensus detection (default: 0.75)"
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Start interactive mode for multiple questions"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status of all configured models and exit"
    )
    
    return parser.parse_args()


async def run_single_deliberation(question: str, config: DeliberationConfig) -> DeliberationSession:
    """
    Run a single deliberation session.
    
    Args:
        question: Question to deliberate on
        config: Deliberation configuration
        
    Returns:
        DeliberationSession with results
    """
    try:
        orchestrator = DeliberationOrchestrator(config)
        session = await orchestrator.run_deliberation(question)
        return session
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Deliberation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def interactive_mode(base_config: DeliberationConfig):
    """
    Run interactive mode for multiple questions.
    
    Args:
        base_config: Base configuration to use
    """
    print("\n🔄 Interactive Mode")
    print("=" * 60)
    print("Enter your questions one at a time.")
    print("Type 'quit', 'exit', or press Ctrl+C to exit.")
    print("Type 'status' to see available models.")
    print("=" * 60)
    
    while True:
        try:
            print("\n")
            question = input("❓ Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if question.lower() == 'status':
                print_model_status()
                continue
            
            # Run deliberation
            session = await run_single_deliberation(question, base_config)
            
            # Ask if user wants to continue
            print("\n" + "=" * 60)
            continue_prompt = input("\nAsk another question? (y/n): ").strip().lower()
            if continue_prompt not in ['y', 'yes', '']:
                print("\n👋 Goodbye!")
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break


def export_session_summary(session: DeliberationSession, filename: Optional[str] = None):
    """
    Export session summary to a file.
    
    Args:
        session: Deliberation session
        filename: Output filename (optional)
    """
    if not filename:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"deliberation_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("MULTI-MODEL DELIBERATION SESSION SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Question: {session.question}\n\n")
        f.write(f"Models Used: {', '.join(session.models_used)}\n")
        f.write(f"Total Rounds: {len(session.rounds)}\n")
        f.write(f"Duration: {session.total_duration:.1f} seconds\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("DELIBERATION ROUNDS\n")
        f.write("=" * 80 + "\n\n")
        
        for round_result in session.rounds:
            f.write(f"\n{'─' * 80}\n")
            f.write(f"ROUND {round_result.round_number}\n")
            f.write(f"{'─' * 80}\n\n")
            
            for model_id, response in round_result.responses.items():
                if response.error:
                    f.write(f"[{response.model_name}] ERROR: {response.error}\n\n")
                else:
                    f.write(f"[{response.model_name}]\n")
                    f.write(response.response + "\n\n")
            
            if round_result.consensus_metrics:
                f.write(f"\n{'─' * 40}\n")
                f.write("Consensus Analysis:\n")
                f.write(str(round_result.consensus_metrics) + "\n")
                f.write(f"{'─' * 40}\n\n")
        
        if session.final_consensus:
            f.write("\n" + "=" * 80 + "\n")
            f.write("FINAL CONSENSUS\n")
            f.write("=" * 80 + "\n\n")
            f.write(session.final_consensus + "\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF SESSION\n")
        f.write("=" * 80 + "\n")
    
    print(f"\n📄 Session summary exported to: {filename}")


async def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Show status and exit if requested
    if args.status:
        print_model_status()
        sys.exit(0)
    
    # Check if question provided or interactive mode
    if not args.question and not args.interactive:
        print("❌ Error: Either provide a question or use --interactive mode", file=sys.stderr)
        print("\nUsage: python deliberate.py \"Your question here\"")
        print("   or: python deliberate.py --interactive")
        print("\nFor more options: python deliberate.py --help")
        sys.exit(1)
    
    # Print banner
    if not args.summary_only:
        print_banner()
    
    # Create configuration
    config = DeliberationConfig(
        rounds=args.rounds,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        verbose=args.verbose,
        summary_only=args.summary_only,
        stream=not args.no_stream,
        consensus_threshold=args.consensus_threshold,
        models=args.models
    )
    
    # Run interactive or single mode
    if args.interactive:
        await interactive_mode(config)
    else:
        session = await run_single_deliberation(args.question, config)
        
        # Optionally export summary
        if args.verbose:
            export_choice = input("\n\n📄 Export session summary to file? (y/n): ").strip().lower()
            if export_choice in ['y', 'yes']:
                export_session_summary(session)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
