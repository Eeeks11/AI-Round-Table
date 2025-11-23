"""Prompt templates for multi-model deliberation."""

from typing import Dict, List


class PromptTemplate:
    """Manager for deliberation prompt templates."""
    
    @staticmethod
    def initial_prompt(question: str) -> str:
        """
        Generate initial prompt for Round 1.
        
        Args:
            question: The user's question
            
        Returns:
            Formatted prompt for first round
        """
        return f"""You are participating in a multi-model AI deliberation session. Multiple AI models (including yourself) will analyze the same question and discuss it over several rounds.

IMPORTANT: You have access to tools for:
- Searching the web for current information (prices, news, products, etc.)
- Getting the current date/time in any timezone

Use these tools whenever you need up-to-date information that may not be in your training data.

Your task is to provide a thoughtful, well-reasoned analysis of the following question:

{question}

Please provide your initial analysis. Be clear, comprehensive, and explain your reasoning. Use the available tools to gather current information when relevant."""
    
    @staticmethod
    def deliberation_prompt(
        question: str,
        round_number: int,
        other_responses: Dict[str, str]
    ) -> str:
        """
        Generate prompt for subsequent deliberation rounds.
        
        Args:
            question: The original question
            round_number: Current round number
            other_responses: Dictionary mapping model names to their responses
            
        Returns:
            Formatted prompt for deliberation round
        """
        responses_text = "\n\n".join([
            f"[{model_name}]:\n{response}"
            for model_name, response in other_responses.items()
        ])
        
        return f"""You are in Round {round_number} of a multi-model AI deliberation session.

IMPORTANT: You have access to tools for:
- Searching the web for current information (prices, news, products, etc.)
- Getting the current date/time in any timezone

Use these tools to verify claims, gather additional data, or check current information.

ORIGINAL QUESTION:
{question}

PERSPECTIVES FROM OTHER AI MODELS:

{responses_text}

YOUR TASK:
1. Consider the perspectives shared by other AI models above
2. Identify points of agreement and disagreement
3. Reflect on whether other models raised valid points you hadn't considered
4. Use the available tools to verify any claims or gather additional current information
5. Refine your analysis based on this collective discussion and any new data
6. Provide your updated perspective

Please be constructive and focus on reaching a well-reasoned consensus while maintaining intellectual honesty. If you disagree with other models, explain why clearly."""
    
    @staticmethod
    def consensus_analysis_prompt(
        question: str,
        all_responses: List[Dict[str, str]]
    ) -> str:
        """
        Generate prompt for analyzing consensus.
        
        Args:
            question: The original question
            all_responses: List of dictionaries containing responses from all rounds
            
        Returns:
            Formatted prompt for consensus analysis
        """
        rounds_text = []
        for i, round_responses in enumerate(all_responses, 1):
            round_text = f"ROUND {i}:\n"
            for model_name, response in round_responses.items():
                round_text += f"\n[{model_name}]: {response[:200]}...\n"
            rounds_text.append(round_text)
        
        return f"""Analyze the following multi-round deliberation and determine if consensus has been reached.

QUESTION: {question}

DISCUSSION:
{chr(10).join(rounds_text)}

Has consensus been reached? Consider:
- Are models converging on similar conclusions?
- Are they building on each other's points?
- Are positions still changing significantly?

Respond with: CONSENSUS or NO_CONSENSUS"""
    
    @staticmethod
    def synthesis_prompt(
        question: str,
        final_responses: Dict[str, str]
    ) -> str:
        """
        Generate prompt for synthesizing final consensus answer.
        
        Args:
            question: The original question
            final_responses: Dictionary of final round responses from each model
            
        Returns:
            Formatted prompt for synthesis
        """
        responses_text = "\n\n".join([
            f"[{model_name}]:\n{response}"
            for model_name, response in final_responses.items()
        ])
        
        return f"""Synthesize a consensus answer from the following multi-model deliberation.

IMPORTANT: You have access to tools for:
- Searching the web for current information
- Getting the current date/time in any timezone

Use these tools if you need to verify any final details or get the latest information for your synthesis.

QUESTION:
{question}

FINAL PERSPECTIVES FROM ALL MODELS:

{responses_text}

YOUR TASK:
Create a comprehensive consensus answer that:
1. Integrates the common themes and agreements across all models
2. Acknowledges any remaining points of disagreement
3. Provides a balanced, well-reasoned response to the original question
4. Highlights the key insights that emerged from the deliberation
5. Verifies any critical facts or current information using the available tools if needed

Format your response as a clear, cohesive answer."""
    
    @staticmethod
    def format_system_message(role: str = "deliberation_participant") -> str:
        """
        Generate system message for the AI model.
        
        Args:
            role: The role of the model in deliberation
            
        Returns:
            System message string
        """
        if role == "deliberation_participant":
            return "You are a thoughtful AI assistant participating in a multi-model deliberation. You have access to web search and date/time tools to gather current information. Be analytical, use tools when you need current data, consider other perspectives, and engage constructively in collaborative reasoning."
        elif role == "synthesizer":
            return "You are an AI assistant tasked with synthesizing consensus from multiple AI perspectives. You have access to web search and date/time tools. Be balanced, comprehensive, focus on common ground, and verify key facts with tools when needed."
        else:
            return "You are a helpful AI assistant with access to web search and date/time tools."
