"""
Custom tools for knowledge management operations using smolagents
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import asyncio
import re
import time
from smolagents import tool

from knowledge.enhanced_knowledge_graph import get_enhanced_knowledge_graph
from knowledge.categorizer import ContentCategorizer
from knowledge.content_processor import ContentProcessor
from knowledge.notes_manager import NotesManager
from models.chat_models import SearchResult


class KnowledgeToolsManager:
    """Manages the knowledge management tools and their shared state"""
    
    def __init__(self):
        self.knowledge_graph = None
        self.categorizer = None
        self.content_processor = None
        self.notes_manager = None
        self.initialized = False
        self.notes_directory = None
        self.knowledge_base_directory = None
    
    def setup_directories(self, notes_dir: str, knowledge_base_dir: str):
        """
        Set up the directories for notes and knowledge base
        
        Args:
            notes_dir: Directory where notes will be stored
            knowledge_base_dir: Directory where knowledge base data will be stored
        """
        self.notes_directory = notes_dir
        self.knowledge_base_directory = knowledge_base_dir
        
        # Create the components with the specified directories
        self.knowledge_graph = get_enhanced_knowledge_graph()
        self.categorizer = ContentCategorizer()
        self.content_processor = ContentProcessor()
        self.notes_manager = NotesManager(notes_directory=notes_dir)
        
        # Update the hash tracker to use the knowledge base directory
        from knowledge.hash_utils import get_hash_tracker
        hash_tracker = get_hash_tracker()
        hash_tracker.cache_file = f"{knowledge_base_dir}/hash_cache.json"
        # Reload cache from new location
        hash_tracker.hash_cache = hash_tracker._load_cache()
        hash_tracker.note_to_node_mapping = hash_tracker._load_mapping()
    
    async def initialize(self):
        """Initialize all components"""
        if self.initialized:
            return
        
        # Initialize with default directories if not set up yet
        if self.knowledge_graph is None:
            self.knowledge_graph = get_enhanced_knowledge_graph()
        if self.categorizer is None:
            self.categorizer = ContentCategorizer()
        if self.content_processor is None:
            self.content_processor = ContentProcessor()
        if self.notes_manager is None:
            self.notes_manager = NotesManager()
        
        print("🚀 Initializing Knowledge Management Tools...")
        
        # Initialize all components
        await self.knowledge_graph.initialize()
        await self.notes_manager.initialize()
        
        # Process existing notes into knowledge graph
        await self._process_existing_notes()
        
        self.initialized = True
        print("✅ Knowledge Management Tools initialized!")
    
    async def _process_existing_notes(self):
        """Process existing notes and add them to the knowledge graph"""
        notes = await self.notes_manager.get_all_notes()
        
        if not notes:
            print("📄 No existing notes found")
            return
        
        print(f"📚 Processing {len(notes)} existing notes...")
        
        for note in notes:
            try:
                # Add note to enhanced knowledge graph using add_note_from_content
                await self.knowledge_graph.add_note_from_content(
                    title=note.title,
                    content=note.content,
                    category=note.category,
                    tags=note.tags,
                    file_path=note.path
                )
            except Exception as e:
                print(f"Error processing note {note.title}: {e}")
        
        print(f"✅ Processed {len(notes)} existing notes into knowledge graph")


# Global instance for shared state
_knowledge_tools_manager = KnowledgeToolsManager()


def _run_async_safely(coro):
    """Run async coroutine safely, handling existing event loops"""
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're in an event loop, we need to use a different approach
        import concurrent.futures
        import threading
        
        # Create a new event loop in a separate thread
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        
        # Run the coroutine in a thread pool
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
            
    except RuntimeError:
        # No event loop running, we can use asyncio.run()
        return asyncio.run(coro)


def _extract_main_content(html: str, url: str) -> Dict[str, str]:
    """
    Extract main content from HTML, avoiding ads and navigation
    Returns a dictionary with title, content, and summary
    """
    try:
        from bs4 import BeautifulSoup
        import urllib.parse
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                           'aside', 'iframe', 'noscript', 'comment']):
            element.decompose()
        
        # Remove elements with common ad/navigation classes
        ad_classes = ['advertisement', 'ad', 'ads', 'sidebar', 'navigation', 
                     'nav', 'menu', 'social', 'share', 'cookie', 'popup']
        for class_name in ad_classes:
            for element in soup.find_all(class_=re.compile(class_name, re.I)):
                element.decompose()
        
        # Extract title
        title = ""
        if soup.title:
            title = soup.title.get_text().strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()
        
        # Extract main content
        content_candidates = []
        
        # Try common content containers first
        for selector in ['article', '[role="main"]', 'main', '.content', '#content',
                        '.post', '.entry', '.article']:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 200:  # Only consider substantial content
                    content_candidates.append(text)
        
        # If no main content found, get all paragraphs
        if not content_candidates:
            paragraphs = soup.find_all('p')
            content_text = ' '.join([p.get_text(separator=' ', strip=True) 
                                   for p in paragraphs if len(p.get_text(strip=True)) > 50])
            if content_text:
                content_candidates.append(content_text)
        
        # Use the longest content candidate
        main_content = max(content_candidates, key=len) if content_candidates else ""
        
        # Clean up the content
        main_content = re.sub(r'\s+', ' ', main_content).strip()
        
        # Create a summary (first 3 sentences or 300 chars, whichever is shorter)
        sentences = re.split(r'[.!?]+', main_content)
        summary_sentences = []
        char_count = 0
        
        for sentence in sentences[:3]:
            sentence = sentence.strip()
            if sentence and char_count + len(sentence) < 300:
                summary_sentences.append(sentence)
                char_count += len(sentence)
            else:
                break
        
        summary = '. '.join(summary_sentences)
        if summary and not summary.endswith('.'):
            summary += '.'
        
        # Limit content length to avoid token bloat (keep ~500 words max)
        if len(main_content) > 3000:
            main_content = main_content[:3000] + "..."
        
        return {
            "title": title or urllib.parse.urlparse(url).netloc,
            "content": main_content,
            "summary": summary or main_content[:300] + "..." if main_content else "",
            "word_count": len(main_content.split()),
            "url": url
        }
        
    except Exception as e:
        print(f"Error extracting content: {e}")
        return {
            "title": f"Content from {url}",
            "content": "",
            "summary": f"Failed to extract content from {url}: {str(e)}",
            "word_count": 0,
            "url": url
        }


def _generate_proper_wiki_links(content: str, target_category: str = None) -> str:
    """
    Generate proper Obsidian wiki-links in content by converting bare links to path-based links.
    This ensures Obsidian can resolve the links correctly.
    
    Args:
        content: The content containing wiki-links to fix
        target_category: The category of the note being created (for context)
        
    Returns:
        Content with properly formatted wiki-links
    """
    import re
    
    if not _knowledge_tools_manager.initialized:
        return content
    
    def replace_wiki_link(match):
        link_content = match.group(1).strip()
        
        # Skip if already has a path (contains '/')
        if '/' in link_content:
            return match.group(0)
        
        # Skip if it's a display link with |
        if '|' in link_content:
            target, display = link_content.split('|', 1)
            target = target.strip()
            display = display.strip()
            
            # Try to resolve the target using notes manager
            proper_link = _knowledge_tools_manager.notes_manager.get_obsidian_wiki_link_for_note(target, target_category)
            if proper_link != f"[[{target}]]":
                # Extract path from proper link
                path_match = re.match(r'\[\[([^\]]+)\]\]', proper_link)
                if path_match:
                    return f"[[{path_match.group(1)}|{display}]]"
            
            return match.group(0)
        
        # Try to resolve bare link using notes manager
        proper_link = _knowledge_tools_manager.notes_manager.get_obsidian_wiki_link_for_note(link_content, target_category)
        return proper_link
    
    # Pattern to match wiki-links
    wiki_link_pattern = r'\[\[([^\]]+)\]\]'
    return re.sub(wiki_link_pattern, replace_wiki_link, content)


@tool
def browse_web_content(url: str, save_to_notes: bool = True, category: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
    """
    Browse a web URL and extract the main content, optionally saving it to knowledge base.
    This tool fetches web content, extracts the main article/content, and provides a summary.
    
    Args:
        url: The URL to browse and extract content from
        save_to_notes: Whether to save the extracted content as a note (default: True)
        category: Category for the note if saving (default: auto-categorized)
        tags: Tags to add to the note if saving (default: auto-generated)
        
    Returns:
        JSON string containing the extracted content, summary, and note information if saved
    """
    async def _browse():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        try:
            import httpx
            from urllib.parse import urlparse, urljoin
            import time
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return json.dumps({
                    "success": False,
                    "error": "Invalid URL format. Please provide a complete URL with http:// or https://",
                    "url": url
                }, indent=2)
            
            print(f"🌐 Browsing URL: {url}")
            
            # Set up headers to mimic a real browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            
            # Fetch the content with timeout
            async with httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    return json.dumps({
                        "success": False,
                        "error": f"URL does not contain HTML content. Content type: {content_type}",
                        "url": url
                    }, indent=2)
                
                html_content = response.text
            
            print("📄 Extracting main content...")
            
            # Extract main content
            extracted = _extract_main_content(html_content, url)
            
            if not extracted["content"]:
                return json.dumps({
                    "success": False,
                    "error": "Could not extract meaningful content from the URL",
                    "url": url,
                    "title": extracted["title"]
                }, indent=2)
            
            result = {
                "success": True,
                "url": url,
                "title": extracted["title"],
                "summary": extracted["summary"],
                "content_preview": extracted["content"][:500] + "..." if len(extracted["content"]) > 500 else extracted["content"],
                "word_count": extracted["word_count"],
                "extracted_at": datetime.now().isoformat()
            }
            
            # Save to notes if requested
            if save_to_notes:
                print("💾 Saving content to knowledge base...")
                
                # Auto-categorize if no category provided
                if not category:
                    categories = await _knowledge_tools_manager.categorizer.categorize(extracted["summary"])
                    category = categories[0] if categories else "Web Content"
                
                # Auto-generate tags if none provided
                if not tags:
                    tags = ["web-content", "article"]
                    # Add domain as tag
                    domain = urlparse(url).netloc.replace('www.', '')
                    if domain:
                        tags.append(domain)
                
                # Create the note content with source attribution
                note_content = f"""# {extracted['title']}

