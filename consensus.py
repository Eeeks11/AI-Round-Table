"""Consensus detection logic for multi-model deliberation."""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import re


@dataclass
class ConsensusMetrics:
    """Metrics for consensus analysis."""
    
    convergence_score: float  # 0.0 to 1.0
    agreement_level: str  # "high", "medium", "low"
    key_agreements: List[str]
    key_disagreements: List[str]
    has_consensus: bool
    
    def __str__(self) -> str:
        """String representation of consensus metrics."""
        return (
            f"Convergence: {self.convergence_score:.2%}\n"
            f"Agreement Level: {self.agreement_level}\n"
            f"Consensus Reached: {'Yes' if self.has_consensus else 'No'}"
        )


class ConsensusDetector:
    """Detects consensus in multi-model deliberations."""
    
    def __init__(self, threshold: float = 0.75):
        """
        Initialize consensus detector.
        
        Args:
            threshold: Convergence threshold for consensus (0.0 to 1.0)
        """
        self.threshold = threshold
    
    def analyze_consensus(
        self,
        responses_by_round: List[Dict[str, str]],
        model_names: List[str]
    ) -> ConsensusMetrics:
        """
        Analyze responses across rounds to detect consensus.
        
        Args:
            responses_by_round: List of dictionaries mapping model names to responses for each round
            model_names: List of model names participating
            
        Returns:
            ConsensusMetrics object with analysis results
        """
        if len(responses_by_round) < 2:
            return ConsensusMetrics(
                convergence_score=0.0,
                agreement_level="insufficient_data",
                key_agreements=[],
                key_disagreements=[],
                has_consensus=False
            )
        
        # Calculate convergence score based on multiple factors
        convergence_score = self._calculate_convergence(responses_by_round, model_names)
        
        # Determine agreement level
        if convergence_score >= 0.8:
            agreement_level = "high"
        elif convergence_score >= 0.6:
            agreement_level = "medium"
        else:
            agreement_level = "low"
        
        # Extract key agreements and disagreements from final round
        final_responses = responses_by_round[-1]
        key_agreements = self._find_common_themes(final_responses)
        key_disagreements = self._find_disagreements(final_responses)
        
        # Determine if consensus reached
        has_consensus = convergence_score >= self.threshold
        
        return ConsensusMetrics(
            convergence_score=convergence_score,
            agreement_level=agreement_level,
            key_agreements=key_agreements,
            key_disagreements=key_disagreements,
            has_consensus=has_consensus
        )
    
    def _calculate_convergence(
        self,
        responses_by_round: List[Dict[str, str]],
        model_names: List[str]
    ) -> float:
        """
        Calculate convergence score across rounds.
        
        Args:
            responses_by_round: List of response dictionaries
            model_names: List of model names
            
        Returns:
            Convergence score between 0.0 and 1.0
        """
        scores = []
        
        # Check if models are referencing each other more over time
        reference_score = self._calculate_cross_reference_score(responses_by_round, model_names)
        scores.append(reference_score)
        
        # Check if response lengths are stabilizing
        stability_score = self._calculate_stability_score(responses_by_round, model_names)
        scores.append(stability_score)
        
        # Check for common keywords and phrases
        keyword_score = self._calculate_keyword_overlap(responses_by_round[-1])
        scores.append(keyword_score)
        
        # Check for agreement language
        agreement_score = self._calculate_agreement_language_score(responses_by_round[-1])
        scores.append(agreement_score)
        
        # Average all scores
        return sum(scores) / len(scores)
    
    def _calculate_cross_reference_score(
        self,
        responses_by_round: List[Dict[str, str]],
        model_names: List[str]
    ) -> float:
        """Calculate score based on models referencing each other."""
        if len(responses_by_round) < 2:
            return 0.0
        
        # Count references to other models in later rounds
        reference_count = 0
        total_checks = 0
        
        for round_idx in range(1, len(responses_by_round)):
            for model_name, response in responses_by_round[round_idx].items():
                response_lower = response.lower()
                total_checks += 1
                
                # Check for references to other models or their points
                reference_patterns = [
                    "agree", "mentioned", "pointed out", "noted",
                    "building on", "as stated", "similarly", "likewise"
                ]
                
                if any(pattern in response_lower for pattern in reference_patterns):
                    reference_count += 1
        
        return reference_count / total_checks if total_checks > 0 else 0.0
    
    def _calculate_stability_score(
        self,
        responses_by_round: List[Dict[str, str]],
        model_names: List[str]
    ) -> float:
        """Calculate score based on response stability between rounds."""
        if len(responses_by_round) < 2:
            return 0.0
        
        # Compare last two rounds
        last_round = responses_by_round[-1]
        prev_round = responses_by_round[-2]
        
        stability_scores = []
        
        for model_name in model_names:
            if model_name in last_round and model_name in prev_round:
                # Simple heuristic: if responses are similar length and share keywords,
                # positions are stabilizing
                last_words = set(self._extract_keywords(last_round[model_name]))
                prev_words = set(self._extract_keywords(prev_round[model_name]))
                
                if len(last_words) > 0:
                    overlap = len(last_words & prev_words) / len(last_words)
                    stability_scores.append(overlap)
        
        return sum(stability_scores) / len(stability_scores) if stability_scores else 0.5
    
    def _calculate_keyword_overlap(self, responses: Dict[str, str]) -> float:
        """Calculate keyword overlap across all responses."""
        if len(responses) < 2:
            return 0.0
        
        # Extract keywords from each response
        keyword_sets = []
        for response in responses.values():
            keywords = set(self._extract_keywords(response))
            keyword_sets.append(keywords)
        
        # Calculate average pairwise overlap
        overlaps = []
        for i in range(len(keyword_sets)):
            for j in range(i + 1, len(keyword_sets)):
                set1, set2 = keyword_sets[i], keyword_sets[j]
                if len(set1) > 0 and len(set2) > 0:
                    overlap = len(set1 & set2) / min(len(set1), len(set2))
                    overlaps.append(overlap)
        
        return sum(overlaps) / len(overlaps) if overlaps else 0.0
    
    def _calculate_agreement_language_score(self, responses: Dict[str, str]) -> float:
        """Calculate score based on agreement language used."""
        agreement_patterns = [
            r'\bagree\b', r'\bconsensus\b', r'\bconcur\b',
            r'\bsimilarly\b', r'\blikewise\b', r'\balign\b',
            r'\bshared view\b', r'\bcommon ground\b'
        ]
        
        total_score = 0
        for response in responses.values():
            response_lower = response.lower()
            matches = sum(
                len(re.findall(pattern, response_lower))
                for pattern in agreement_patterns
            )
            # Normalize by response length (per 100 words)
            words = len(response_lower.split())
            if words > 0:
                total_score += min(matches / (words / 100), 1.0)
        
        return total_score / len(responses) if responses else 0.0
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract meaningful keywords from text.
        
        Args:
            text: Input text
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction: lowercase words, filter common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # Extract words (lowercase, alphanumeric only)
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Filter stop words and short words
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        return keywords
    
    def _find_common_themes(self, responses: Dict[str, str]) -> List[str]:
        """
        Find common themes across responses.
        
        Args:
            responses: Dictionary of model responses
            
        Returns:
            List of common themes
        """
        # Extract keywords from all responses
        all_keywords = []
        for response in responses.values():
            all_keywords.extend(self._extract_keywords(response))
        
        # Count keyword frequencies
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Find keywords that appear in multiple responses
        num_models = len(responses)
        common_threshold = max(2, num_models // 2)  # At least half of models
        
        common_themes = [
            keyword for keyword, count in keyword_counts.items()
            if count >= common_threshold
        ]
        
        # Return top themes
        return sorted(common_themes, key=lambda k: keyword_counts[k], reverse=True)[:5]
    
    def _find_disagreements(self, responses: Dict[str, str]) -> List[str]:
        """
        Find potential points of disagreement.
        
        Args:
            responses: Dictionary of model responses
            
        Returns:
            List of disagreement indicators
        """
        disagreement_indicators = []
        
        disagreement_patterns = [
            r'\bdisagree\b', r'\bhowever\b', r'\balthough\b',
            r'\bdifferent view\b', r'\bon the other hand\b',
            r'\bcontrast\b', r'\bbut\b', r'\balternatively\b'
        ]
        
        for model_name, response in responses.items():
            response_lower = response.lower()
            for pattern in disagreement_patterns:
                if re.search(pattern, response_lower):
                    # Extract sentence containing disagreement
                    sentences = response.split('.')
                    for sentence in sentences:
                        if re.search(pattern, sentence.lower()):
                            disagreement_indicators.append(
                                f"{model_name}: {sentence.strip()[:100]}..."
                            )
                            break
                    break
        
        return disagreement_indicators[:3]  # Return top 3
