"""
AI-powered risk evaluation using OpenAI
"""
import json
import re
from typing import Dict, Any, List
import hashlib

from openai import OpenAI

from configs.settings import settings


class RiskClassifier:
    """Rule-based risk classification for Bulgarian car listings"""
    
    # Red flag keywords in Bulgarian
    RED_FLAGS = {
        'accident': [
            'катастрофирал', 'катастрофа', 'удар', 'ударен', 'повреди от катастрофа',
            'accident', 'crashed', 'collision'
        ],
        'salvage': [
            'тотал', 'дерегистриран', 'бракуван', 'на части',
            'salvage', 'totaled', 'write-off', 'for parts'
        ],
        'import': [
            'нов внос', 'пресен внос', 'американски внос', 'от америка',
            'fresh import', 'imported from'
        ],
        'mileage_doubt': [
            'реални километри', 'неманипулиран километраж', 'верен километраж',
            'real mileage', 'original mileage'
        ],
        'urgent': [
            'спешно', 'бърза продажба', 'зле ми са парите', 'заминавам',
            'urgent', 'quick sale', 'need money'
        ],
        'cosmetic': [
            'драскотини', 'вдлъбнатини', 'нуждае се от бояджийски',
            'scratches', 'dents', 'needs bodywork'
        ],
    }
    
    # Positive indicators
    POSITIVE_FLAGS = {
        'maintenance': [
            'сервизна история', 'редовно обслужвана', 'на гаранция',
            'service history', 'well maintained', 'under warranty'
        ],
        'ownership': [
            'първи собственик', 'един собственик', 'личен автомобил',
            'first owner', 'one owner', 'personal use'
        ],
        'condition': [
            'перфектно състояние', 'отлично състояние', 'много запазена',
            'perfect condition', 'excellent condition', 'well preserved'
        ],
    }
    
    def classify(self, title: str, description: str) -> Dict[str, Any]:
        """
        Classify risk based on text analysis
        
        Args:
            title: Listing title
            description: Listing description
            
        Returns:
            Dictionary with flags, risk_level, and confidence
        """
        text = f"{title}\n{description}".lower()
        
        flags = {
            'red_flags': [],
            'positive_flags': [],
        }
        
        # Check for red flags
        for category, keywords in self.RED_FLAGS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    flags['red_flags'].append({
                        'category': category,
                        'keyword': keyword,
                    })
        
        # Check for positive flags
        for category, keywords in self.POSITIVE_FLAGS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    flags['positive_flags'].append({
                        'category': category,
                        'keyword': keyword,
                    })
        
        # Calculate risk level
        red_count = len(flags['red_flags'])
        positive_count = len(flags['positive_flags'])
        
        if red_count >= 3:
            risk_level = 'high'
            confidence = 0.8
        elif red_count >= 1:
            risk_level = 'medium'
            confidence = 0.6
        elif positive_count >= 2:
            risk_level = 'low'
            confidence = 0.7
        else:
            risk_level = 'low'
            confidence = 0.5
        
        return {
            'flags': flags,
            'risk_level': risk_level,
            'rule_confidence': confidence,
            'needs_llm': confidence < 0.7 or risk_level == 'medium',
        }


class LLMEvaluator:
    """LLM-based evaluation using OpenAI"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self._cache = {}
    
    def evaluate(
        self,
        title: str,
        description: str,
        price_bgn: float,
        predicted_price_bgn: float,
        discount_pct: float,
        rule_flags: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate listing using LLM
        
        Args:
            title: Listing title
            description: Listing description
            price_bgn: Asking price
            predicted_price_bgn: Market price estimate
            discount_pct: Discount percentage
            rule_flags: Flags from rule-based classifier
            
        Returns:
            Dictionary with risk_level, summary, confidence, and reasons
        """
        # Check cache
        cache_key = hashlib.md5(description.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Build prompt
        prompt = self._build_prompt(
            title, description, price_bgn,
            predicted_price_bgn, discount_pct, rule_flags
        )
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at evaluating used car listings in Bulgaria. "
                                   "Analyze the listing and identify potential risks or red flags."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            
            # Parse response
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Validate and normalize
            normalized_result = {
                'risk_level': result.get('risk_level', 'medium').lower(),
                'summary': result.get('summary', ''),
                'reasons': result.get('reasons', []),
                'buyer_notes': result.get('buyer_notes', ''),
                'llm_confidence': result.get('confidence', 0.7),
                'model_version': self.model,
            }
            
            # Cache result
            self._cache[cache_key] = normalized_result
            
            return normalized_result
            
        except Exception as e:
            # Fallback on error
            return {
                'risk_level': 'medium',
                'summary': f'LLM evaluation failed: {str(e)}',
                'reasons': [],
                'buyer_notes': '',
                'llm_confidence': 0.3,
                'model_version': self.model,
                'error': str(e),
            }
    
    def _build_prompt(
        self,
        title: str,
        description: str,
        price_bgn: float,
        predicted_price_bgn: float,
        discount_pct: float,
        rule_flags: Dict[str, Any],
    ) -> str:
        """Build evaluation prompt"""
        return f"""Analyze this Bulgarian used car listing:

**Title:** {title}

**Description:**
{description}

**Pricing:**
- Asking Price: {price_bgn:.0f} BGN
- Market Estimate: {predicted_price_bgn:.0f} BGN
- Discount: {discount_pct:.1f}%

**Initial Flags:**
- Red Flags: {len(rule_flags.get('red_flags', []))}
- Positive Flags: {len(rule_flags.get('positive_flags', []))}

Evaluate this listing and provide your assessment in JSON format:

{{
  "risk_level": "low|medium|high",
  "confidence": 0.0-1.0,
  "summary": "2-3 sentence summary in Bulgarian",
  "reasons": ["reason 1", "reason 2", "reason 3"],
  "buyer_notes": "Important notes for potential buyers"
}}

Consider:
1. Signs of accident damage or salvage title
2. Mileage authenticity concerns
3. Import history red flags
4. Maintenance and ownership claims
5. Pricing relative to market (why such discount?)
6. Urgency or pressure tactics
7. Overly positive language (too good to be true)

Focus on Bulgarian-specific patterns and scams."""
