"""Discussion orchestration logic for multi-model deliberation."""

import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
import sys
import time

from config import DeliberationConfig, ModelConfig, get_available_models
from providers import ProviderFactory, BaseProvider, ProviderError, RateLimitError, ModelResponseChunk
from prompts import PromptTemplate
from consensus import ConsensusDetector, ConsensusMetrics
from tools import ToolRegistry


@dataclass
class ModelResponse:
    """Response from a single model."""
    
    model_id: str
    model_name: str
    response: str
    round_number: int
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None


@dataclass
class DeliberationRound:
    """Results from a single deliberation round."""
    
    round_number: int
    responses: Dict[str, ModelResponse]
    consensus_metrics: Optional[ConsensusMetrics] = None
    duration: float = 0.0


@dataclass
class DeliberationSession:
    """Complete deliberation session results."""
    
    question: str
    rounds: List[DeliberationRound]
    final_consensus: Optional[str] = None
    total_duration: float = 0.0
    models_used: List[str] = field(default_factory=list)


class DeliberationOrchestrator:
    """Orchestrates multi-model deliberation sessions."""
    
    def __init__(
        self,
        config: DeliberationConfig,
        output_callback: Optional[Callable] = None
    ):
        """
        Initialize orchestrator.
        
        Args:
            config: Deliberation configuration
            output_callback: Optional callback for real-time output
        """
        self.config = config
        self.output_callback = output_callback or self._default_output
        self.consensus_detector = ConsensusDetector(config.consensus_threshold)
        
        # Initialize tools
        self.tool_registry = ToolRegistry()
        
        # Initialize providers
        self.providers: Dict[str, BaseProvider] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available providers."""
        available_models = get_available_models(self.config.models)
        
        if not available_models:
            raise ValueError(
                "No models available. Please check your API keys in .env file."
            )
        
        for model_id, model_config in available_models.items():
            try:
                provider = ProviderFactory.create_provider(model_config)
                self.providers[model_id] = provider
                self.model_configs[model_id] = model_config
                self.output_callback(
                    f"✓ Initialized {model_config.display_name}",
                    "info"
                )
            except Exception as e:
                self.output_callback(
                    f"✗ Failed to initialize {model_config.display_name}: {str(e)}",
                    "warning"
                )
        
        if not self.providers:
            raise ValueError("No providers could be initialized")
    
    async def run_deliberation(self, question: str) -> DeliberationSession:
        """
        Run complete deliberation session.
        
        Args:
            question: The question to deliberate on
            
        Returns:
            DeliberationSession with complete results
        """
        start_time = time.time()
        
        self.output_callback(f"\n{'='*80}", "header")
        self.output_callback(f"MULTI-MODEL DELIBERATION SESSION", "header")
        self.output_callback(f"{'='*80}", "header")
        self.output_callback(f"\nQuestion: {question}\n", "question")
        self.output_callback(
            f"Models: {', '.join(c.display_name for c in self.model_configs.values())}",
            "info"
        )
        self.output_callback(f"Rounds: {self.config.rounds}\n", "info")
        
        session = DeliberationSession(
            question=question,
            rounds=[],
            models_used=list(self.model_configs.keys())
        )
        
        # Store responses across rounds for consensus analysis
        all_responses_by_round: List[Dict[str, str]] = []
        
        # Run deliberation rounds
        for round_num in range(1, self.config.rounds + 1):
            self.output_callback(f"\n{'─'*80}", "separator")
            self.output_callback(f"ROUND {round_num}", "round_header")
            self.output_callback(f"{'─'*80}\n", "separator")
            
            round_start = time.time()
            
            # Generate prompts for this round
            if round_num == 1:
                # Initial round - each model gets the question independently
                round_result = await self._run_initial_round(question)
            else:
                # Subsequent rounds - models see each other's responses
                previous_responses = all_responses_by_round[-1]
                round_result = await self._run_deliberation_round(
                    question, round_num, previous_responses
                )
            
            round_result.duration = time.time() - round_start
            session.rounds.append(round_result)
            
            # Collect responses for consensus analysis
            current_responses = {
                model_id: resp.response
                for model_id, resp in round_result.responses.items()
                if resp.error is None
            }
            all_responses_by_round.append(current_responses)
            
            # Analyze consensus after round 2+
            if round_num >= 2:
                consensus = self.consensus_detector.analyze_consensus(
                    all_responses_by_round,
                    list(self.model_configs.keys())
                )
                round_result.consensus_metrics = consensus
                
                if not self.config.summary_only:
                    self.output_callback(f"\n{'─'*40}", "separator")
                    self.output_callback("Consensus Analysis:", "consensus_header")
                    self.output_callback(str(consensus), "consensus")
                    self.output_callback(f"{'─'*40}\n", "separator")
                
                # Early exit if consensus reached
                if consensus.has_consensus and round_num < self.config.rounds:
                    self.output_callback(
                        f"\n✓ Consensus reached after {round_num} rounds!",
                        "success"
                    )
                    break
        
        # Generate final synthesis
        if all_responses_by_round:
            self.output_callback(f"\n{'='*80}", "header")
            self.output_callback("GENERATING FINAL CONSENSUS...", "header")
            self.output_callback(f"{'='*80}\n", "header")
            
            final_consensus = await self._synthesize_consensus(
                question, all_responses_by_round[-1]
            )
            session.final_consensus = final_consensus
        
        session.total_duration = time.time() - start_time
        
        self.output_callback(f"\n{'='*80}", "header")
        self.output_callback(
            f"Session completed in {session.total_duration:.1f} seconds",
            "info"
        )
        self.output_callback(f"{'='*80}\n", "header")
        
        # Print API usage statistics
        self._print_usage_stats()
        
        return session
    
    def _print_usage_stats(self):
        """Print API usage statistics for all providers."""
        self.output_callback("\n📊 API Usage Statistics:", "info")
        self.output_callback("─" * 80, "separator")
        
        for model_id, provider in self.providers.items():
            stats = provider.rate_limiter.get_usage_stats()
            model_name = self.model_configs[model_id].display_name
            
            rpm_pct = (stats['rpm'] / stats['rpm_limit']) * 100 if stats['rpm_limit'] > 0 else 0
            tpm_pct = (stats['tpm'] / stats['tpm_limit']) * 100 if stats['tpm_limit'] > 0 else 0
            rpd_pct = (stats['rpd'] / stats['rpd_limit']) * 100 if stats['rpd_limit'] > 0 else 0
            
            self.output_callback(f"\n{model_name}:", "info")
            self.output_callback(
                f"  RPM: {stats['rpm']}/{stats['rpm_limit']} ({rpm_pct:.1f}%)",
                "info"
            )
            self.output_callback(
                f"  TPM: {stats['tpm']:,}/{stats['tpm_limit']:,} ({tpm_pct:.1f}%)",
                "info"
            )
            self.output_callback(
                f"  RPD: {stats['rpd']}/{stats['rpd_limit']} ({rpd_pct:.1f}%)",
                "info"
            )
        
        self.output_callback("─" * 80 + "\n", "separator")
    
    async def _run_initial_round(self, question: str) -> DeliberationRound:
        """
        Run initial round where each model responds independently.
        
        Args:
            question: The question to ask
            
        Returns:
            DeliberationRound with responses
        """
        prompt = PromptTemplate.initial_prompt(question)
        system_message = PromptTemplate.format_system_message("deliberation_participant")
        
        # Get responses from all models concurrently
        tasks = []
        for model_id, provider in self.providers.items():
            task = self._get_model_response(
                model_id, provider, prompt, system_message, 1
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        round_responses = {}
        for model_id, result in zip(self.providers.keys(), responses):
            if isinstance(result, Exception):
                self.output_callback(
                    f"Error from {self.model_configs[model_id].display_name}: {str(result)}",
                    "error"
                )
                round_responses[model_id] = ModelResponse(
                    model_id=model_id,
                    model_name=self.model_configs[model_id].display_name,
                    response="",
                    round_number=1,
                    error=str(result)
                )
            else:
                round_responses[model_id] = result
        
        return DeliberationRound(round_number=1, responses=round_responses)
    
    async def _run_deliberation_round(
        self,
        question: str,
        round_number: int,
        previous_responses: Dict[str, str]
    ) -> DeliberationRound:
        """
        Run deliberation round where models see each other's responses.
        
        Args:
            question: Original question
            round_number: Current round number
            previous_responses: Responses from previous round
            
        Returns:
            DeliberationRound with responses
        """
        system_message = PromptTemplate.format_system_message("deliberation_participant")
        
        # Get responses from all models concurrently
        tasks = []
        for model_id, provider in self.providers.items():
            # Create prompt with other models' responses
            other_responses = {
                self.model_configs[other_id].display_name: response
                for other_id, response in previous_responses.items()
                if other_id != model_id and response  # Exclude self and empty responses
            }
            
            prompt = PromptTemplate.deliberation_prompt(
                question, round_number, other_responses
            )
            
            task = self._get_model_response(
                model_id, provider, prompt, system_message, round_number
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        round_responses = {}
        for model_id, result in zip(self.providers.keys(), responses):
            if isinstance(result, Exception):
                self.output_callback(
                    f"Error from {self.model_configs[model_id].display_name}: {str(result)}",
                    "error"
                )
                round_responses[model_id] = ModelResponse(
                    model_id=model_id,
                    model_name=self.model_configs[model_id].display_name,
                    response="",
                    round_number=round_number,
                    error=str(result)
                )
            else:
                round_responses[model_id] = result
        
        return DeliberationRound(round_number=round_number, responses=round_responses)
    
    async def _get_model_response(
        self,
        model_id: str,
        provider: BaseProvider,
        prompt: str,
        system_message: str,
        round_number: int
    ) -> ModelResponse:
        """
        Get response from a single model with tool support.
        Implements multi-turn tool calling: model requests tools, we execute them,
        and send results back for the model to formulate a final response.
        
        Args:
            model_id: Model identifier
            provider: Provider instance
            prompt: Prompt to send
            system_message: System message
            round_number: Current round number
            
        Returns:
            ModelResponse object
        """
        model_name = self.model_configs[model_id].display_name
        
        if not self.config.summary_only:
            self.output_callback(f"\n[{model_name}]", "model_name")
        
        response_text_chunks = []
        conversation_history = []  # Track the conversation with tool calls
        
        try:
            # Get tool definitions
            tools = self.tool_registry.get_tool_definitions()
            
            # Initial request
            current_prompt = prompt
            tool_calls_made = []
            
            # Get response with tool support - rate limiting handled by provider
            async for chunk in provider.generate_response(
                current_prompt, system_message, stream=self.config.stream, tools=tools
            ):
                # Handle text chunks
                if chunk.text:
                    response_text_chunks.append(chunk.text)
                    if self.config.stream and not self.config.summary_only:
                        print(chunk.text, end='', flush=True)
                
                # Handle tool calls
                if chunk.tool_calls:
                    tool_calls_made.extend(chunk.tool_calls)
            
            # If tools were called, execute them and get a follow-up response
            if tool_calls_made:
                tool_results_text = []
                
                for tool_call in tool_calls_made:
                    if not self.config.summary_only:
                        print(f"\n🔧 Using tool: {tool_call.name}({tool_call.arguments})", flush=True)
                    
                    # Execute the tool
                    tool_result = await self.tool_registry.execute_tool(
                        tool_call.name,
                        tool_call.arguments
                    )
                    
                    tool_results_text.append(f"Tool '{tool_call.name}' result: {tool_result}")
                    
                    if not self.config.summary_only:
                        print(f"✓ Tool result received\n", flush=True)
                
                # Create a follow-up prompt with tool results
                initial_response = "".join(response_text_chunks).strip()
                tool_results_combined = "\n\n".join(tool_results_text)
                
                follow_up_prompt = f"""You previously requested to use tools to answer this question:
{prompt}

