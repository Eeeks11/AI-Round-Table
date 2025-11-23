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
        if len(responses_by_round) < 1:
            return ConsensusMetrics(
                convergence_score=0.0,
                agreement_level="insufficient_data",
                key_agreements=[],
                key_disagreements=[],
                has_consensus=False
            )
        
        # For single round, check if all models agree on factual content
        if len(responses_by_round) == 1:
            final_responses = responses_by_round[0]
            
            # Check factual agreement (dates, numbers, etc.)
            factual_score = self._calculate_core_answer_consistency(final_responses)
            
            # For first round, we need strong factual agreement to claim consensus
            if factual_score >= 0.95:
                key_agreements = self._find_common_themes(final_responses)
                return ConsensusMetrics(
                    convergence_score=factual_score,
                    agreement_level="high",
                    key_agreements=key_agreements,
                    key_disagreements=[],
                    has_consensus=True
                )
            
            # Otherwise, need more rounds to establish consensus
            return ConsensusMetrics(
                convergence_score=factual_score,
                agreement_level="low" if factual_score < 0.55 else "medium",
                key_agreements=self._find_common_themes(final_responses),
                key_disagreements=[],
                has_consensus=False
            )
        
        # Calculate convergence score based on multiple factors
        convergence_score = self._calculate_convergence(responses_by_round, model_names)
        
        # Determine agreement level
        if convergence_score >= 0.75:
            agreement_level = "high"
        elif convergence_score >= 0.55:
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
        weights = []
        
        # Check for explicit consensus/agreement language (high weight)
        agreement_score = self._calculate_agreement_language_score(responses_by_round[-1])
        scores.append(agreement_score)
        weights.append(2.5)  # Highest weight - explicit agreement is strong signal
        
        # Check for consistent core answers (high weight)
        core_answer_score = self._calculate_core_answer_consistency(responses_by_round[-1])
        scores.append(core_answer_score)
        weights.append(2.0)  # High weight - semantic consistency matters most
        
        # Check if models are referencing each other more over time (medium-high weight)
        reference_score = self._calculate_cross_reference_score(responses_by_round, model_names)
        scores.append(reference_score)
        weights.append(1.5)  # Medium-high weight
        
        # Check if response lengths are stabilizing (medium weight)
        stability_score = self._calculate_stability_score(responses_by_round, model_names)
        scores.append(stability_score)
        weights.append(1.0)  # Medium weight
        
        # Check for common keywords and phrases (low weight)
        keyword_score = self._calculate_keyword_overlap(responses_by_round[-1])
        scores.append(keyword_score)
        weights.append(0.5)  # Low weight - vocabulary can differ even with agreement
        
        # Calculate weighted average
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        return weighted_sum / total_weight
    
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
            r'\bshared view\b', r'\bcommon ground\b',
            r'\bstrong alignment\b', r'\bfully endorse\b',
            r'\bsame conclusion\b', r'\bno disagreement\b',
            r'\bcomplete agreement\b', r'\bunanimously\b'
        ]
        
        total_score = 0
        num_with_agreement = 0
        
        for response in responses.values():
            response_lower = response.lower()
            matches = sum(
                len(re.findall(pattern, response_lower))
                for pattern in agreement_patterns
            )
            
            if matches > 0:
                num_with_agreement += 1
                # Cap individual score at 1.0 to avoid over-weighting verbose responses
                words = len(response_lower.split())
                if words > 0:
                    # Higher density of agreement language = higher score
                    score = min(matches / max(words / 200, 1.0), 1.0)
                    total_score += score
        
        # If most models show agreement language, boost the score
        if num_with_agreement >= len(responses) * 0.6:  # 60% or more
            total_score *= 1.2
        
        return min(total_score / len(responses), 1.0) if responses else 0.0
    
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
    
    def _calculate_core_answer_consistency(self, responses: Dict[str, str]) -> float:
        """
        Calculate consistency of core answers across responses.
        Looks for consistent YES/NO answers, dates, numbers, or shared factual patterns.
        
        Args:
            responses: Dictionary of model responses
            
        Returns:
            Consistency score between 0.0 and 1.0
        """
        if len(responses) < 2:
            return 0.5
        
        # First, try to extract factual data (dates, numbers, specific facts)
        factual_consistency = self._check_factual_agreement(responses)
        if factual_consistency >= 0.9:  # High factual agreement found
            return factual_consistency
        
        # Extract initial answer patterns from each response
        answer_patterns = []
        
        for response in responses.values():
            response_lower = response.lower()
            # Get first 300 chars where the core answer usually is
            initial_text = response_lower[:300]
            
            # Detect affirmative/negative/neutral patterns
            yes_score = sum([
                initial_text.count('yes'),
                initial_text.count('correct'),
                initial_text.count('true'),
                initial_text.count('i can'),
                initial_text.count('i am able')
            ])
            
            no_score = sum([
                initial_text.count('no'),
                initial_text.count('not'),
                initial_text.count('cannot'),
                initial_text.count('unable'),
                initial_text.count('don\'t'),
                initial_text.count('do not')
            ])
            
            maybe_score = sum([
                initial_text.count('depends'),
                initial_text.count('partially'),
                initial_text.count('sometimes'),
                initial_text.count('it varies')
            ])
            
            # Classify the answer
            max_score = max(yes_score, no_score, maybe_score)
            if max_score == 0:
                answer_patterns.append('neutral')
            elif yes_score == max_score:
                answer_patterns.append('yes')
            elif no_score == max_score:
                answer_patterns.append('no')
            else:
                answer_patterns.append('maybe')
        
        # Calculate consistency: how many responses have the same pattern
        from collections import Counter
        pattern_counts = Counter(answer_patterns)
        most_common_count = pattern_counts.most_common(1)[0][1] if pattern_counts else 0
        consistency_ratio = most_common_count / len(answer_patterns)
        
        # Bonus for unanimous agreement
        if consistency_ratio == 1.0:
            return 1.0
        
        # Use the higher of factual or pattern consistency
        return max(consistency_ratio, factual_consistency)
    
    def _check_factual_agreement(self, responses: Dict[str, str]) -> float:
        """
        Check if responses agree on core factual data like dates, numbers, names, etc.
        
        Args:
            responses: Dictionary of model responses
            
        Returns:
            Score between 0.0 and 1.0 indicating factual agreement
        """
        if len(responses) < 2:
            return 0.5
        
        # Extract dates from all responses
        dates = []
        for response in responses.values():
            extracted_dates = self._extract_dates(response)
            if extracted_dates:
                dates.append(extracted_dates[0])  # Use first date found
        
        # If all responses mention the same date, that's perfect consensus
        if len(dates) >= 2 and len(set(dates)) == 1:
            # All models agree on the same date
            return 1.0
        
        # Extract numbers (prices, quantities, etc.)
        numbers = []
        for response in responses.values():
            extracted_numbers = self._extract_numbers(response)
            if extracted_numbers:
                numbers.extend(extracted_numbers)
        
        # Check if key numbers are consistent
        if numbers:
            from collections import Counter
            number_counts = Counter(numbers)
            most_common_count = number_counts.most_common(1)[0][1] if number_counts else 0
            if most_common_count >= len(responses) * 0.8:  # 80% mention same number
                return 0.95
        
        # Extract key proper nouns/entities
        entities = []
        for response in responses.values():
            extracted_entities = self._extract_entities(response)
            entities.extend(extracted_entities)
        
        if entities:
            from collections import Counter
            entity_counts = Counter(entities)
            # Check if responses share key entities
            common_entities = sum(1 for count in entity_counts.values() if count >= len(responses) * 0.7)
            if common_entities >= 2:
                return 0.85
        
        return 0.0  # No clear factual agreement detected
    
    def _extract_dates(self, text: str) -> List[str]:
        """
        Extract dates from text in various formats.
        
        Args:
            text: Input text
            
        Returns:
            List of normalized date strings
        """
        import re
        dates = []
        
        # Match patterns like: November 23, 2025 / 23 November 2025 / 2025-11-23
        patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2025-11-23
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 23-11-2025
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December))\s+(\d{1,2}),?\s+(\d{4})',  # November 23, 2025
            r'(\d{1,2})\s+((?:January|February|March|April|May|June|July|August|September|October|November|December))\s+(\d{4})',  # 23 November 2025
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Normalize to YYYY-MM-DD format
                try:
                    if re.match(r'\d{4}-\d{1,2}-\d{1,2}', '-'.join(match)):
                        dates.append('-'.join(match))
                    else:
                        # Convert month names to numbers
                        month_map = {
                            'january': '01', 'february': '02', 'march': '03', 'april': '04',
                            'may': '05', 'june': '06', 'july': '07', 'august': '08',
                            'september': '09', 'october': '10', 'november': '11', 'december': '12'
                        }
                        
                        if len(match) == 3:
                            month_str = match[0] if match[0].lower() in month_map else match[1]
                            month_num = month_map.get(month_str.lower(), '01')
                            
                            # Find day and year
                            day = match[1] if match[1].isdigit() else match[0]
                            year = match[2] if len(match[2]) == 4 else match[0]
                            
                            if year.isdigit() and len(year) == 4:
                                normalized = f"{year}-{month_num}-{day.zfill(2)}"
                                dates.append(normalized)
                except:
                    pass
        
        return dates
    
    def _extract_numbers(self, text: str) -> List[str]:
        """
        Extract significant numbers from text (prices, quantities, etc.).
        
        Args:
            text: Input text
            
        Returns:
            List of number strings
        """
        import re
        
        # Match numbers with optional currency symbols, decimals, commas
        patterns = [
            r'\$[\d,]+\.?\d*',  # $123.45 or $1,234
            r'£[\d,]+\.?\d*',  # £123.45
            r'€[\d,]+\.?\d*',  # €123.45
            r'\b\d+\.?\d*\s*(?:dollars?|euros?|pounds?|km|miles?|percent|%)\b',  # 123 dollars, 45.5 km
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers.extend(matches)
        
        return numbers
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract key proper nouns and entities (capitalized words).
        
        Args:
            text: Input text
            
        Returns:
            List of entity strings
        """
        import re
        
        # Extract capitalized words (likely proper nouns)
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter out common starting words and keep significant entities
        common_starts = {'The', 'This', 'That', 'These', 'Those', 'A', 'An', 'In', 'On', 'At', 'To', 'For'}
        entities = [e for e in entities if e not in common_starts]
        
        return entities[:10]  # Return top 10 entities
    
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
