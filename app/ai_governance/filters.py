"""
AI Content Filters

These filters analyze and control AI-generated content
"""

import re
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any
from django.conf import settings
import logging

logger = logging.getLogger('ai_governance')


class BaseContentFilter(ABC):
    """Base class for all content filters"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.threshold = self.config.get('threshold', 0.5)
        self.is_active = self.config.get('is_active', True)

    @abstractmethod
    def filter_prompt(self, prompt: str, context: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Filter input prompt
        Returns: (is_allowed, modified_prompt, metadata)
        """
        pass

    @abstractmethod
    def filter_response(self, response: str, context: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Filter AI response
        Returns: (is_allowed, modified_response, metadata)
        """
        pass


class ProfanityFilter(BaseContentFilter):
    """Filter for profanity and inappropriate content"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.profanity_words = self._load_profanity_words()
        self.severity_levels = {
            'mild': 0.3,
            'moderate': 0.6,
            'severe': 0.9
        }

    def _load_profanity_words(self) -> Dict[str, float]:
        """Load profanity words with severity scores"""
        # Arabic profanity words with severity scores
        arabic_words = {
            # Add Arabic profanity words here with severity scores
            'كلب': 0.4,
            'حمار': 0.3,
            # Add more words as needed
        }
        
        # English profanity words
        english_words = {
            'damn': 0.3,
            'hell': 0.3,
            'stupid': 0.4,
            # Add more words as needed
        }
        
        return {**arabic_words, **english_words}

    def filter_prompt(self, prompt: str, context: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Filter input prompt for profanity"""
        score, detected_words = self._calculate_profanity_score(prompt)
        
        metadata = {
            'profanity_score': score,
            'detected_words': detected_words,
            'filter_type': 'profanity_prompt'
        }
        
        if score > self.threshold:
            logger.warning(f"Profanity detected in prompt: {detected_words}")
            return False, "", metadata
        
        # Clean the prompt by replacing mild profanity
        cleaned_prompt = self._clean_text(prompt, detected_words)
        return True, cleaned_prompt, metadata

    def filter_response(self, response: str, context: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Filter AI response for profanity"""
        score, detected_words = self._calculate_profanity_score(response)
        
        metadata = {
            'profanity_score': score,
            'detected_words': detected_words,
            'filter_type': 'profanity_response'
        }
        
        if score > self.threshold:
            logger.warning(f"Profanity detected in response: {detected_words}")
            return False, "عذراً، لا يمكنني تقديم هذا المحتوى.", metadata
        
        # Clean the response
        cleaned_response = self._clean_text(response, detected_words)
        return True, cleaned_response, metadata

    def _calculate_profanity_score(self, text: str) -> Tuple[float, List[str]]:
        """Calculate profanity score for text"""
        text_lower = text.lower()
        detected_words = []
        total_score = 0.0
        
        for word, severity in self.profanity_words.items():
            if word in text_lower:
                detected_words.append(word)
                total_score += severity
        
        # Normalize score
        max_possible_score = len(detected_words) * 1.0
        normalized_score = min(total_score / max(max_possible_score, 1), 1.0)
        
        return normalized_score, detected_words

    def _clean_text(self, text: str, detected_words: List[str]) -> str:
        """Clean text by replacing mild profanity"""
        cleaned_text = text
        for word in detected_words:
            if self.profanity_words[word] <= 0.4:  # Only clean mild profanity
                cleaned_text = re.sub(
                    re.escape(word), 
                    '*' * len(word), 
                    cleaned_text, 
                    flags=re.IGNORECASE
                )
        return cleaned_text


class BiasDetectionFilter(BaseContentFilter):
    """Filter for detecting and mitigating bias in AI responses"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.bias_patterns = self._load_bias_patterns()

    def _load_bias_patterns(self) -> Dict[str, List[str]]:
        """Load bias detection patterns"""
        return {
            'gender_bias': [
                r'\b(رجال|نساء)\s+(أفضل|أسوأ)\s+في\b',
                r'\b(الرجل|المرأة)\s+(يجب|لا يجب)\b',
            ],
            'racial_bias': [
                r'\b(العرب|الأجانب)\s+(دائماً|أبداً)\b',
                r'\b(هذا العرق|تلك الجنسية)\s+(معروف|مشهور)\s+بـ\b',
            ],
            'religious_bias': [
                r'\b(المسلمون|المسيحيون|اليهود)\s+(كلهم|جميعهم)\b',
                r'\b(هذا الدين|تلك الطائفة)\s+(يعلم|يحرم)\b',
            ],
            'age_bias': [
                r'\b(الشباب|كبار السن)\s+(لا يفهمون|لا يستطيعون)\b',
                r'\b(في هذا العمر|الجيل الجديد)\s+(دائماً|أبداً)\b',
            ]
        }

    def filter_prompt(self, prompt: str, context: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Filter prompt for bias indicators"""
        bias_score, detected_biases = self._detect_bias(prompt)
        
        metadata = {
            'bias_score': bias_score,
            'detected_biases': detected_biases,
            'filter_type': 'bias_prompt'
        }
        
        if bias_score > self.threshold:
            logger.warning(f"Bias detected in prompt: {detected_biases}")
            # Add bias warning to context instead of blocking
            modified_prompt = f"{prompt}\n\n[تنبيه: يرجى تجنب التعميمات والأحكام المسبقة في الإجابة]"
            return True, modified_prompt, metadata
        
        return True, prompt, metadata

    def filter_response(self, response: str, context: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Filter response for bias"""
        bias_score, detected_biases = self._detect_bias(response)
        
        metadata = {
            'bias_score': bias_score,
            'detected_biases': detected_biases,
            'filter_type': 'bias_response'
        }
        
        if bias_score > self.threshold:
            logger.warning(f"Bias detected in response: {detected_biases}")
            # Modify response to add disclaimer
            modified_response = f"{response}\n\n⚠️ تنبيه: هذه الإجابة قد تحتوي على تعميمات. يرجى مراعاة التنوع والاختلافات الفردية."
            return True, modified_response, metadata
        
        return True, response, metadata

    def _detect_bias(self, text: str) -> Tuple[float, Dict[str, List[str]]]:
        """Detect bias patterns in text"""
        detected_biases = {}
        total_matches = 0
        
        for bias_type, patterns in self.bias_patterns.items():
            matches = []
            for pattern in patterns:
                found_matches = re.findall(pattern, text, re.IGNORECASE)
                if found_matches:
                    matches.extend(found_matches)
                    total_matches += len(found_matches)
            
            if matches:
                detected_biases[bias_type] = matches
        
        # Calculate bias score based on number of matches
        bias_score = min(total_matches * 0.2, 1.0)
        
        return bias_score, detected_biases


class FactCheckFilter(BaseContentFilter):
    """Filter for basic fact checking and misinformation detection"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.suspicious_patterns = self._load_suspicious_patterns()

    def _load_suspicious_patterns(self) -> List[str]:
        """Load patterns that might indicate misinformation"""
        return [
            r'\b(أثبتت الدراسات|العلماء يؤكدون)\b.*\b(بنسبة 100%|مؤكد تماماً)\b',
            r'\b(كل|جميع)\s+(الأطباء|العلماء|الخبراء)\s+(يتفقون|يؤكدون)\b',
            r'\b(هذا سر|الحقيقة المخفية|لا يريدون منك أن تعرف)\b',
            r'\b(علاج نهائي|شفاء فوري|نتائج مضمونة)\b',
        ]

    def filter_prompt(self, prompt: str, context: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Filter prompt for fact-check indicators"""
        suspicion_score, detected_patterns = self._check_suspicious_content(prompt)
        
        metadata = {
            'suspicion_score': suspicion_score,
            'detected_patterns': detected_patterns,
            'filter_type': 'factcheck_prompt'
        }
        
        if suspicion_score > self.threshold:
            # Add fact-checking reminder to prompt
            modified_prompt = f"{prompt}\n\n[تنبيه: يرجى التأكد من دقة المعلومات وذكر المصادر عند الإمكان]"
            return True, modified_prompt, metadata
        
        return True, prompt, metadata

    def filter_response(self, response: str, context: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Filter response for potential misinformation"""
        suspicion_score, detected_patterns = self._check_suspicious_content(response)
        
        metadata = {
            'suspicion_score': suspicion_score,
            'detected_patterns': detected_patterns,
            'filter_type': 'factcheck_response'
        }
        
        if suspicion_score > self.threshold:
            # Add fact-checking disclaimer
            modified_response = f"{response}\n\n📋 ملاحظة: يرجى التحقق من هذه المعلومات من مصادر موثوقة قبل الاعتماد عليها."
            return True, modified_response, metadata
        
        return True, response, metadata

    def _check_suspicious_content(self, text: str) -> Tuple[float, List[str]]:
        """Check for suspicious content patterns"""
        detected_patterns = []
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected_patterns.append(pattern)
        
        # Calculate suspicion score
        suspicion_score = min(len(detected_patterns) * 0.3, 1.0)
        
        return suspicion_score, detected_patterns


class ContentFilterManager:
    """Manager class for coordinating multiple content filters"""
    
    def __init__(self):
        self.filters = []
        self._load_filters()

    def _load_filters(self):
        """Load and initialize all content filters"""
        filter_configs = getattr(settings, 'AI_GOVERNANCE', {}).get('CONTENT_FILTERS', [])
        
        filter_classes = {
            'app.ai_governance.filters.ProfanityFilter': ProfanityFilter,
            'app.ai_governance.filters.BiasDetectionFilter': BiasDetectionFilter,
            'app.ai_governance.filters.FactCheckFilter': FactCheckFilter,
        }
        
        for filter_path in filter_configs:
            if filter_path in filter_classes:
                filter_class = filter_classes[filter_path]
                self.filters.append(filter_class())

    def filter_prompt(self, prompt: str, context: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Apply all filters to prompt"""
        current_prompt = prompt
        all_metadata = {}
        
        for filter_instance in self.filters:
            if not filter_instance.is_active:
                continue
                
            is_allowed, modified_prompt, metadata = filter_instance.filter_prompt(current_prompt, context)
            
            # Merge metadata
            all_metadata.update(metadata)
            
            if not is_allowed:
                return False, "", all_metadata
            
            current_prompt = modified_prompt
        
        return True, current_prompt, all_metadata

    def filter_response(self, response: str, context: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Apply all filters to response"""
        current_response = response
        all_metadata = {}
        
        for filter_instance in self.filters:
            if not filter_instance.is_active:
                continue
                
            is_allowed, modified_response, metadata = filter_instance.filter_response(current_response, context)
            
            # Merge metadata
            all_metadata.update(metadata)
            
            if not is_allowed:
                return False, "عذراً، لا يمكنني تقديم هذا المحتوى.", all_metadata
            
            current_response = modified_response
        
        return True, current_response, all_metadata
