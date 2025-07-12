import re
import asyncio
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
import markdown
from datetime import datetime
import json
import os

class ContentProcessor:
    def __init__(self):
        self.initialized = False
        self.http_client = None
        
    async def initialize(self):
        """Initialize the content processor"""
        if self.initialized:
            return
            
        # Initialize HTTP client for web scraping
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        
        self.initialized = True
    
    async def extract_content(self, text: str) -> Dict[str, Any]:
        """Extract structured information from text content"""
        extracted = {
            "text": text,
            "type": "text",
            "has_links": False,
            "has_meaningful_content": True,
            "metadata": {},
            "extracted_at": datetime.now().isoformat()
        }
        
        # Detect content type
        content_type = await self._detect_content_type(text)
        extracted["type"] = content_type
        
        # Extract URLs
        urls = await self._extract_urls(text)
        if urls:
            extracted["has_links"] = True
            extracted["urls"] = urls
            
            # If the content is primarily a URL, extract web content
            if content_type == "link" and len(urls) == 1:
                web_content = await self._extract_web_content(urls[0])
                if web_content:
                    extracted["web_content"] = web_content
        
        # Extract key phrases and concepts
        key_phrases = await self._extract_key_phrases(text)
        if key_phrases:
            extracted["key_phrases"] = key_phrases
        
        # Extract questions
        questions = await self._extract_questions(text)
        if questions:
            extracted["questions"] = questions
        
        # Extract code snippets
        code_snippets = await self._extract_code_snippets(text)
        if code_snippets:
            extracted["code_snippets"] = code_snippets
        
        # Check if content is meaningful
        if len(text.strip()) < 3 or text.strip().lower() in ["test", "hello", "hi", "ok", "yes", "no"]:
            extracted["has_meaningful_content"] = False
        
        # Extract metadata based on content type
        if content_type == "markdown":
            extracted["metadata"] = await self._extract_markdown_metadata(text)
        elif content_type == "code":
            extracted["metadata"] = await self._extract_code_metadata(text)
        elif content_type == "research":
            extracted["metadata"] = await self._extract_research_metadata(text)
        
        return extracted
    
    async def _detect_content_type(self, text: str) -> str:
        """Detect the type of content"""
        text_lower = text.lower().strip()
        
        # Check for URLs
        if re.search(r'https?://', text) and len(text.split()) <= 3:
            return "link"
        
        # Check for markdown
        if re.search(r'#+\s|```|\*\*|\[.*\]\(.*\)', text):
            return "markdown"
        
        # Check for code
        if re.search(r'```|def |class |function |import |from .* import|<\w+>|{\w+}', text):
            return "code"
        
        # Check for research content
        if any(keyword in text_lower for keyword in ["research", "study", "paper", "methodology", "results", "findings"]):
            return "research"
        
        # Check for questions
        if text.strip().endswith('?') or text.lower().startswith(('what', 'how', 'why', 'when', 'where', 'which')):
            return "question"
        
        # Check for personal reflection
        if any(pronoun in text_lower for pronoun in ["i think", "i feel", "i believe", "in my opinion"]):
            return "personal"
        
        # Check for ideas
        if any(phrase in text_lower for phrase in ["idea:", "concept:", "what if", "maybe we could", "possibly"]):
            return "idea"
        
        return "text"
    
    async def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        urls = re.findall(url_pattern, text)
        return urls
    
    async def _extract_web_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content from a web URL"""
        if not self.http_client:
            return None
            
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ""
            
            # Extract main content (heuristic)
            content = ""
            
            # Try to find main content areas
            main_content_selectors = [
                'main', 'article', '.content', '.post-content', 
                '.entry-content', '.article-content', 'div[role="main"]'
            ]
            
            for selector in main_content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text().strip()
                    break
            
            # Fallback to body content
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text().strip()
            
            # Clean up content
            content = re.sub(r'\s+', ' ', content)[:1000]  # Limit to 1000 chars
            
            return {
                "title": title_text,
                "description": description,
                "content": content,
                "url": url,
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error extracting web content from {url}: {e}")
            return None
    
    async def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        # Simple keyword extraction using word frequency and patterns
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out common words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'this', 'that', 'these', 'those',
            'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'are', 'is', 'be', 'being'
        }
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top phrases
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10] if freq > 1]
    
    async def _extract_questions(self, text: str) -> List[str]:
        """Extract questions from text"""
        # Find sentences that end with question marks
        sentences = re.split(r'[.!?]+', text)
        questions = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence.endswith('?'):
                questions.append(sentence + '?')
            elif any(sentence.lower().startswith(word) for word in ['what', 'how', 'why', 'when', 'where', 'which', 'who']):
                questions.append(sentence + '?')
        
        return questions
    
    async def _extract_code_snippets(self, text: str) -> List[Dict[str, Any]]:
        """Extract code snippets from text"""
        code_snippets = []
        
        # Extract code blocks (```)
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', text, re.DOTALL)
        for language, code in code_blocks:
            code_snippets.append({
                "type": "code_block",
                "language": language or "unknown",
                "code": code.strip()
            })
        
        # Extract inline code (`)
        inline_code = re.findall(r'`([^`]+)`', text)
        for code in inline_code:
            if len(code) > 5:  # Only capture meaningful inline code
                code_snippets.append({
                    "type": "inline_code",
                    "code": code.strip()
                })
        
        return code_snippets
    
    async def _extract_markdown_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from markdown content"""
        metadata = {}
        
        # Extract headers
        headers = re.findall(r'^#+\s+(.+)$', text, re.MULTILINE)
        if headers:
            metadata["headers"] = headers
        
        # Extract links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
        if links:
            metadata["links"] = [{"text": text, "url": url} for text, url in links]
        
        # Extract bold/italic text
        bold_text = re.findall(r'\*\*([^*]+)\*\*', text)
        if bold_text:
            metadata["bold_text"] = bold_text
        
        return metadata
    
    async def _extract_code_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from code content"""
        metadata = {}
        
        # Detect programming language
        language_indicators = {
            'python': ['def ', 'import ', 'from ', 'class ', 'if __name__'],
            'javascript': ['function ', 'const ', 'let ', 'var ', '=>'],
            'java': ['public class', 'private ', 'public ', 'void '],
            'c++': ['#include', 'using namespace', 'int main'],
            'html': ['<html>', '<div>', '<script>', '<!DOCTYPE'],
            'css': ['{', '}', 'color:', 'background:', 'margin:']
        }
        
        detected_languages = []
        for lang, indicators in language_indicators.items():
            if any(indicator in text for indicator in indicators):
                detected_languages.append(lang)
        
        if detected_languages:
            metadata["detected_languages"] = detected_languages
        
        # Extract function names
        functions = re.findall(r'(?:def|function)\s+(\w+)', text)
        if functions:
            metadata["functions"] = functions
        
        return metadata
    
    async def _extract_research_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from research content"""
        metadata = {}
        
        # Extract potential citations
        citations = re.findall(r'\(([^)]*\d{4}[^)]*)\)', text)
        if citations:
            metadata["citations"] = citations
        
        # Extract methodology mentions
        methodology_keywords = ['methodology', 'method', 'approach', 'technique', 'analysis']
        found_methods = []
        for keyword in methodology_keywords:
            if keyword in text.lower():
                found_methods.append(keyword)
        
        if found_methods:
            metadata["methodology_mentions"] = found_methods
        
        # Extract numerical data
        numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', text)
        if len(numbers) > 3:  # Only if there are several numbers
            metadata["numerical_data"] = numbers[:10]  # Limit to 10
        
        return metadata
    
    async def close(self):
        """Close the HTTP client"""
        if self.http_client:
            await self.http_client.aclose() 