**Source:** {url}
**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Summary:** {extracted['summary']}

---

{extracted['content']}

---
*Content extracted from web source and may be truncated. Visit the original URL for complete content.*"""
                
                # Fix wiki-links in content for Obsidian compatibility
                note_content = _generate_proper_wiki_links(note_content, category)
                
                # Create the note
                note = await _knowledge_tools_manager.notes_manager.create_note(
                    title=f"Web: {extracted['title'][:50]}..." if len(extracted['title']) > 50 else f"Web: {extracted['title']}",
                    content=note_content,
                    category=category,
                    tags=tags
                )
                
                # Add to knowledge graph
                node_id = await _knowledge_tools_manager.knowledge_graph.add_note_from_content(
                    title=note.title,
                    content=note_content,
                    category=category,
                    tags=tags,
                    file_path=note.path
                )
                
                result.update({
                    "note_created": True,
                    "note": {
                        "title": note.title,
                        "category": category,
                        "tags": tags,
                        "path": note.path,
                        "node_id": node_id,
                        "obsidian_wiki_link": note.get_obsidian_wiki_link(_knowledge_tools_manager.notes_manager.notes_directory)
                    }
                })
                
                print(f"✅ Created note: {note.title}")
            else:
                result["note_created"] = False
            
            return json.dumps(result, indent=2)
            
        except httpx.TimeoutException:
            return json.dumps({
                "success": False,
                "error": "Request timed out. The website took too long to respond.",
                "url": url
            }, indent=2)
        except httpx.HTTPStatusError as e:
            return json.dumps({
                "success": False,
                "error": f"HTTP error {e.response.status_code}: {e.response.reason_phrase}",
                "url": url
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error browsing URL: {str(e)}",
                "url": url
            }, indent=2)
    
    return _run_async_safely(_browse())


@tool
def summarize_web_links(text_with_links: str, auto_save: bool = True) -> str:
    """
    Extract URLs from text and summarize their content for knowledge augmentation.
    Useful for processing text that contains multiple links that should be researched.
    
    Args:
        text_with_links: Text containing one or more URLs to be processed
        auto_save: Whether to automatically save summaries to knowledge base (default: True)
        
    Returns:
        JSON string containing summaries of all found links and their integration status
    """
    async def _summarize_links():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Extract URLs from text
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text_with_links)
        
        if not urls:
            return json.dumps({
                "success": False,
                "error": "No valid URLs found in the provided text",
                "text_preview": text_with_links[:200] + "..." if len(text_with_links) > 200 else text_with_links
            }, indent=2)
        
        print(f"🔗 Found {len(urls)} URLs to process")
        
        results = {
            "success": True,
            "total_urls": len(urls),
            "processed_urls": [],
            "failed_urls": [],
            "notes_created": 0,
            "processing_time": time.time()
        }
        
        for i, url in enumerate(urls[:5]):  # Limit to 5 URLs to avoid overwhelming
            print(f"🌐 Processing URL {i+1}/{min(len(urls), 5)}: {url}")
            
            try:
                # Use the browse_web_content function
                browse_result = json.loads(await _browse_single_url(url, auto_save))
                
                if browse_result["success"]:
                    results["processed_urls"].append({
                        "url": url,
                        "title": browse_result["title"],
                        "summary": browse_result["summary"],
                        "word_count": browse_result["word_count"],
                        "note_created": browse_result.get("note_created", False)
                    })
                    
                    if browse_result.get("note_created"):
                        results["notes_created"] += 1
                else:
                    results["failed_urls"].append({
                        "url": url,
                        "error": browse_result["error"]
                    })
                
                # Small delay between requests to be respectful
                await asyncio.sleep(1)
                
            except Exception as e:
                results["failed_urls"].append({
                    "url": url,
                    "error": str(e)
                })
        
        if len(urls) > 5:
            results["note"] = f"Only processed first 5 URLs out of {len(urls)} found to avoid overwhelming the system"
        
        results["processing_time"] = round(time.time() - results["processing_time"], 2)
        
        return json.dumps(results, indent=2)
    
    async def _browse_single_url(url, save_to_notes):
        """Helper function to browse a single URL"""
        return browse_web_content(url, save_to_notes=save_to_notes)
    
    return _run_async_safely(_summarize_links())


@tool
def process_and_categorize_content(content: str, title: Optional[str] = None) -> str:
    """
    Process content and categorize it for knowledge management with caching.
    
    Args:
        content: The content to process and categorize
        title: Optional title for the content
        
    Returns:
        JSON string containing processed content with category and metadata
    """
    async def _process():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Check if we've already processed this content recently
        from knowledge.hash_utils import calculate_content_hash, get_hash_tracker
        
        content_hash = calculate_content_hash(content)
        cache_key = f"processed_content:{content_hash}"
        hash_tracker = get_hash_tracker()
        
        # Check if we have cached results
        if not hash_tracker.has_content_changed(cache_key, content):
            cache_entry = hash_tracker.hash_cache.get(cache_key, {})
            cached_result = cache_entry.get('metadata', {}).get('result')
            if cached_result:
                print(f"⚡ Using cached content processing for hash {content_hash[:8]}...")
                return cached_result
        
        # Process the content
        processed_content = await _knowledge_tools_manager.content_processor.extract_content(content)
        
        # Categorize the content
        categories = await _knowledge_tools_manager.categorizer.categorize(
            processed_content.get("text", content)
        )
        best_category = categories[0] if categories else "Quick Notes"
        
        # Fix wiki-links in content for Obsidian compatibility
        fixed_content = _generate_proper_wiki_links(content, best_category)
        
        result = {
            "processed_content": processed_content,
            "category": best_category,
            "all_categories": categories,
            "title": title or processed_content.get("title", ""),
            "content_hash": content_hash,
            "fixed_content": fixed_content
        }
        
        result_json = json.dumps(result, indent=2)
        
        # Cache the result
        hash_tracker.update_hash(
            cache_key,
            content_hash,
            {
                "result": result_json,
                "processed_at": datetime.now().isoformat(),
                "category": best_category
            }
        )
        
        return result_json
    
    return _run_async_safely(_process())


@tool
def create_knowledge_note(content: str, category: str, title: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
    """
    Create a new knowledge note and add it to the knowledge graph with hash tracking.
    
    Args:
        content: The content of the note
        category: The category for the note
        title: Optional title for the note
        tags: Optional list of tags for the note
        
    Returns:
        JSON string containing the created note information
    """
    async def _create():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Fix wiki-links in content for Obsidian compatibility
        fixed_content = _generate_proper_wiki_links(content, category)
        
        # Create the note
        note = await _knowledge_tools_manager.notes_manager.create_note(
            title=title or f"Note from {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            content=fixed_content,
            category=category,
            tags=tags or []
        )
        
        # Add to enhanced knowledge graph
        node_id = await _knowledge_tools_manager.knowledge_graph.add_note_from_content(
            title=note.title,
            content=fixed_content,
            category=category,
            tags=note.tags,
            file_path=note.path
        )
        
        return json.dumps({
            "success": True,
            "note": note.to_dict(),
            "knowledge_node_id": node_id,
            "message": f"Created note: {note.title}",
            "obsidian_wiki_link": note.get_obsidian_wiki_link(_knowledge_tools_manager.notes_manager.notes_directory),
            "cached": False
        }, indent=2)
    
    return _run_async_safely(_create())


@tool
def update_knowledge_note(note_path: str, additional_content: str) -> str:
    """
    Update an existing knowledge note with additional content and sync knowledge graph.
    
    Args:
        note_path: Path to the note to update
        additional_content: Additional content to add to the note
        
    Returns:
        JSON string containing the updated note information
    """
    async def _update():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Check if this content would actually change the note
        from knowledge.hash_utils import calculate_content_hash, get_hash_tracker
        
        hash_tracker = get_hash_tracker()
        
        # Get current note if it exists
        try:
            current_note = _knowledge_tools_manager.notes_manager.notes_index.get(note_path)
            if current_note:
                # Check if we're trying to add content that would result in the same hash
                test_content = current_note.content + f"\n\n## Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{additional_content}"
                if not current_note.has_content_changed(test_content):
                    return json.dumps({
                        "success": True,
                        "note": current_note.to_dict(),
                        "message": f"No changes needed for note: {current_note.title}",
                        "cached": True
                    }, indent=2)
        except Exception as e:
            print(f"Warning: Could not check for content changes: {e}")
        
        # Fix wiki-links in additional content for Obsidian compatibility
        # Get category from existing note if available
        target_category = None
        try:
            current_note = _knowledge_tools_manager.notes_manager.notes_index.get(note_path)
            if current_note:
                target_category = current_note.category
        except:
            pass
        
        fixed_additional_content = _generate_proper_wiki_links(additional_content, target_category)
        
        # Update the note
        note = await _knowledge_tools_manager.notes_manager.update_note(
            note_path, fixed_additional_content
        )
        
        # Update enhanced knowledge graph
        node_id = await _knowledge_tools_manager.knowledge_graph.add_note_from_content(
            title=note.title,
            content=note.content,
            category=note.category,
            tags=note.tags,
            file_path=note.path
        )
        
        return json.dumps({
            "success": True,
            "note": note.to_dict(),
            "knowledge_node_id": node_id,
            "message": f"Updated note: {note.title}",
            "obsidian_wiki_link": note.get_obsidian_wiki_link(_knowledge_tools_manager.notes_manager.notes_directory),
            "cached": False
        }, indent=2)
    
    return _run_async_safely(_update())


@tool
def search_knowledge(query: str, limit: int = 10) -> str:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        JSON string containing search results
    """
    async def _search():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Search enhanced knowledge graph
        results = await _knowledge_tools_manager.knowledge_graph.search_semantic(query, limit)
        
        # Convert SearchResult objects to dictionaries
        results_dict = []
        for result in results:
            if hasattr(result, 'model_dump'):
                results_dict.append(result.model_dump())
            elif hasattr(result, 'to_dict'):
                results_dict.append(result.to_dict())
            else:
                # Handle if it's already a dict or create a basic dict
                results_dict.append({
                    "content": getattr(result, 'content', str(result)),
                    "category": getattr(result, 'category', 'Unknown'),
                    "similarity": getattr(result, 'similarity', 1.0),
                    "node_id": getattr(result, 'node_id', ''),
                    "metadata": getattr(result, 'metadata', {})
                })
        
        return json.dumps({
            "query": query,
            "results": results_dict,
            "count": len(results_dict)
        }, indent=2)
    
    return _run_async_safely(_search())


