"""
Knowledge Agent powered by smolagents for intelligent knowledge management
Enhanced with PKM features: wiki-links, typed relationships, and compiled graph indexing
"""
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator, Set
import os
from datetime import datetime
import json
from pathlib import Path
import threading
import time

from smolagents import ToolCallingAgent, CodeAgent, InferenceClientModel, LiteLLMModel
from models.chat_models import ChatMessage, ChatResponse, KnowledgeUpdate, SearchResult
from agent.knowledge_tools import KNOWLEDGE_TOOLS, _knowledge_tools_manager
from agent.action_reporter import ActionReporter
from knowledge.enhanced_knowledge_graph import get_enhanced_knowledge_graph
from knowledge.file_watcher import get_knowledge_graph_watcher, start_file_watcher
import litellm

# Enable LiteLLM debugging if DEBUG env var is set
if os.getenv("DEBUG") == "true":
    litellm._turn_on_debug()



class KnowledgeAgent:
    """
    Simple knowledge management agent focused on organizing user input into notes
    Takes user input and places it in appropriate note locations without adding external knowledge
    """
    
    def __init__(self, model_name: str = "meta-llama/Llama-3.3-70B-Instruct", dir: str = None):
        """
        Initialize the simple knowledge agent
        
        Args:
            model_name: The LLM model to use for the agents
            dir: Directory where notes will be stored (creates if not exists)
                 Knowledge base data will be stored in a .knowledge_base subdirectory
        """
        self.model_name = model_name
        self.knowledge_worker = None
        self.manager_agent = None
        self.initialized = False
        self.action_reporter = ActionReporter()
        
        # Enhanced knowledge graph
        self.enhanced_graph = get_enhanced_knowledge_graph()
        self.file_watcher = get_knowledge_graph_watcher()
        
        # Set up directory structure
        self.setup_directories(dir)
        
        self._setup_model()
        
    def setup_directories(self, dir: str = None):
        """Setup directory structure for notes and knowledge base"""
        if dir is None:
            dir = os.getcwd()
        
        # Ensure absolute path
        self.notes_dir = os.path.abspath(dir)
        self.knowledge_base_dir = os.path.join(self.notes_dir, ".knowledge_base")
        
        # Create directories if they don't exist
        os.makedirs(self.notes_dir, exist_ok=True)
        os.makedirs(self.knowledge_base_dir, exist_ok=True)
        
        # Create category structure
        categories = [
            "quick-notes",
            "ideas", 
            "projects",
            "learning",
            "research",
            "personal",
            "reading-list"
        ]
        
        for category in categories:
            category_dir = os.path.join(self.notes_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            
            # Create README if it doesn't exist
            readme_path = os.path.join(category_dir, "README.md")
            if not os.path.exists(readme_path):
                with open(readme_path, 'w') as f:
                    f.write(f"# {category.replace('-', ' ').title()}\n\n")
                    f.write(f"This folder contains notes related to {category.replace('-', ' ').lower()}.\n")
        
        # Set environment variables for the enhanced graph
        os.environ["KNOWLEDGE_BASE_PATH"] = self.knowledge_base_dir
        os.environ["NOTES_DIRECTORY"] = self.notes_dir
        
        print(f"📁 Directory structure setup:")
        print(f"   Notes directory: {self.notes_dir}")
        print(f"   Knowledge base: {self.knowledge_base_dir}")
        
    def _setup_model(self):
        """Setup the LLM model with priority order"""
        # Priority order for model selection
        model_configs = [
            ("openrouter", self._setup_openrouter_model),
            ("anthropic", self._setup_anthropic_model),
            ("huggingface", self._setup_huggingface_model),
            ("openai", self._setup_openai_model),
            ("free_huggingface", self._setup_free_huggingface_model)
        ]
        
        self.model = None
        for model_type, setup_func in model_configs:
            try:
                self.model = setup_func()
                if self.model:
                    print(f"✅ Using {model_type} model: {self.model_name}")
                    break
            except Exception as e:
                print(f"⚠️  {model_type} model setup failed: {e}")
                continue
        
        if not self.model:
            raise ValueError("No suitable model configuration found. Please set up API keys.")
    
    def _setup_openrouter_model(self):
        """Setup OpenRouter model (highest priority)"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return None
        
        # Get the model name from environment or use default
        model_name = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        
        # Set up OpenRouter-specific environment variables
        os.environ["OPENROUTER_API_KEY"] = api_key
        
        # Optional: Set site URL and app name for OpenRouter rankings
        site_url = os.getenv("OR_SITE_URL", "")
        app_name = os.getenv("OR_APP_NAME", "Knowledge-Management-System")
        
        if site_url:
            os.environ["OR_SITE_URL"] = site_url
        if app_name:
            os.environ["OR_APP_NAME"] = app_name
        
        # For LiteLLM, OpenRouter models must be prefixed with "openrouter/"
        litellm_model_name = f"openrouter/{model_name}"
        
        try:
            # Create the LiteLLM model with proper OpenRouter configuration
            model = LiteLLMModel(
                model_id=litellm_model_name,
                api_key=api_key
            )
            
            print(f"🔗 OpenRouter model configured: {litellm_model_name}")
            return model
            
        except Exception as e:
            print(f"❌ Failed to setup OpenRouter model: {e}")
            return None
    
    def _setup_anthropic_model(self):
        """Setup Anthropic Claude model"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
            
        model_name = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        
        return LiteLLMModel(
            model_id=model_name,
            api_key=api_key
        )
    
    def _setup_huggingface_model(self):
        """Setup HuggingFace model with token"""
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            return None
            
        return InferenceClientModel(
            model_id=self.model_name,
            token=hf_token
        )
    
    def _setup_openai_model(self):
        """Setup OpenAI model"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
            
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        return LiteLLMModel(
            model_id=model_name,
            api_key=api_key
        )
    
    def _setup_free_huggingface_model(self):
        """Setup free HuggingFace model (fallback)"""
        return InferenceClientModel(
            model_id=self.model_name
        )
    
    async def initialize(self):
        """Initialize the enhanced hierarchical agent system"""
        if self.initialized:
            return
        
        print("🚀 Initializing Simple Knowledge Agent System...")
        
        # Initialize knowledge graph
        await self.enhanced_graph.initialize()
        
        # Start file watcher for incremental updates
        await start_file_watcher()
        
        # Initialize knowledge tools
        await _knowledge_tools_manager.initialize()
        
        # Create specialized Knowledge Worker Agent (ToolCallingAgent)
        self.knowledge_worker = ToolCallingAgent(
            model=self.model,
            tools=KNOWLEDGE_TOOLS,
            max_steps=8,
            verbosity_level=1,
            planning_interval=2,
            name="knowledge_worker",
            description="""A focused knowledge management worker for simple note organization with web browsing capabilities:
- Process user input and find appropriate note locations
- Create minimal new notes or update existing ones
- Maintain wiki-links [[note name]] and basic relationships
- Search existing notes to avoid duplication
- Place information in multiple relevant locations when appropriate
- Keep knowledge graph updated with new connections
- Browse web URLs to extract and summarize content from links
- Augment information with relevant web content when URLs are provided
- Focus on user input - do not add external knowledge unless explicitly requested via URLs

IMPORTANT: Only work with the user's input. Do not expand, research, or add external knowledge unless the user provides URLs to browse. Simply organize what the user provides.""",
            provide_run_summary=True,
        )
        
        # Create strategic Knowledge Manager Agent (CodeAgent)
        self.manager_agent = CodeAgent(
            model=self.model,
            tools=[],
            max_steps=10,
            verbosity_level=1,
            additional_authorized_imports=["json", "asyncio", "datetime", "hashlib", "typing", "collections"],
            planning_interval=3,
            name="knowledge_manager",
            description="Simple knowledge management coordinator focused on note placement and organization"
        )
        
        # Add managed agents
        self.manager_agent.managed_agents = [self.knowledge_worker]
        
        self.initialized = True
        print("✅ Simple Knowledge Agent System initialized!")
        print(f"🤖 Manager Agent: {self.manager_agent.name}")
        print(f"🔧 Knowledge Worker: {self.knowledge_worker.name}")
        print(f"📊 Available tools: {len(KNOWLEDGE_TOOLS)}")

    async def process_message(self, message: str, conversation_history: List[ChatMessage] = None) -> ChatResponse:
        """
        Process a user message using the simple note organization system
        
        Args:
            message: The user input to organize into notes
            conversation_history: Optional conversation history
            
        Returns:
            ChatResponse with the agent's response and actions taken
        """
        if not self.initialized:
            await self.initialize()
        
        # Create comprehensive prompt for the manager agent
        prompt = await self._create_manager_prompt(message, conversation_history)
        
        try:
            # Use Manager Agent to coordinate the note organization
            print("🧠 Simple Note Manager analyzing input...")
            
            # Handle managed agents properly - use ask_managed_agent method if available
            if hasattr(self.manager_agent, 'ask_managed_agent'):
                # Use the smolagents managed agent communication method
                worker_prompt = f"""
Process this user input and organize it into appropriate notes:
{message}

Follow these steps:
1. Search existing notes to find relevant locations
2. Decide whether to create new notes or update existing ones
3. Place the information in appropriate location(s)
4. Create basic wiki-links [[note name]] for connections
5. Keep content minimal and focused on user input only

IMPORTANT: Do not add external knowledge or research. Only organize what the user provided.
"""
                result = self.manager_agent.ask_managed_agent(
                    agent=self.knowledge_worker,
                    request=worker_prompt,
                    timeout=30
                )
            else:
                # Fallback to direct worker agent usage
                print("🔄 Using simple note worker directly...")
                result = self.knowledge_worker.run(prompt)
            
            # Parse the agent's response and actions
            response = self._parse_agent_response(result, message)
            
            return response
            
        except Exception as e:
            print(f"Error processing message: {e}")
            # Fallback to direct worker usage
            try:
                print("🔄 Falling back to direct simple note worker...")
                result = self.knowledge_worker.run(self._create_worker_prompt(message, conversation_history))
                response = self._parse_agent_response(result, message)
                return response
            except Exception as e2:
                print(f"Fallback also failed: {e2}")
                return ChatResponse(
                    response=f"I encountered an error while organizing your input: {str(e)}",
                    categories=["Error"],
                    knowledge_updates=[],
                    suggested_actions=["Try rephrasing your input", "Check system logs for details"]
                )

    async def stream_response(self, message: str, conversation_history: List[ChatMessage] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream the agent's processing with detailed action updates
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Start with initialization
            yield {"type": "action", "action": "Starting", "details": "Initializing knowledge system", "timestamp": datetime.now().isoformat()}
            
            # Create prompts
            manager_prompt = await self._create_manager_prompt(message, conversation_history)
            worker_prompt = self._create_worker_prompt(message, conversation_history)
            
            yield {"type": "action", "action": "Planning", "details": "Analyzing your request and determining approach", "timestamp": datetime.now().isoformat()}
            
            # Execute agent
            result = None
            execution_error = None
            try:
                if hasattr(self.manager_agent, 'ask_managed_agent'):
                    worker_request = f"""
Process this user input and organize it into appropriate notes:
{message}

Follow these steps:
1. Search existing notes to find relevant locations
2. Decide whether to create new notes or update existing ones
3. Place the information in appropriate location(s)
4. Create basic wiki-links [[note name]] for connections
5. Keep content minimal and focused on user input only

IMPORTANT: Do not add external knowledge or research. Only organize what the user provided.
"""
                    yield {"type": "action", "action": "Coordinating", "details": "Activating knowledge management workflow", "timestamp": datetime.now().isoformat()}
                    
                    # Stream real-time agent execution and capture result
                    async for step_data in self._stream_agent_execution(self.manager_agent, worker_request, "manager"):
                        if step_data["type"] == "execution_result":
                            result = step_data["result"]
                            execution_error = step_data["error"]
                        else:
                            yield step_data
                    
                    # If execution failed, raise the error
                    if execution_error:
                        raise execution_error
                else:
                    yield {"type": "action", "action": "Processing", "details": "Working directly with knowledge tools", "timestamp": datetime.now().isoformat()}
                    
                    # Stream real-time worker execution and capture result
                    async for step_data in self._stream_agent_execution(self.knowledge_worker, worker_prompt, "worker"):
                        if step_data["type"] == "execution_result":
                            result = step_data["result"]
                            execution_error = step_data["error"]
                        else:
                            yield step_data
                    
                    # If execution failed, raise the error
                    if execution_error:
                        raise execution_error
                    
            except Exception as e:
                yield {"type": "action", "action": "Error Handling", "details": f"Encountering issue: {str(e)[:100]}...", "timestamp": datetime.now().isoformat()}
                
                # Fallback execution - capture result from fallback as well
                async for step_data in self._stream_agent_execution(self.knowledge_worker, worker_prompt, "fallback"):
                    if step_data["type"] == "execution_result":
                        result = step_data["result"]
                        execution_error = step_data["error"]
                    else:
                        yield step_data
                
                # If fallback also failed, re-raise the error
                if execution_error:
                    raise execution_error
            
            # Final processing
            yield {"type": "action", "action": "Finalizing", "details": "Organizing response and updating knowledge graph", "timestamp": datetime.now().isoformat()}
            
            # Parse and simplify the response
            response = self._parse_agent_response(result, message)
            
            # Create a clean, simple final response
            clean_response_text = self._create_clean_response(response, message)
            
            # Ensure we have some response text
            if not clean_response_text or clean_response_text.strip() == "":
                if result and str(result).strip():
                    clean_response_text = str(result).strip()
                else:
                    clean_response_text = "I've processed your request and organized the information in your knowledge base."
            
            clean_response = {
                "response": clean_response_text,
                "categories": response.categories,
                "knowledge_updates": [update.dict() for update in response.knowledge_updates],
                "suggested_actions": response.suggested_actions[:3]  # Limit to 3 suggestions
            }
            
            print(f"DEBUG: Sending complete response with {len(clean_response_text)} characters")
            
            yield {"type": "action", "action": "Complete", "details": "Knowledge organization finished successfully", "timestamp": datetime.now().isoformat()}
            yield {"type": "complete", "response": clean_response}
            
        except Exception as e:
            yield {"type": "error", "message": str(e)}
    
    async def _stream_agent_execution(self, agent, prompt: str, agent_name: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream agent execution with detailed action updates and return result"""
        try:
            # Get initial step count
            initial_step_count = 0
            if hasattr(agent, 'memory') and hasattr(agent.memory, 'steps'):
                initial_step_count = len(agent.memory.steps)
            
            yield {"type": "action", "action": f"{agent_name.title()} Starting", "details": "Beginning analysis", "timestamp": datetime.now().isoformat()}
            
            # Start execution in a separate thread
            execution_finished = threading.Event()
            execution_result = {'result': None, 'error': None}
            
            def run_agent():
                try:
                    if agent_name == "manager" and hasattr(agent, 'ask_managed_agent'):
                        result = agent.ask_managed_agent(
                            agent=self.knowledge_worker,
                            request=prompt,
                            timeout=30
                        )
                    else:
                        result = agent.run(prompt)
                    execution_result['result'] = result
                except Exception as e:
                    execution_result['error'] = e
                finally:
                    execution_finished.set()
            
            # Start agent execution
            agent_thread = threading.Thread(target=run_agent)
            agent_thread.start()
            
            # Monitor agent memory for new steps
            last_processed_step = initial_step_count
            
            while not execution_finished.is_set():
                # Check for new steps in agent memory
                if hasattr(agent, 'memory') and hasattr(agent.memory, 'steps'):
                    current_steps = agent.memory.steps
                    
                    # Process new steps
                    for i in range(last_processed_step, len(current_steps)):
                        step = current_steps[i]
                        
                        # Get step details
                        step_type = type(step).__name__
                        step_content = str(getattr(step, 'output', ''))
                        
                        # Enhanced tool extraction - try multiple approaches
                        tool_name = None
                        tool_input = None
                        
                        # Method 1: Direct attributes
                        if hasattr(step, 'tool_name'):
                            tool_name = step.tool_name
                        if hasattr(step, 'tool_input'):
                            tool_input = step.tool_input
                        
                        # Method 2: Check for tool_calls in step
                        if not tool_name and hasattr(step, 'tool_calls'):
                            tool_calls = step.tool_calls
                            if tool_calls and len(tool_calls) > 0:
                                first_call = tool_calls[0]
                                if hasattr(first_call, 'name'):
                                    tool_name = first_call.name
                                if hasattr(first_call, 'arguments'):
                                    tool_input = first_call.arguments
                        
                        # Method 3: Parse from step content/output
                        if not tool_name and step_content:
                            # Look for tool patterns in content
                            if "search_knowledge" in step_content.lower():
                                tool_name = "search_knowledge"
                            elif "create_knowledge_note" in step_content.lower():
                                tool_name = "create_knowledge_note"
                            elif "update_knowledge_note" in step_content.lower():
                                tool_name = "update_knowledge_note"
                            elif "find_related_notes" in step_content.lower():
                                tool_name = "find_related_notes"
                            elif "browse_web_content" in step_content.lower():
                                tool_name = "browse_web_content"
                            elif "summarize_web_links" in step_content.lower():
                                tool_name = "summarize_web_links"
                        
                        # Method 4: Check if step has action attribute
                        if hasattr(step, 'action') and step.action:
                            action_obj = step.action
                            if hasattr(action_obj, 'tool_name'):
                                tool_name = action_obj.tool_name
                            if hasattr(action_obj, 'tool_input'):
                                tool_input = action_obj.tool_input
                        
                        # Debug logging to understand step structure
                        if os.getenv("DEBUG") == "true":
                            print(f"DEBUG: Step {i} - Type: {step_type}")
                            print(f"DEBUG: Step attributes: {dir(step)}")
                            print(f"DEBUG: Tool name: {tool_name}")
                            print(f"DEBUG: Tool input: {tool_input}")
                            print(f"DEBUG: Step content: {step_content[:200]}...")
                            print("---")
                        
                        # Create detailed action information
                        if tool_name:
                            # Handle specific tool actions
                            if tool_name == "search_knowledge":
                                action_title = "🔍 Searching Knowledge"
                                details = f"Tool: {tool_name}"
                                if tool_input and isinstance(tool_input, dict):
                                    query = tool_input.get('query', '')
                                    if query:
                                        details += f" | Query: '{query[:50]}...'" if len(query) > 50 else f" | Query: '{query}'"
                                else:
                                    details += " | Looking for existing notes"
                            elif tool_name == "create_knowledge_note":
                                action_title = "📝 Creating Note"
                                details = f"Tool: {tool_name}"
                                if tool_input and isinstance(tool_input, dict):
                                    title = tool_input.get('title', '')
                                    category = tool_input.get('category', '')
                                    if title:
                                        details += f" | Title: '{title}'"
                                    if category:
                                        details += f" | Category: {category}"
                                else:
                                    details += " | Creating new note"
                            elif tool_name == "update_knowledge_note":
                                action_title = "✏️ Updating Note"
                                details = f"Tool: {tool_name}"
                                if tool_input and isinstance(tool_input, dict):
                                    title = tool_input.get('title', '')
                                    if title:
                                        details += f" | Title: '{title}'"
                                else:
                                    details += " | Updating existing note"
                            elif tool_name == "find_related_notes":
                                action_title = "🔗 Finding Connections"
                                details = f"Tool: {tool_name}"
                                if tool_input and isinstance(tool_input, dict):
                                    query = tool_input.get('query', '')
                                    if query:
                                        details += f" | Query: '{query}'"
                                else:
                                    details += " | Finding related notes"
                            elif tool_name == "browse_web_content":
                                action_title = "🌐 Browsing Web"
                                details = f"Tool: {tool_name}"
                                if tool_input and isinstance(tool_input, dict):
                                    url = tool_input.get('url', '')
                                    if url:
                                        details += f" | URL: {url[:50]}..."
                                else:
                                    details += " | Extracting web content"
                            elif tool_name == "summarize_web_links":
                                action_title = "📋 Processing Links"
                                details = f"Tool: {tool_name}"
                                if tool_input and isinstance(tool_input, dict):
                                    text = tool_input.get('text', '')
                                    if text:
                                        details += f" | Text: {text[:30]}..."
                                else:
                                    details += " | Processing multiple links"
                            else:
                                action_title = f"🔧 Using {tool_name}"
                                details = f"Tool: {tool_name}"
                                if tool_input:
                                    details += f" | Input: {str(tool_input)[:100]}..."
                        else:
                            # Handle non-tool steps with better detection
                            if "thinking" in step_type.lower() or "thought" in step_type.lower():
                                action_title = "💭 Thinking"
                                details = f"Step: {step_type} | Analyzing approach"
                            elif "code" in step_type.lower():
                                action_title = "⚙️ Processing"
                                details = f"Step: {step_type} | Processing content"
                            elif "planning" in step_type.lower():
                                action_title = "📋 Planning"
                                details = f"Step: {step_type} | Planning approach"
                            elif "task" in step_type.lower():
                                action_title = "📋 Task Execution"
                                details = f"Step: {step_type}"
                                # Try to extract more context from task steps
                                if step_content:
                                    content_preview = step_content[:100].replace('\n', ' ')
                                    details += f" | Content: {content_preview}..."
                            elif "action" in step_type.lower():
                                action_title = "⚡ Action"
                                details = f"Step: {step_type}"
                                # Try to extract more context from action steps
                                if step_content:
                                    content_preview = step_content[:100].replace('\n', ' ')
                                    details += f" | Content: {content_preview}..."
                            else:
                                action_title = f"🔄 {step_type}"
                                details = f"Step: {step_type}"
                                if step_content:
                                    content_preview = step_content[:100].replace('\n', ' ')
                                    details += f" | Content: {content_preview}..."
                        
                        # Add step output if available and meaningful
                        if step_content and len(step_content) > 10:
                            # Extract meaningful information from output
                            if "created" in step_content.lower():
                                details += " → Note created successfully"
                            elif "updated" in step_content.lower():
                                details += " → Note updated successfully"
                            elif "found" in step_content.lower():
                                details += " → Found relevant information"
                            elif "connected" in step_content.lower():
                                details += " → Created connections"
                        
                        yield {
                            "type": "action", 
                            "action": action_title, 
                            "details": details,
                            "timestamp": datetime.now().isoformat(),
                            "agent": agent_name,
                            "step_type": step_type,
                            "tool_name": tool_name
                        }
                        
                        last_processed_step = i + 1
                        
                        # Brief pause to prevent overwhelming the stream
                        await asyncio.sleep(0.1)
                
                # Brief pause before checking again
                await asyncio.sleep(0.5)
            
            # Wait for thread to complete
            agent_thread.join()
            
            # Check for execution errors and yield final result
            if execution_result['error']:
                yield {
                    "type": "action", 
                    "action": "❌ Error", 
                    "details": f"{agent_name} execution failed: {str(execution_result['error'])[:100]}...",
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent_name
                }
                # Return error result to caller
                yield {
                    "type": "execution_result",
                    "result": None,
                    "error": execution_result['error']
                }
            else:
                yield {
                    "type": "action", 
                    "action": f"✅ {agent_name.title()} Complete", 
                    "details": "Analysis finished successfully",
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent_name
                }
                # Return successful result to caller
                yield {
                    "type": "execution_result",
                    "result": execution_result['result'],
                    "error": None
                }
            
        except Exception as e:
            yield {
                "type": "action", 
                "action": "❌ Monitoring Error", 
                "details": f"Error monitoring {agent_name}: {str(e)[:100]}...",
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name
            }
            # Return error result to caller
            yield {
                "type": "execution_result",
                "result": None,
                "error": e
            }
    
    async def _stream_post_execution_steps(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream final steps summary"""
        try:
            # Get a simple summary of what was accomplished
            actions_taken = []
            
            # Check both agents for recent actions
            for agent_name, agent in [("manager", self.manager_agent), ("worker", self.knowledge_worker)]:
                if agent and hasattr(agent, 'memory') and hasattr(agent.memory, 'steps'):
                    if agent.memory.steps:
                        last_step = agent.memory.steps[-1]
                        summary = self.action_reporter.get_intelligent_summary(last_step)
                        if summary and summary not in actions_taken:
                            actions_taken.append(summary)
            
            if actions_taken:
                for i, action in enumerate(actions_taken[-2:]):  # Last 2 unique actions
                    yield {"type": "action", "action": "Summary", "details": action}
                    await asyncio.sleep(0.1)
            else:
                yield {"type": "action", "action": "Summary", "details": "Knowledge organization completed"}
                
        except Exception as e:
            yield {"type": "action", "action": "Summary", "details": "Processing completed"}

    async def _create_manager_prompt(self, message: str, conversation_history: List[ChatMessage] = None) -> str:
        """Create a focused prompt for the simple knowledge manager agent"""
        # Get graph statistics
        graph_stats = {}
        try:
            graph_stats = await self.enhanced_graph.get_statistics()
        except:
            graph_stats = {"total_nodes": 0, "total_edges": 0}
        
        prompt_parts = [
            "You are a Simple Knowledge Manager focused on organizing user input into appropriate notes.",
            "Your role is to take user input and place it in the right location(s) without adding external knowledge.",
            "",
            "SYSTEM OVERVIEW:",
            "- You manage a Knowledge Worker Agent that handles note operations",
            "- The system supports wiki-links [[note name]] and basic relationships",
            "- Focus on organizing user input, not researching or expanding content",
            "",
            f"CURRENT GRAPH STATE:",
            f"- Notes directory: {self.notes_dir}",
            f"- Total existing notes: {graph_stats.get('total_nodes', 0)}",
            f"- Existing categories: {', '.join(graph_stats.get('categories', {}).keys())}",
            "",
            "CORE PRINCIPLES:",
            "1. Process ONLY the user's input - do not add external knowledge",
            "2. Search existing notes to find relevant locations",
            "3. Create new notes only when necessary",
            "4. Update existing notes when appropriate",
            "5. Place information in multiple locations if relevant",
            "6. Maintain basic wiki-links and relationships",
            "7. Keep content minimal and focused",
            "",
            "AVAILABLE MANAGED AGENT:",
            "- knowledge_worker: Simple note management specialist",
            "",
            "COORDINATION STRATEGY:",
            "1. Analyze the user's input (do not expand or research)",
            "2. Search for existing relevant notes",
            "3. Decide whether to create new notes or update existing ones",
            "4. Place information in appropriate location(s)",
            "5. Maintain basic relationships and wiki-links",
            "",
            "TASK DELEGATION GUIDELINES:",
            "- For new content: Use worker to create minimal notes from user input",
            "- For existing content: Use worker to update relevant notes",
            "- For organization: Use worker to place content in appropriate categories",
            "- For connections: Use worker to create basic wiki-links when relevant",
            "",
            f"USER INPUT: {message}",
            "",
            "Process this input and organize it appropriately. Focus on placement and organization, not expansion."
        ]
        
        if conversation_history:
            prompt_parts.insert(-4, "CONVERSATION CONTEXT:")
            for msg in conversation_history[-3:]:
                role = "User" if msg.sender == "user" else "Assistant"
                prompt_parts.insert(-4, f"{role}: {msg.content}")
            prompt_parts.insert(-4, "")
        
        return "\n".join(prompt_parts)
    
    def _create_worker_prompt(self, message: str, conversation_history: List[ChatMessage] = None) -> str:
        """Create a focused prompt for the simple knowledge worker"""
        prompt_parts = [
            "You are a simple knowledge management worker focused on organizing user input into notes.",
            "Your goal is to take user input and place it in appropriate note locations without adding external knowledge.",
            "",
            f"DIRECTORY STRUCTURE:",
            f"- Notes directory: {self.notes_dir}",
            f"- Knowledge base: {self.knowledge_base_dir}",
            "",
            "CORE OPERATIONS:",
            "1. Search existing notes to find relevant locations",
            "2. Create new notes only when necessary",
            "3. Update existing notes when appropriate",
            "4. Use basic wiki-links [[note name]] for connections",
            "5. Place content in multiple locations if relevant",
            "6. Keep content minimal and focused on user input",
            "",
            "AVAILABLE TOOLS:",
            "- unified_search: Comprehensive search combining semantic, grep, title, and tag search",
            "- search_knowledge: Find existing relevant notes (semantic search)",
            "- create_knowledge_note: Create new notes from user input",
            "- update_knowledge_note: Update existing notes",
            "- find_related_notes: Find connections for wiki-links",
            "- decide_note_action: Intelligently decide whether to create or update notes",
            "- browse_web_content: Extract and summarize content from web URLs",
            "- summarize_web_links: Process multiple URLs from text input",
            "",
            "IMPORTANT GUIDELINES:",
            "- ONLY use the user's input - do not add external knowledge or research",
            "- Search first to avoid creating duplicate notes",
            "- Keep notes simple and focused",
            "- Create wiki-links to connect related concepts",
            "- Place information in multiple relevant locations when appropriate",
            "- Improve wording/diction but don't add new information",
            "",
            f"User input: {message}",
            "",
            "Process this input by:",
            "1. Searching for existing relevant notes",
            "2. Deciding whether to create new notes or update existing ones",
            "3. Placing the information appropriately",
            "4. Creating basic connections with wiki-links"
        ]
        
        if conversation_history:
            prompt_parts.insert(-6, "Recent conversation:")
            for msg in conversation_history[-3:]:
                role = "User" if msg.sender == "user" else "Assistant"
                prompt_parts.insert(-6, f"{role}: {msg.content}")
            prompt_parts.insert(-6, "")
        
        return "\n".join(prompt_parts)
    
    def _parse_agent_response(self, agent_result: str, original_message: str) -> ChatResponse:
        """Parse the enhanced agent's response and extract structured information"""
        try:
            response_text = str(agent_result)
            
            # Try to get additional info from manager agent memory
            if self.manager_agent and hasattr(self.manager_agent, 'memory') and hasattr(self.manager_agent.memory, 'steps'):
                steps = self.manager_agent.memory.steps
                if steps:
                    last_step = steps[-1]
                    if hasattr(last_step, 'output') and last_step.output:
                        response_text = str(last_step.output)
            
            # Enhanced parsing for PKM features
            categories = self._extract_categories_from_response(response_text)
            knowledge_updates = self._extract_enhanced_knowledge_updates(response_text)
            suggested_actions = self._generate_enhanced_suggested_actions(response_text, original_message)
            
            return ChatResponse(
                response=response_text,
                categories=categories,
                knowledge_updates=knowledge_updates,
                suggested_actions=suggested_actions
            )
            
        except Exception as e:
            print(f"Error parsing enhanced agent response: {e}")
            return ChatResponse(
                response=str(agent_result),
                categories=["General"],
                knowledge_updates=[],
                suggested_actions=["Continue the conversation"]
            )
    
    def _extract_categories_from_response(self, response: str) -> List[str]:
        """Extract categories from the agent's response"""
        categories = []
        
        # Look for category mentions in the response
        common_categories = [
            "Quick Notes", "Learning", "Projects", "Ideas", "Research", 
            "Tasks", "References", "Personal", "Technical", "Business"
        ]
        
        response_lower = response.lower()
        for category in common_categories:
            if category.lower() in response_lower:
                categories.append(category)
        
        return categories if categories else ["General"]
    
    def _extract_enhanced_knowledge_updates(self, response: str) -> List[KnowledgeUpdate]:
        """Extract enhanced knowledge updates from the agent's response"""
        updates = []
        
        # Look for PKM-specific updates
        if "wiki-link" in response.lower() or "[[" in response:
            updates.append(KnowledgeUpdate(
                action="linked",
                category="Wiki-Links",
                content="Wiki-links processed",
                node_id=str(hash(response))
            ))
        
        if "relationship" in response.lower() or "parent_of" in response.lower():
            updates.append(KnowledgeUpdate(
                action="related",
                category="Typed Relationships",
                content="Typed relationships created",
                node_id=str(hash(response))
            ))
        
        if "hierarchy" in response.lower() or "parent" in response.lower():
            updates.append(KnowledgeUpdate(
                action="organized",
                category="Hierarchy",
                content="Hierarchical structure updated",
                node_id=str(hash(response))
            ))
        
        # Original update detection
        if "created note" in response.lower() or "note created" in response.lower():
            updates.append(KnowledgeUpdate(
                action="added",
                category="Notes",
                content="New note created",
                node_id=str(hash(response))
            ))
        
        if "updated note" in response.lower() or "note updated" in response.lower():
            updates.append(KnowledgeUpdate(
                action="updated",
                category="Notes", 
                content="Note updated",
                node_id=str(hash(response))
            ))
        
        if "knowledge graph" in response.lower() or "relationships" in response.lower():
            updates.append(KnowledgeUpdate(
                action="connected",
                category="Knowledge Graph",
                content="Knowledge relationships analyzed",
                node_id=str(hash(response))
            ))
        
        return updates
    
    def _generate_enhanced_suggested_actions(self, response: str, original_message: str) -> List[str]:
        """Generate enhanced suggested actions based on PKM capabilities"""
        suggestions = []
        
        # PKM-specific suggestions
        if "wiki-link" in response.lower() or "[[" in response:
            suggestions.extend([
                "Explore backlinks to see what references this note",
                "Create more wiki-links to build connections",
                "Analyze the knowledge graph for insights"
            ])
        
        if "relationship" in response.lower() or "parent" in response.lower():
            suggestions.extend([
                "Review the hierarchical structure",
                "Add more typed relationships (supports, contradicts, etc.)",
                "Explore related notes in the same hierarchy"
            ])
        
        if "orphan" in response.lower() or "broken" in response.lower():
            suggestions.extend([
                "Fix broken links in the knowledge graph",
                "Connect orphaned notes to the main graph",
                "Run a comprehensive graph analysis"
            ])
        
        # Original suggestions
        if "note" in response.lower():
            suggestions.extend([
                "Expand the note with additional details",
                "Find related notes and create connections",
                "Organize notes into better categories"
            ])
        
        if "search" in response.lower() or "found" in response.lower():
            suggestions.extend([
                "Refine search with more specific criteria",
                "Explore related knowledge areas",
                "Create notes from search findings"
            ])
        
        # Enhanced system suggestions
        suggestions.extend([
            "Use wiki-links [[note name]] to create connections",
            "Add typed relationships like parent_of or supports",
            "Explore the knowledge graph visualization",
            "Ask for graph analytics and insights"
        ])
        
        return list(set(suggestions))  # Remove duplicates

    # Enhanced delegate methods using the new graph system
    async def get_knowledge_graph(self) -> Dict[str, Any]:
        """Get the enhanced knowledge graph data"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return await self.enhanced_graph.get_graph_data()
        except Exception as e:
            print(f"Error getting enhanced knowledge graph: {e}")
            return {"nodes": [], "edges": [], "error": str(e)}
    
    async def search_knowledge(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search the enhanced knowledge base"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return await self.enhanced_graph.search_semantic(query, limit)
        except Exception as e:
            print(f"Error searching enhanced knowledge: {e}")
            return []
    
    async def get_all_notes(self) -> List[Dict[str, Any]]:
        """Get all notes from the enhanced system (without content for efficiency)"""
        if not self.initialized:
            await self.initialize()
        
        try:
            notes = []
            for node in self.enhanced_graph.nodes_by_id.values():
                notes.append({
                    "title": node.title,
                    "category": node.category,
                    "tags": node.tags,
                    "path": node.file_path,
                    "updated_at": node.updated_at,
                    "content_hash": node.content_hash,
                    "metadata": node.metadata
                })
            return notes
        except Exception as e:
            print(f"Error getting all notes: {e}")
            return []
    
    async def search_content_in_files(self, query: str, case_sensitive: bool = False, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for content in actual files using grep-like functionality"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return await self.enhanced_graph.search_content_in_files(query, case_sensitive, limit)
        except Exception as e:
            print(f"Error searching content in files: {e}")
            return []
    
    async def unified_search(
        self, 
        query: str, 
        limit: int = 20,
        include_semantic: bool = True,
        include_grep: bool = True,
        include_title: bool = True,
        include_tag: bool = True,
        semantic_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Unified search that combines multiple search methods for comprehensive results
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            include_semantic: Include semantic search results
            include_grep: Include grep/content search results  
            include_title: Include title matching results
            include_tag: Include tag matching results
            semantic_threshold: Minimum similarity score for semantic results
            
        Returns:
            List of unified search results with snippets and context
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Use the enhanced knowledge graph's unified search
            results = await self.enhanced_graph.unified_search(
                query=query,
                limit=limit,
                include_semantic=include_semantic,
                include_grep=include_grep,
                include_title=include_title,
                include_tag=include_tag,
                semantic_threshold=semantic_threshold
            )
            
            # Convert to dictionary format for easier consumption
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
            
            return search_results
            
        except Exception as e:
            print(f"Error in unified search: {e}")
            return []
    
    async def get_pkm_statistics(self) -> Dict[str, Any]:
        """Get comprehensive PKM statistics"""
        if not self.initialized:
            await self.initialize()
        
        try:
            stats = await self.enhanced_graph.get_statistics()
            watcher_stats = self.file_watcher.get_statistics()
            
            return {
                "graph_stats": stats,
                "watcher_stats": watcher_stats,
                "system_info": {
                    "notes_directory": str(self.notes_dir),
                    "knowledge_base_directory": str(self.knowledge_base_dir),
                    "model_name": self.model_name,
                    "features": [
                        "Wiki-links [[note name]]",
                        "Typed relationships",
                        "YAML front-matter",
                        "Hierarchical organization",
                        "Semantic search",
                        "Backlink analysis",
                        "Incremental updates"
                    ]
                }
            }
        except Exception as e:
            print(f"Error getting PKM statistics: {e}")
            return {"error": str(e)}
    
    def get_agent_logs(self) -> List[Dict[str, Any]]:
        """Get logs from the enhanced hierarchical agent system"""
        logs = []
        
        # Get logs from Knowledge Manager
        if self.manager_agent and hasattr(self.manager_agent, 'memory') and hasattr(self.manager_agent.memory, 'steps'):
            for i, step in enumerate(self.manager_agent.memory.steps):
                log_entry = {
                    "step": i,
                    "agent": "enhanced_manager",
                    "type": type(step).__name__,
                    "timestamp": getattr(step, 'timestamp', None),
                }
                
                if hasattr(step, 'input'):
                    log_entry["input"] = str(step.input)
                if hasattr(step, 'output'):
                    log_entry["output"] = str(step.output)
                if hasattr(step, 'action'):
                    log_entry["action"] = str(step.action)
                
                logs.append(log_entry)
        
        # Get logs from Enhanced Knowledge Worker
        if self.knowledge_worker and hasattr(self.knowledge_worker, 'memory') and hasattr(self.knowledge_worker.memory, 'steps'):
            for i, step in enumerate(self.knowledge_worker.memory.steps):
                log_entry = {
                    "step": len(logs) + i,
                    "agent": "enhanced_worker",
                    "type": type(step).__name__,
                    "timestamp": getattr(step, 'timestamp', None),
                }
                
                if hasattr(step, 'input'):
                    log_entry["input"] = str(step.input)
                if hasattr(step, 'output'):
                    log_entry["output"] = str(step.output)
                if hasattr(step, 'action'):
                    log_entry["action"] = str(step.action)
                
                logs.append(log_entry)
        
        return logs
    
    def reset_agent_memory(self):
        """Reset both agents' memory for a fresh start"""
        try:
            # Reset Simple Knowledge Worker
            if self.knowledge_worker:
                self.knowledge_worker = ToolCallingAgent(
                    model=self.model,
                    tools=KNOWLEDGE_TOOLS,
                    max_steps=8,
                    verbosity_level=1,
                    planning_interval=2,
                    name="knowledge_worker",
                    description="""A focused knowledge management worker for simple note organization with web browsing capabilities:
- Process user input and find appropriate note locations
- Create minimal new notes or update existing ones
- Maintain wiki-links [[note name]] and basic relationships
- Search existing notes to avoid duplication
- Place information in multiple relevant locations when appropriate
- Keep knowledge graph updated with new connections
- Browse web URLs to extract and summarize content from links
- Augment information with relevant web content when URLs are provided
- Focus on user input - do not add external knowledge unless explicitly requested via URLs

IMPORTANT: Only work with the user's input. Do not expand, research, or add external knowledge unless the user provides URLs to browse. Simply organize what the user provides.""",
                    provide_run_summary=True,
                )
            
            # Reset Simple Knowledge Manager
            if self.manager_agent:
                self.manager_agent = CodeAgent(
                    model=self.model,
                    tools=[],
                    max_steps=10,
                    verbosity_level=1,
                    additional_authorized_imports=["json", "asyncio", "datetime", "hashlib", "typing", "collections"],
                    planning_interval=3,
                    name="knowledge_manager",
                    description="Simple knowledge management coordinator focused on note placement and organization"
                )
                
                # Add managed agents
                self.manager_agent.managed_agents = [self.knowledge_worker]
                
            print("🔄 Reset Simple Knowledge Agent System")
        except Exception as e:
            print(f"Error resetting simple agent memory: {e}")
    
    # Legacy compatibility methods (deprecated but maintained for existing code)
    @property
    def tool_agent(self):
        """Legacy compatibility: return enhanced knowledge worker"""
        return self.knowledge_worker
    
    @property 
    def code_agent(self):
        """Legacy compatibility: return enhanced manager agent"""
        return self.manager_agent
    
    def _requires_complex_reasoning(self, message: str) -> bool:
        """Legacy compatibility: always use hierarchical system now"""
        return True  # Enhanced hierarchical system handles all complexity levels
    
    async def sync_knowledge_base(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Sync the knowledge base with the current vault state
        
        Args:
            force_rebuild: If True, force a complete rebuild regardless of changes
            
        Returns:
            Detailed sync results including changes detected and actions taken
        """
        if not self.initialized:
            await self.initialize()
        
        print(f"🔄 Starting knowledge base sync (force_rebuild={force_rebuild})...")
        
        start_time = datetime.now()
        cleanup_results = None
        
        try:
            # If force rebuild, clean everything first
            if force_rebuild:
                print("🧹 Force rebuild mode: Cleaning all storage...")
                cleanup_results = await self._clean_all_storage()
                
            # Get current vault state
            vault_files = self._scan_vault_files()
            
            # Get existing knowledge graph state
            graph_files = set()
            for node in self.enhanced_graph.nodes_by_id.values():
                if node.file_path:
                    graph_files.add(node.file_path)
            
            # Detect changes
            changes = self._detect_changes(vault_files, graph_files, force_rebuild)
            
            # Process changes
            sync_results = await self._process_sync_changes(changes)
            
            # Clean up any orphaned entries in vector database
            await self._clean_orphaned_vector_entries()
            
            # Update statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Final sync report
            final_results = {
                "sync_completed": True,
                "processing_time_seconds": processing_time,
                "timestamp": start_time.isoformat(),
                "vault_files_found": len(vault_files),
                "graph_nodes_before": len(self.enhanced_graph.nodes_by_id),
                "changes_detected": changes,
                "actions_taken": sync_results.get("actions_taken", []),
                "graph_nodes_after": len(self.enhanced_graph.nodes_by_id),
                "graph_edges_after": len(self.enhanced_graph.edges_by_id),
                "errors": sync_results.get("errors", []),
                "warnings": sync_results.get("warnings", [])
            }
            
            # Add cleanup results if force rebuild was used
            if force_rebuild and cleanup_results:
                final_results["cleanup_results"] = cleanup_results
            
            print(f"✅ Knowledge base sync completed in {processing_time:.2f}s")
            print(f"   📊 Files: {len(vault_files)}, Nodes: {len(self.enhanced_graph.nodes_by_id)}, Edges: {len(self.enhanced_graph.edges_by_id)}")
            
            return final_results
            
        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            error_results = {
                "sync_completed": False,
                "error": error_msg,
                "processing_time_seconds": (datetime.now() - start_time).total_seconds(),
                "timestamp": start_time.isoformat()
            }
            
            # Include cleanup results even if sync failed
            if force_rebuild and cleanup_results:
                error_results["cleanup_results"] = cleanup_results
            
            return error_results
    
    def _scan_vault_files(self) -> Dict[str, Dict[str, Any]]:
        """Scan the vault directory for all markdown files"""
        vault_files = {}
        
        notes_path = Path(self.notes_dir)
        if not notes_path.exists():
            return vault_files
        
        for md_file in notes_path.rglob("*.md"):
            try:
                # Get file stats
                stat = md_file.stat()
                
                # Calculate content hash
                content = md_file.read_text(encoding='utf-8')
                content_hash = self.enhanced_graph.hash_tracker.hash_cache.get(
                    str(md_file), {}
                ).get('hash', '')
                
                # Calculate current hash
                from knowledge.hash_utils import calculate_content_hash
                current_hash = calculate_content_hash(content)
                
                vault_files[str(md_file)] = {
                    "path": str(md_file),
                    "size": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime),
                    "content_hash": current_hash,
                    "cached_hash": content_hash,
                    "content": content
                }
                
            except Exception as e:
                print(f"   ⚠️  Error reading {md_file}: {e}")
        
        return vault_files
    
    def _detect_changes(self, vault_files: Dict[str, Dict[str, Any]], 
                       graph_files: Set[str], force_rebuild: bool) -> Dict[str, Any]:
        """Detect what has changed between vault and graph"""
        
        vault_paths = set(vault_files.keys())
        
        # Find different types of changes
        new_files = vault_paths - graph_files
        deleted_files = graph_files - vault_paths
        potentially_modified = vault_paths & graph_files
        
        # Check for actual content changes
        modified_files = set()
        unchanged_files = set()
        
        for file_path in potentially_modified:
            vault_file = vault_files[file_path]
            if (force_rebuild or 
                vault_file["content_hash"] != vault_file["cached_hash"] or
                not vault_file["cached_hash"]):
                modified_files.add(file_path)
            else:
                unchanged_files.add(file_path)
        
        return {
            "new_files": list(new_files),
            "deleted_files": list(deleted_files),
            "modified_files": list(modified_files),
            "unchanged_files": list(unchanged_files),
            "total_changes": len(new_files) + len(deleted_files) + len(modified_files),
            "force_rebuild": force_rebuild
        }
    
    async def _process_sync_changes(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Process the detected changes"""
        actions_taken = []
        errors = []
        warnings = []
        
        try:
            # Handle deleted files
            for file_path in changes["deleted_files"]:
                try:
                    await self._remove_file_from_graph(file_path)
                    actions_taken.append(f"Removed deleted file: {file_path}")
                except Exception as e:
                    errors.append(f"Error removing {file_path}: {str(e)}")
            
            # Handle new files
            for file_path in changes["new_files"]:
                try:
                    await self._add_file_to_graph(file_path)
                    actions_taken.append(f"Added new file: {file_path}")
                except Exception as e:
                    errors.append(f"Error adding {file_path}: {str(e)}")
            
            # Handle modified files
            for file_path in changes["modified_files"]:
                try:
                    await self._update_file_in_graph(file_path)
                    actions_taken.append(f"Updated modified file: {file_path}")
                except Exception as e:
                    errors.append(f"Error updating {file_path}: {str(e)}")
            
            # Resolve wiki-links after all changes
            if changes["total_changes"] > 0:
                try:
                    await self.enhanced_graph._resolve_wiki_links()
                    actions_taken.append("Resolved wiki-links")
                except Exception as e:
                    errors.append(f"Error resolving wiki-links: {str(e)}")
                
                # Save the updated graph
                try:
                    await self.enhanced_graph._save_graph()
                    actions_taken.append("Saved updated graph")
                except Exception as e:
                    errors.append(f"Error saving graph: {str(e)}")
            
            # Clean up hash cache
            try:
                valid_files = set(changes["new_files"] + changes["modified_files"] + changes["unchanged_files"])
                self.enhanced_graph.hash_tracker.cleanup_stale_entries(valid_files)
                actions_taken.append("Cleaned up hash cache")
            except Exception as e:
                warnings.append(f"Error cleaning hash cache: {str(e)}")
            
        except Exception as e:
            errors.append(f"Critical sync error: {str(e)}")
        
        return {
            "actions_taken": actions_taken,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _remove_file_from_graph(self, file_path: str):
        """Remove a file from the knowledge graph"""
        # Find the node for this file
        node_to_remove = None
        for node in self.enhanced_graph.nodes_by_id.values():
            if node.file_path == file_path:
                node_to_remove = node
                break
        
        if node_to_remove:
            node_id = node_to_remove.id
            
            # Remove from ChromaDB first
            try:
                if self.enhanced_graph.collection:
                    self.enhanced_graph.collection.delete(ids=[node_id])
                    print(f"   🗑️  Removed from ChromaDB: {node_id}")
            except Exception as e:
                print(f"   ⚠️  Error removing from ChromaDB: {e}")
            
            # Remove from indexes
            self.enhanced_graph.nodes_by_id.pop(node_id, None)
            self.enhanced_graph.title_to_id.pop(node_to_remove.title, None)
            
            # Remove from category index
            if node_to_remove.category in self.enhanced_graph.category_index:
                self.enhanced_graph.category_index[node_to_remove.category].discard(node_id)
                # Clean up empty category sets
                if not self.enhanced_graph.category_index[node_to_remove.category]:
                    del self.enhanced_graph.category_index[node_to_remove.category]
            
            # Remove from tag index
            for tag in node_to_remove.tags:
                if tag in self.enhanced_graph.tag_index:
                    self.enhanced_graph.tag_index[tag].discard(node_id)
                    # Clean up empty tag sets
                    if not self.enhanced_graph.tag_index[tag]:
                        del self.enhanced_graph.tag_index[tag]
            
            # Remove from hierarchy index
            if node_to_remove.parent_id:
                if node_to_remove.parent_id in self.enhanced_graph.hierarchy_index:
                    self.enhanced_graph.hierarchy_index[node_to_remove.parent_id].discard(node_id)
                    # Clean up empty hierarchy sets
                    if not self.enhanced_graph.hierarchy_index[node_to_remove.parent_id]:
                        del self.enhanced_graph.hierarchy_index[node_to_remove.parent_id]
            
            # Remove edges
            edges_to_remove = []
            for edge_id, edge in self.enhanced_graph.edges_by_id.items():
                if edge.source_id == node_id or edge.target_id == node_id:
                    edges_to_remove.append(edge_id)
            
            for edge_id in edges_to_remove:
                self.enhanced_graph.edges_by_id.pop(edge_id, None)
            
            # Remove from NetworkX graph
            if node_id in self.enhanced_graph.graph:
                self.enhanced_graph.graph.remove_node(node_id)
            
            # Remove from hash tracker
            self.enhanced_graph.hash_tracker.remove_note_mapping(file_path)
            
            print(f"   🗑️  Removed node: {node_to_remove.title}")
        else:
            print(f"   ⚠️  No node found for file: {file_path}")
    
    async def _add_file_to_graph(self, file_path: str):
        """Add a new file to the knowledge graph"""
        file_path_obj = Path(file_path)
        
        # Parse the file
        parsed_note = self.enhanced_graph.markdown_parser.parse_file(file_path_obj)
        
        # Add to graph
        await self.enhanced_graph._add_parsed_note(file_path_obj, parsed_note)
        
        print(f"   ✨ Added node: {parsed_note.title}")
    
    async def _update_file_in_graph(self, file_path: str):
        """Update an existing file in the knowledge graph"""
        # Remove the old version
        await self._remove_file_from_graph(file_path)
        
        # Add the new version
        await self._add_file_to_graph(file_path)
        
        print(f"   🔄 Updated node for: {file_path}") 

    async def _clean_all_storage(self) -> Dict[str, Any]:
        """
        Clean all storage components including vector databases
        Used in force_rebuild scenarios
        """
        cleanup_results = {
            "actions_taken": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # 1. Clean ChromaDB collection
            print("   🗑️  Cleaning ChromaDB collection...")
            try:
                if self.enhanced_graph.collection:
                    # Get all existing IDs
                    existing_ids = self.enhanced_graph.collection.get()["ids"]
                    if existing_ids:
                        self.enhanced_graph.collection.delete(ids=existing_ids)
                        cleanup_results["actions_taken"].append(f"Removed {len(existing_ids)} entries from ChromaDB")
                    else:
                        cleanup_results["actions_taken"].append("ChromaDB collection was already empty")
                else:
                    cleanup_results["warnings"].append("ChromaDB collection not initialized")
            except Exception as e:
                cleanup_results["errors"].append(f"Error cleaning ChromaDB: {str(e)}")
            
            # 2. Clear all graph indexes
            print("   🗑️  Clearing graph indexes...")
            try:
                old_nodes_count = len(self.enhanced_graph.nodes_by_id)
                old_edges_count = len(self.enhanced_graph.edges_by_id)
                
                self.enhanced_graph.nodes_by_id.clear()
                self.enhanced_graph.edges_by_id.clear()
                self.enhanced_graph.title_to_id.clear()
                self.enhanced_graph.category_index.clear()
                self.enhanced_graph.tag_index.clear()
                self.enhanced_graph.hierarchy_index.clear()
                self.enhanced_graph.graph.clear()
                
                cleanup_results["actions_taken"].append(f"Cleared {old_nodes_count} nodes and {old_edges_count} edges from graph indexes")
            except Exception as e:
                cleanup_results["errors"].append(f"Error clearing graph indexes: {str(e)}")
            
            # 3. Clear hash cache
            print("   🗑️  Clearing hash cache...")
            try:
                cache_stats_before = self.enhanced_graph.hash_tracker.get_cache_stats()
                self.enhanced_graph.hash_tracker.clear_cache()
                cleanup_results["actions_taken"].append(f"Cleared hash cache ({cache_stats_before['total_cached_items']} items, {cache_stats_before['total_mapped_notes']} mappings)")
            except Exception as e:
                cleanup_results["errors"].append(f"Error clearing hash cache: {str(e)}")
            
            # 4. Remove saved graph file
            print("   🗑️  Removing saved graph file...")
            try:
                import os
                graph_path = os.path.join(self.enhanced_graph.knowledge_base_path, "enhanced_graph.json")
                if os.path.exists(graph_path):
                    os.remove(graph_path)
                    cleanup_results["actions_taken"].append("Removed saved graph file")
                else:
                    cleanup_results["actions_taken"].append("No saved graph file to remove")
            except Exception as e:
                cleanup_results["errors"].append(f"Error removing saved graph file: {str(e)}")
            
            # 5. Clear NetworkX graph
            print("   🗑️  Clearing NetworkX graph...")
            try:
                self.enhanced_graph.graph.clear()
                cleanup_results["actions_taken"].append("Cleared NetworkX graph")
            except Exception as e:
                cleanup_results["errors"].append(f"Error clearing NetworkX graph: {str(e)}")
            
            print(f"   ✅ Storage cleanup completed: {len(cleanup_results['actions_taken'])} actions, {len(cleanup_results['errors'])} errors")
            
        except Exception as e:
            cleanup_results["errors"].append(f"Critical cleanup error: {str(e)}")
        
        return cleanup_results
    
    async def _clean_orphaned_vector_entries(self):
        """
        Clean up orphaned entries in the vector database that don't have corresponding graph nodes
        """
        try:
            if not self.enhanced_graph.collection:
                return
            
            # Get all IDs in ChromaDB
            chroma_data = self.enhanced_graph.collection.get()
            chroma_ids = set(chroma_data["ids"]) if chroma_data["ids"] else set()
            
            # Get all IDs in graph
            graph_ids = set(self.enhanced_graph.nodes_by_id.keys())
            
            # Find orphaned IDs (in ChromaDB but not in graph)
            orphaned_ids = chroma_ids - graph_ids
            
            if orphaned_ids:
                print(f"   🧹 Found {len(orphaned_ids)} orphaned vector entries, cleaning...")
                self.enhanced_graph.collection.delete(ids=list(orphaned_ids))
                print(f"   ✅ Cleaned {len(orphaned_ids)} orphaned vector entries")
            
        except Exception as e:
            print(f"   ⚠️  Error cleaning orphaned vector entries: {e}") 

    def _create_clean_response(self, response: ChatResponse, original_message: str) -> str:
        """Create a clean, readable response for the user"""
        try:
            # Extract the main response content
            main_response = response.response
            
            print(f"DEBUG: Raw response content: {main_response[:300]}...")
            
            if not main_response or main_response.strip() == "":
                print("DEBUG: Empty response, using fallback")
                # Fallback to summary based on what was done
                if response.knowledge_updates:
                    updates = len(response.knowledge_updates)
                    if updates == 1:
                        return f"I've organized your information and created a note in the {response.categories[0] if response.categories else 'appropriate'} category."
                    else:
                        return f"I've organized your information and created {updates} notes in your knowledge base."
                else:
                    return "I've processed your request and organized the information in your knowledge base."
            
            # First, try to extract "Final answer:" section if it exists
            if "Final answer:" in main_response:
                print("DEBUG: Found 'Final answer:' in response")
                final_answer_start = main_response.find("Final answer:")
                if final_answer_start != -1:
                    final_answer_content = main_response[final_answer_start + 13:].strip()
                    print(f"DEBUG: Extracted final answer: {final_answer_content[:200]}...")
                    
                    # Clean the final answer content
                    final_lines = final_answer_content.split('\n')
                    clean_final_lines = []
                    
                    for line in final_lines:
                        line = line.strip()
                        if (line and 
                            not (line.startswith('[') and line.endswith(']') and 'Step' in line and 'Duration' in line) and
                            not line.lower().startswith('input tokens:') and
                            not line.lower().startswith('output tokens:')):
                            clean_final_lines.append(line)
                    
                    if clean_final_lines:
                        cleaned_final = '\n'.join(clean_final_lines)
                        print(f"DEBUG: Returning cleaned final answer: {cleaned_final[:200]}...")
                        return cleaned_final
            
            # If no final answer, clean up the full response
            print("DEBUG: No 'Final answer:' found, cleaning full response")
            lines = main_response.split('\n')
            clean_lines = []
            
            for line in lines:
                line = line.strip()
                # Only skip truly technical lines, preserve most content
                if (line and 
                    not line.startswith('```') and 
                    not line.startswith('json') and
                    not line.startswith('{"') and
                    not line.startswith('}') and
                    not (line.startswith('[') and line.endswith(']') and 'Step' in line and 'Duration' in line) and
                    not line.lower().startswith('input tokens:') and
                    not line.lower().startswith('output tokens:')):
                    clean_lines.append(line)
            
            if clean_lines:
                # Join the lines
                cleaned_response = '\n'.join(clean_lines)
                print(f"DEBUG: Cleaned response length: {len(cleaned_response)}")
                
                # Limit response length for UI
                if len(cleaned_response) > 1000:
                    cleaned_response = cleaned_response[:800] + "\n\n[Response truncated for brevity]"
                
                print(f"DEBUG: Returning cleaned response: {cleaned_response[:200]}...")
                return cleaned_response
            else:
                print("DEBUG: No clean lines found, using knowledge updates fallback")
                # If no clean lines found, use fallback
                if response.knowledge_updates:
                    updates = len(response.knowledge_updates)
                    if updates == 1:
                        return f"I've organized your information and created a note in the {response.categories[0] if response.categories else 'appropriate'} category."
                    else:
                        return f"I've organized your information and created {updates} notes in your knowledge base."
                else:
                    return "I've processed your request and organized the information in your knowledge base." 
        except Exception as e:
            print(f"Error in _create_clean_response: {e}")
            return "I've successfully organized your information into your knowledge base." 