Tool Results:
{tool_results_combined}

Now, please provide a clear, direct answer to the question based on these tool results. Be concise and specific."""
                
                # Clear the response chunks for the follow-up
                response_text_chunks = []
                
                # Get follow-up response WITHOUT tools (to avoid loops)
                async for chunk in provider.generate_response(
                    follow_up_prompt, system_message, stream=self.config.stream, tools=None
                ):
                    if chunk.text:
                        response_text_chunks.append(chunk.text)
                        if self.config.stream and not self.config.summary_only:
                            print(chunk.text, end='', flush=True)
            
            if not self.config.summary_only:
                print()  # Newline after streaming
            
            # Return the final response
            full_response = "".join(response_text_chunks).strip()
            
            # If somehow we still have no text, add the tool results directly
            if not full_response and tool_calls_made:
                full_response = "Tool results: " + "\n".join(tool_results_text)
            
            return ModelResponse(
                model_id=model_id,
                model_name=model_name,
                response=full_response,
                round_number=round_number
            )
            
        except Exception as e:
            raise ProviderError(f"Error from {model_name}: {str(e)}")
    
    async def _synthesize_consensus(
        self,
        question: str,
        final_responses: Dict[str, str]
    ) -> str:
        """
        Synthesize final consensus from all responses.
        
        Args:
            question: Original question
            final_responses: Final round responses from all models
            
        Returns:
            Synthesized consensus answer
        """
        # Use first available provider to synthesize
        provider = list(self.providers.values())[0]
        
        # Create synthesis prompt
        responses_dict = {
            self.model_configs[model_id].display_name: response
            for model_id, response in final_responses.items()
            if response
        }
        
        prompt = PromptTemplate.synthesis_prompt(question, responses_dict)
        system_message = PromptTemplate.format_system_message("synthesizer")
        
        self.output_callback("Final Consensus:", "consensus_header")
        self.output_callback("─" * 80, "separator")
        
        # Get tool definitions for synthesis (models may want to verify facts)
        tools = self.tool_registry.get_tool_definitions()
        
        response_text_chunks = []
        tool_calls_made = []
        
        # Initial synthesis request
        async for chunk in provider.generate_response(
            prompt, system_message, stream=self.config.stream, tools=tools
        ):
            # Handle text chunks
            if chunk.text:
                response_text_chunks.append(chunk.text)
                if self.config.stream:
                    print(chunk.text, end='', flush=True)
            
            # Handle tool calls
            if chunk.tool_calls:
                tool_calls_made.extend(chunk.tool_calls)
        
        # If tools were called, execute them and get a follow-up response
        if tool_calls_made:
            tool_results_text = []
            
            for tool_call in tool_calls_made:
                print(f"\n🔧 Using tool: {tool_call.name}({tool_call.arguments})", flush=True)
                
                # Execute the tool
                tool_result = await self.tool_registry.execute_tool(
                    tool_call.name,
                    tool_call.arguments
                )
                
                tool_results_text.append(f"Tool '{tool_call.name}' result: {tool_result}")
                print(f"✓ Tool result received\n", flush=True)
            
            # Create a follow-up prompt with tool results
            tool_results_combined = "\n\n".join(tool_results_text)
            
            follow_up_prompt = f"""You are synthesizing a consensus answer for this question:
{question}