@tool
def search_content_in_files(query: str, case_sensitive: bool = False, limit: int = 10) -> str:
    """
    Search for specific content within note files using grep-like functionality.
    Use this when you need to find exact text or patterns within the actual file contents.
    
    Args:
        query: The text or regex pattern to search for in file contents
        case_sensitive: Whether the search should be case sensitive (default: False)
        limit: Maximum number of files to return (default: 10)
        
    Returns:
        JSON string containing search results with matches and context
    """
    async def _search_content():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Search file contents directly
        results = await _knowledge_tools_manager.knowledge_graph.search_content_in_files(query, case_sensitive, limit)
        
        return json.dumps({
            "query": query,
            "case_sensitive": case_sensitive,
            "results": results,
            "total_files_found": len(results),
            "total_matches": sum(r.get('total_matches', 0) for r in results)
        }, indent=2)
    
    return _run_async_safely(_search_content())


@tool
def find_related_notes(content: str, limit: int = 5) -> str:
    """
    Find notes related to the given content.
    
    Args:
        content: Content to find related notes for
        limit: Maximum number of related notes to return
        
    Returns:
        JSON string containing related notes
    """
    async def _find():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Find related notes
        related_notes = await _knowledge_tools_manager.notes_manager.find_related_notes(
            content, limit
        )
        
        return json.dumps({
            "query_content": content[:100] + "..." if len(content) > 100 else content,
            "related_notes": [note.to_dict() for note in related_notes],
            "count": len(related_notes)
        }, indent=2)
    
    return _run_async_safely(_find())


