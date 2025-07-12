import re
import asyncio
from typing import List, Dict, Any
import openai
from openai import AsyncOpenAI
import os
from datetime import datetime

class ContentCategorizer:
    def __init__(self):
        self.client = None
        self.initialized = False
        
        # Predefined categories with their characteristics
        self.categories = {
            "Ideas to Develop": {
                "keywords": ["idea", "concept", "thought", "think", "maybe", "what if", "could", "should", "vision", "future"],
                "patterns": [r"\b(idea|concept|thought)\b", r"\b(maybe|perhaps|possibly)\b", r"\?.*\?"],
                "description": "Incomplete thoughts and concepts that need development"
            },
            "Personal": {
                "keywords": ["i", "me", "my", "myself", "personal", "feel", "think", "believe", "experience"],
                "patterns": [r"\bi\s", r"\bme\b", r"\bmy\b", r"\bmyself\b"],
                "description": "Personal reflections and experiences"
            },
            "Research": {
                "keywords": ["research", "study", "paper", "article", "analysis", "findings", "results", "methodology"],
                "patterns": [r"\bresearch\b", r"\bstudy\b", r"\bpaper\b", r"\barticle\b"],
                "description": "Academic or professional research content"
            },
            "Reading List": {
                "keywords": ["http", "https", "www", "link", "article", "blog", "read", "check out"],
                "patterns": [r"https?://", r"www\.", r"\blink\b", r"\bread\b"],
                "description": "Links and articles to read later"
            },
            "Projects": {
                "keywords": ["project", "build", "create", "develop", "implement", "todo", "task", "goal"],
                "patterns": [r"\bproject\b", r"\bbuild\b", r"\bcreate\b", r"\btodo\b"],
                "description": "Project-related content"
            },
            "Learning": {
                "keywords": ["learn", "tutorial", "course", "lesson", "education", "skill", "knowledge", "understand"],
                "patterns": [r"\blearn\b", r"\btutorial\b", r"\bcourse\b", r"\blesson\b"],
                "description": "Educational content and notes"
            },
            "Quick Notes": {
                "keywords": ["note", "remember", "reminder", "quick", "brief"],
                "patterns": [r"\bnote\b", r"\bremember\b", r"\breminder\b"],
                "description": "Brief thoughts and reminders"
            }
        }
        
    async def initialize(self):
        """Initialize the categorizer"""
        if self.initialized:
            return
            
        # Initialize OpenAI client if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        
        self.initialized = True
        
    async def categorize(self, content: str) -> List[str]:
        """Categorize content using rule-based and AI-based approaches"""
        # Rule-based categorization
        rule_categories = await self._rule_based_categorization(content)
        
        # AI-based categorization if OpenAI is available
        if self.client:
            try:
                ai_categories = await self._ai_categorization(content)
                # Combine and deduplicate
                combined_categories = list(set(rule_categories + ai_categories))
                return combined_categories[:3]  # Return top 3 categories
            except Exception as e:
                print(f"AI categorization failed: {e}")
        
        return rule_categories[:2] if rule_categories else ["Quick Notes"]
    
    async def _rule_based_categorization(self, content: str) -> List[str]:
        """Rule-based categorization using keywords and patterns"""
        content_lower = content.lower()
        category_scores = {}
        
        for category, config in self.categories.items():
            score = 0
            
            # Check keywords
            for keyword in config["keywords"]:
                if keyword in content_lower:
                    score += 1
            
            # Check patterns
            for pattern in config["patterns"]:
                if re.search(pattern, content_lower):
                    score += 2  # Patterns are weighted higher
            
            # Special rules
            if category == "Reading List" and ("http" in content_lower or "www" in content_lower):
                score += 5
            
            if category == "Personal" and any(pronoun in content_lower for pronoun in ["i ", "me ", "my ", "myself"]):
                score += 3
            
            if category == "Ideas to Develop" and ("?" in content or len(content.split()) < 15):
                score += 2
            
            if category == "Quick Notes" and len(content.split()) < 10:
                score += 1
            
            category_scores[category] = score
        
        # Sort by score and return top categories
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, score in sorted_categories if score > 0]
    
    async def _ai_categorization(self, content: str) -> List[str]:
        """AI-based categorization using OpenAI"""
        if not self.client:
            return []
            
        try:
            categories_list = "\n".join([f"- {cat}: {config['description']}" for cat, config in self.categories.items()])
            
            prompt = f"""
            Categorize the following content into the most appropriate categories. 
            
            Available categories:
            {categories_list}
            
            Content: "{content}"
            
            Return only the category names, separated by commas. Choose 1-3 most relevant categories.
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3
            )
            
            if response.choices:
                categories_text = response.choices[0].message.content.strip()
                categories = [cat.strip() for cat in categories_text.split(',')]
                
                # Validate categories
                valid_categories = []
                for cat in categories:
                    if cat in self.categories:
                        valid_categories.append(cat)
                
                return valid_categories
                
        except Exception as e:
            print(f"OpenAI categorization error: {e}")
            
        return []
    
    async def get_category_suggestions(self, content: str) -> Dict[str, Any]:
        """Get detailed category suggestions with confidence scores"""
        content_lower = content.lower()
        suggestions = {}
        
        for category, config in self.categories.items():
            score = 0
            reasons = []
            
            # Check keywords
            found_keywords = []
            for keyword in config["keywords"]:
                if keyword in content_lower:
                    found_keywords.append(keyword)
                    score += 1
            
            if found_keywords:
                reasons.append(f"Contains keywords: {', '.join(found_keywords)}")
            
            # Check patterns
            found_patterns = []
            for pattern in config["patterns"]:
                if re.search(pattern, content_lower):
                    found_patterns.append(pattern)
                    score += 2
            
            if found_patterns:
                reasons.append(f"Matches patterns: {', '.join(found_patterns)}")
            
            # Special rules with explanations
            if category == "Reading List" and ("http" in content_lower or "www" in content_lower):
                score += 5
                reasons.append("Contains URLs")
            
            if category == "Personal" and any(pronoun in content_lower for pronoun in ["i ", "me ", "my ", "myself"]):
                score += 3
                reasons.append("Contains personal pronouns")
            
            if category == "Ideas to Develop" and ("?" in content or len(content.split()) < 15):
                score += 2
                reasons.append("Contains questions or is a brief thought")
            
            if category == "Quick Notes" and len(content.split()) < 10:
                score += 1
                reasons.append("Short content")
            
            if score > 0:
                suggestions[category] = {
                    "score": score,
                    "confidence": min(score / 10, 1.0),  # Normalize to 0-1
                    "reasons": reasons,
                    "description": config["description"]
                }
        
        return suggestions
    
    async def add_custom_category(self, name: str, keywords: List[str], patterns: List[str], description: str):
        """Add a custom category"""
        self.categories[name] = {
            "keywords": keywords,
            "patterns": patterns,
            "description": description
        }
    
    async def get_available_categories(self) -> Dict[str, str]:
        """Get all available categories and their descriptions"""
        return {name: config["description"] for name, config in self.categories.items()} 