Based on the models' responses, you requested tool data. Here are the tool results:
{tool_results_combined}

Now, please provide a clear, final consensus answer based on these tool results and the previous model responses. Be concise and specific."""
            
            # Clear the response chunks for the follow-up
            response_text_chunks = []
            
            # Get follow-up response WITHOUT tools
            async for chunk in provider.generate_response(
                follow_up_prompt, system_message, stream=self.config.stream, tools=None
            ):
                if chunk.text:
                    response_text_chunks.append(chunk.text)
                    if self.config.stream:
                        print(chunk.text, end='', flush=True)
        
        print()  # Newline after streaming
        
        # Return the final response
        full_response = "".join(response_text_chunks).strip()
        
        # If somehow we still have no text, add the tool results directly
        if not full_response and tool_calls_made:
            full_response = "Tool results: " + "\n".join(tool_results_text)
        
        return full_response
    
    def _default_output(self, message: str, msg_type: str = "info"):
        """
        Default output callback.
        
        Args:
            message: Message to output
            msg_type: Type of message (for formatting)
        """
        if self.config.summary_only and msg_type not in ["consensus_header", "header", "success"]:
            return
        
        # Simple output - can be enhanced with colors
        if msg_type in ["header", "round_header", "consensus_header"]:
            print(f"\033[1m{message}\033[0m")  # Bold
        elif msg_type == "model_name":
            print(f"\033[94m{message}\033[0m")  # Blue
        elif msg_type == "error":
            print(f"\033[91m{message}\033[0m")  # Red
        elif msg_type == "warning":
            print(f"\033[93m{message}\033[0m")  # Yellow
        elif msg_type == "success":
            print(f"\033[92m{message}\033[0m")  # Green
        else:
            print(message)