@tool
def get_knowledge_graph_data() -> str:
    """
    Get the current knowledge graph data structure.
    
    Returns:
        JSON string containing the knowledge graph data
    """
    async def _get_graph():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        graph_data = await _knowledge_tools_manager.knowledge_graph.get_graph_data()
        
        return json.dumps({
            "knowledge_graph": graph_data,
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    
    return _run_async_safely(_get_graph())


# @tool - REMOVED: get_all_notes tool disabled for performance reasons
# def get_all_notes() -> str:
#     """
#     Get all notes in the knowledge base.
#     
#     Returns:
#         JSON string containing all notes
#     """
#     async def _get_all():
#         if not _knowledge_tools_manager.initialized:
#             await _knowledge_tools_manager.initialize()
#         
#         notes = await _knowledge_tools_manager.notes_manager.get_all_notes()
#         
#         return json.dumps({
#             "notes": [note.to_dict() for note in notes],
#             "count": len(notes),
#             "timestamp": datetime.now().isoformat()
#         }, indent=2)
#     
#     return _run_async_safely(_get_all())


@tool
def search_notes(query: str, limit: int = 10) -> str:
    """
    Search for notes matching the query.
    
    Args:
        query: The search query
        limit: Maximum number of notes to return
        
    Returns:
        JSON string containing matching notes
    """
    async def _search_notes():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        notes = await _knowledge_tools_manager.notes_manager.search_notes(query, limit)
        
        return json.dumps({
            "query": query,
            "notes": [note.to_dict() for note in notes],
            "count": len(notes)
        }, indent=2)
    
    return _run_async_safely(_search_notes())


@tool
def unified_search(
    query: str, 
    limit: int = 20,
    include_semantic: bool = True,
    include_grep: bool = True,
    include_title: bool = True,
    include_tag: bool = True,
    semantic_threshold: float = 0.3
) -> str:
    """
    Unified search function that combines semantic search, grep search, title search, and tag search.
    Returns results with relevant snippets and context.
    
    Args:
        query: Search query
        limit: Maximum number of results to return (default: 20)
        include_semantic: Include semantic search results (default: True)
        include_grep: Include grep/content search results (default: True)
        include_title: Include title matching results (default: True)
        include_tag: Include tag matching results (default: True)
        semantic_threshold: Minimum similarity score for semantic results (default: 0.3)
        
    Returns:
        JSON string containing unified search results with snippets and context
    """
    async def _unified_search():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Use the enhanced knowledge graph's unified search
        results = await _knowledge_tools_manager.knowledge_graph.unified_search(
            query=query,
            limit=limit,
            include_semantic=include_semantic,
            include_grep=include_grep,
            include_title=include_title,
            include_tag=include_tag,
            semantic_threshold=semantic_threshold
        )
        
        # Convert results to JSON-serializable format
        search_results = []
        for result in results:
            search_results.append({
                "content": result.content,
                "title": result.title,
                "category": result.category,
                "source_type": result.source_type,
                "relevance_score": result.relevance_score,
                "node_id": result.node_id,
                "file_path": result.file_path,
                "line_number": result.line_number,
                "context": result.context,
                "snippet": result.snippet,
                "chunk_index": result.chunk_index,
                "total_chunks": result.total_chunks,
                "metadata": result.metadata
            })
        
        return json.dumps({
            "query": query,
            "total_results": len(search_results),
            "results": search_results,
            "search_types_used": {
                "semantic": include_semantic,
                "grep": include_grep,
                "title": include_title,
                "tag": include_tag
            },
            "timestamp": datetime.now().isoformat()
        }, indent=2)
    
    return _run_async_safely(_unified_search())


@tool
def decide_note_action(content: str, category: str) -> str:
    """
    Use an LLM to intelligently decide whether to create a new note or update an existing one.
    Searches for relevant notes using unified search and provides context to the LLM for decision making.
    
    Args:
        content: The content to process
        category: The category for the content
        
    Returns:
        JSON string containing the LLM's decision and reasoning
    """
    async def _decide():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        # Use unified search to find relevant notes
        search_results = await _knowledge_tools_manager.knowledge_graph.unified_search(
            query=content,
            limit=5,
            include_semantic=True,
            include_grep=True,
            include_title=True,
            include_tag=False,  # Don't need tag search for this
            semantic_threshold=0.25  # Lower threshold for more results
        )
        
        # Filter and prepare relevant notes for LLM analysis
        relevant_notes = []
        for result in search_results:
            # Prioritize same category or high relevance
            if result.category == category or result.relevance_score > 0.3:
                relevant_notes.append({
                    "title": result.title,
                    "category": result.category,
                    "file_path": result.file_path,
                    "relevance_score": result.relevance_score,
                    "source_type": result.source_type,
                    "snippet": result.snippet,
                    "context": result.context if result.context else result.content[:300] + "..."
                })
        
        # Sort by relevance and keep top 3
        relevant_notes.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_notes = relevant_notes[:3]
        
        # Create LLM prompt
        llm_prompt = _create_decision_prompt(content, category, top_notes)
        
        # Get LLM decision
        try:
            decision = await _get_llm_decision(llm_prompt)
        except Exception as e:
            print(f"Error getting LLM decision: {e}")
            # Fallback to a simple heuristic
            decision = _fallback_decision(content, category, top_notes)
        
        return json.dumps(decision, indent=2, ensure_ascii=False)
    
    def _create_decision_prompt(content: str, category: str, relevant_notes: list) -> str:
        """Create a comprehensive prompt for the LLM to make the decision"""
        prompt = f"""You are an intelligent knowledge management assistant. Your task is to decide whether to CREATE a new note or UPDATE an existing note based on the user's content and existing notes.

USER'S NEW CONTENT:
Category: {category}
Content: {content}
Word count: {len(content.split())} words

EXISTING RELEVANT NOTES:
"""
        
        if relevant_notes:
            for i, note in enumerate(relevant_notes, 1):
                prompt += f"""
{i}. Title: {note['title']}
   Category: {note['category']}
   Relevance Score: {note['relevance_score']:.2f}
   Search Method: {note['source_type']}
   File Path: {note['file_path']}
   Snippet: {note['snippet']}
   Context: {note['context'][:200]}...
"""
        else:
            prompt += "No relevant existing notes found.\n"
        
        prompt += """
DECISION CRITERIA:
- CREATE a new note if:
  * Content is substantially different from existing notes
  * Content is a complete, standalone piece of information
  * User's content doesn't logically fit into any existing note
  * Existing notes are only tangentially related
  * Content represents a new concept or topic

- UPDATE an existing note if:
  * Content clearly extends, clarifies, or adds to an existing note
  * Content fixes errors or provides corrections to existing information
  * Content is a continuation of thoughts in an existing note
  * Content provides examples or details for existing concepts
  * Content is brief and would benefit from being part of a larger note

INSTRUCTIONS:
Analyze the content and existing notes carefully. Consider the semantic meaning, not just keyword matches. Pay attention to the context and how the content would fit into the knowledge structure.

Respond with ONLY a valid JSON object in this exact format:
{
    "action": "create" | "update",
    "confidence": 0.0-1.0,
    "reasoning": ["reason1", "reason2", "reason3"],
    "recommended_note": {
        "title": "note title",
        "file_path": "path/to/file.md",
        "category": "category name"
    } | null,
    "alternatives": [
        {
            "title": "alternative note title", 
            "reason": "why this could be an alternative"
        }
    ]
}

Your decision:"""
        
        return prompt
    
    async def _get_llm_decision(prompt: str) -> dict:
        """Get decision from LLM using the same model as the knowledge agent"""
        import litellm
        import os
        import json
        import re
        
        def _get_openrouter_config():
            """Get OpenRouter configuration"""
            api_key = os.getenv("OPENROUTER_API_KEY")
            if api_key:
                model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
                return {
                    "model": f"openrouter/{model}",
                    "api_key": api_key
                }
            return None
        
        def _get_anthropic_config():
            """Get Anthropic configuration"""
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
                return {
                    "model": model,
                    "api_key": api_key
                }
            return None
        
        def _get_openai_config():
            """Get OpenAI configuration"""
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                return {
                    "model": model,
                    "api_key": api_key
                }
            return None
        
        # Try to use the same model configuration as the knowledge agent
        model_configs = [
            ("openrouter", _get_openrouter_config),
            ("anthropic", _get_anthropic_config),
            ("openai", _get_openai_config)
        ]
        
        for model_type, config_func in model_configs:
            try:
                model_config = config_func()
                if model_config:
                    response = await litellm.acompletion(
                        model=model_config["model"],
                        messages=[{"role": "user", "content": prompt}],
                        api_key=model_config["api_key"],
                        max_tokens=500,
                        temperature=0.1  # Low temperature for consistent decisions
                    )
                    
                    response_text = response.choices[0].message.content.strip()
                    
                    # Try to parse the JSON response
                    try:
                        # Look for JSON in the response
                        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                        else:
                            # If no JSON found, try to parse the whole response
                            return json.loads(response_text)
                    except json.JSONDecodeError:
                        print(f"Failed to parse LLM response as JSON: {response_text}")
                        continue
                        
            except Exception as e:
                print(f"Error with {model_type} model: {e}")
                continue
        
        # If all models fail, raise an error to trigger fallback
        raise Exception("All LLM models failed")
    
    def _fallback_decision(content: str, category: str, relevant_notes: list) -> dict:
        """Fallback decision making if LLM fails"""
        content_words = len(content.split())
        
        # Simple fallback logic
        if relevant_notes and relevant_notes[0]["relevance_score"] > 0.7:
            return {
                "action": "update",
                "confidence": 0.7,
                "reasoning": [
                    f"High relevance score ({relevant_notes[0]['relevance_score']:.2f}) with existing note",
                    "LLM unavailable - using fallback logic"
                ],
                "recommended_note": {
                    "title": relevant_notes[0]["title"],
                    "file_path": relevant_notes[0]["file_path"],
                    "category": relevant_notes[0]["category"]
                },
                "alternatives": []
            }
        else:
            return {
                "action": "create",
                "confidence": 0.6,
                "reasoning": [
                    "No highly relevant existing notes found" if not relevant_notes else f"Low relevance score ({relevant_notes[0]['relevance_score']:.2f})",
                    f"Content length ({content_words} words) suggests standalone note",
                    "LLM unavailable - using fallback logic"
                ],
                "recommended_note": None,
                "alternatives": []
            }
    
    return _run_async_safely(_decide())


@tool
def get_cache_stats() -> str:
    """
    Get statistics about the hash cache and note mappings.
    
    Returns:
        JSON string containing cache statistics and performance metrics
    """
    async def _get_stats():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        from knowledge.hash_utils import get_hash_tracker
        
        hash_tracker = get_hash_tracker()
        cache_stats = hash_tracker.get_cache_stats()
        
        # Get additional statistics
        notes_count = len(_knowledge_tools_manager.notes_manager.notes_index)
        
        # Calculate cache hit rate if possible
        total_requests = cache_stats.get('total_requests', 0)
        cache_hits = cache_stats.get('cache_hits', 0)
        hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "cache_statistics": cache_stats,
            "notes_count": notes_count,
            "cache_hit_rate_percent": round(hit_rate, 2),
            "memory_efficiency": {
                "cached_items_vs_notes_ratio": round(cache_stats['total_cached_items'] / max(notes_count, 1), 2),
                "mapping_coverage_percent": round(cache_stats['total_mapped_notes'] / max(notes_count, 1) * 100, 2)
            },
            "recommendations": []
        }
        
        # Add recommendations based on stats
        if cache_stats['total_mapped_notes'] < notes_count * 0.8:
            stats["recommendations"].append("Consider rebuilding cache - some notes may not be mapped to knowledge nodes")
        
        if cache_stats['total_cached_items'] > notes_count * 2:
            stats["recommendations"].append("Cache cleanup may be beneficial - many stale entries detected")
        
        return json.dumps(stats, indent=2)
    
    return _run_async_safely(_get_stats())


@tool
def clear_cache(confirm: str = "no") -> str:
    """
    Clear the hash cache and note mappings (use with caution).
    
    Args:
        confirm: Must be "yes" to actually clear the cache
        
    Returns:
        JSON string containing the result of the cache clearing operation
    """
    if confirm.lower() != "yes":
        return json.dumps({
            "success": False,
            "message": "Cache not cleared. Use confirm='yes' to actually clear the cache.",
            "warning": "This will remove all cached content hashes and note mappings, requiring full reprocessing on next startup."
        }, indent=2)
    
    async def _clear():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        from knowledge.hash_utils import get_hash_tracker
        
        hash_tracker = get_hash_tracker()
        old_stats = hash_tracker.get_cache_stats()
        
        # Clear the cache
        hash_tracker.clear_cache()
        
        return json.dumps({
            "success": True,
            "message": "Cache cleared successfully",
            "cleared_items": old_stats['total_cached_items'],
            "cleared_mappings": old_stats['total_mapped_notes'],
            "warning": "All cached data has been removed. Next startup will require full reprocessing."
        }, indent=2)
    
    return _run_async_safely(_clear())


@tool
def rebuild_cache() -> str:
    """
    Rebuild the hash cache by reprocessing all notes and content.
    
    Returns:
        JSON string containing the result of the cache rebuilding operation
    """
    async def _rebuild():
        if not _knowledge_tools_manager.initialized:
            await _knowledge_tools_manager.initialize()
        
        from knowledge.hash_utils import get_hash_tracker
        
        hash_tracker = get_hash_tracker()
        
        print("🔄 Starting cache rebuild...")
        
        # Clear existing cache
        old_stats = hash_tracker.get_cache_stats()
        hash_tracker.clear_cache()
        
        # Reinitialize notes manager to rebuild cache
        notes_manager = _knowledge_tools_manager.notes_manager
        notes_manager.notes_index.clear()
        await notes_manager._scan_existing_notes()
        
        # Get new stats
        new_stats = hash_tracker.get_cache_stats()
        
        return json.dumps({
            "success": True,
            "message": "Cache rebuilt successfully",
            "before": {
                "cached_items": old_stats['total_cached_items'],
                "mapped_notes": old_stats['total_mapped_notes']
            },
            "after": {
                "cached_items": new_stats['total_cached_items'],
                "mapped_notes": new_stats['total_mapped_notes']
            },
            "notes_processed": len(notes_manager.notes_index)
        }, indent=2)
    
    return _run_async_safely(_rebuild())


# List of all available tools for easy import
KNOWLEDGE_TOOLS = [
    process_and_categorize_content,
    create_knowledge_note,
    update_knowledge_note,
    search_knowledge,
    search_content_in_files,
    find_related_notes,
    get_knowledge_graph_data,
    # get_all_notes,  # REMOVED: Disabled for performance reasons - use search_notes instead
    search_notes,
    unified_search,
    decide_note_action,
    get_cache_stats,
    clear_cache,
    rebuild_cache,
    browse_web_content,
    summarize_web_links
] 