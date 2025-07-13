"""
Knowledge Agent powered by smolagents for intelligent knowledge management
Enhanced with PKM features: wiki-links, typed relationships, and compiled graph indexing
"""
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import os
from datetime import datetime
import json
from pathlib import Path

from smolagents import ToolCallingAgent, CodeAgent, InferenceClientModel, LiteLLMModel
from models.chat_models import ChatMessage, ChatResponse, KnowledgeUpdate, SearchResult
from agent.knowledge_tools import KNOWLEDGE_TOOLS, _knowledge_tools_manager
from knowledge.enhanced_knowledge_graph import get_enhanced_knowledge_graph
from knowledge.file_watcher import get_knowledge_graph_watcher, start_file_watcher
import litellm

# Enable LiteLLM debugging if DEBUG env var is set
if os.getenv("DEBUG") == "true":
    litellm._turn_on_debug()


class ProgressSummarizer:
    """
    Intelligent progress summarization system for Knowledge Agent operations
    """
    
    def __init__(self):
        self.current_phase = "initializing"
        self.total_phases = 5
        self.current_step = 0
        self.steps_in_current_phase = 0
        self.operation_type = "knowledge_management"
        self.detailed_steps = []
        self.phase_descriptions = {
            "initializing": "🚀 Setting up note management",
            "analyzing": "🔍 Analyzing your input",
            "processing": "⚙️ Finding and organizing notes",
            "organizing": "📚 Placing content in appropriate locations",
            "finalizing": "✅ Completing note organization"
        }
        
    def start_operation(self, operation_type: str, total_phases: int = 5):
        """Start a new operation with progress tracking"""
        self.operation_type = operation_type
        self.total_phases = total_phases
        self.current_step = 0
        self.current_phase = "initializing"
        self.detailed_steps = []
        
    def advance_phase(self, phase_name: str, steps_in_phase: int = 1):
        """Advance to the next phase"""
        self.current_phase = phase_name
        self.steps_in_current_phase = steps_in_phase
        self.current_step = 0
        
    def add_step(self, step_description: str, details: Dict[str, Any] = None):
        """Add a detailed step to the current operation"""
        step_info = {
            "phase": self.current_phase,
            "step": self.current_step,
            "description": step_description,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.detailed_steps.append(step_info)
        self.current_step += 1
        
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a comprehensive progress summary"""
        phase_index = list(self.phase_descriptions.keys()).index(self.current_phase)
        overall_progress = (phase_index / self.total_phases) * 100
        
        if self.steps_in_current_phase > 0:
            phase_progress = (self.current_step / self.steps_in_current_phase) * 100
            overall_progress += (phase_progress / self.total_phases)
        
        return {
            "overall_progress": min(overall_progress, 100),
            "current_phase": self.current_phase,
            "phase_description": self.phase_descriptions.get(self.current_phase, "Processing..."),
            "phase_progress": min((self.current_step / max(self.steps_in_current_phase, 1)) * 100, 100),
            "total_phases": self.total_phases,
            "operation_type": self.operation_type,
            "detailed_steps": self.detailed_steps[-5:],  # Last 5 steps
            "current_step": self.current_step,
            "steps_in_phase": self.steps_in_current_phase
        }
        
    def get_intelligent_summary(self, agent_step: Any) -> str:
        """Generate intelligent summary based on agent step type and content"""
        step_type = type(agent_step).__name__
        
        # Map agent step types to user-friendly descriptions
        step_mappings = {
            "ToolCallStep": "🔧 Using note management tools",
            "CodeStep": "💻 Processing note data",
            "ThinkingStep": "🤔 Deciding note placement",
            "OutputStep": "📝 Preparing note organization",
            "PlanningStep": "📋 Planning note operations",
            "ToolResultStep": "✅ Note operation completed",
            "AgentStep": "🤖 Coordinating note management",
            "UserStep": "👤 Processing user input"
        }
        
        base_summary = step_mappings.get(step_type, f"⚙️ {step_type}")
        
        # Add specific details based on step content
        if hasattr(agent_step, 'output') and agent_step.output:
            output_str = str(agent_step.output).lower()
            if "wiki-link" in output_str or "[[" in output_str:
                return f"{base_summary} - Adding wiki-links"
            elif "search" in output_str or "finding" in output_str:
                return f"{base_summary} - Searching existing notes"
            elif "created" in output_str or "creating" in output_str:
                return f"{base_summary} - Creating new note"
            elif "updated" in output_str or "updating" in output_str:
                return f"{base_summary} - Updating existing note"
            elif "note" in output_str:
                return f"{base_summary} - Managing notes"
            elif "categoriz" in output_str or "organiz" in output_str:
                return f"{base_summary} - Organizing content"
                
        if hasattr(agent_step, 'action') and agent_step.action:
            action_str = str(agent_step.action).lower()
            if "tool" in action_str:
                return f"{base_summary} - Using note tools"
            elif "code" in action_str:
                return f"{base_summary} - Processing notes"
                
        return base_summary
        
    def extract_progress_metrics(self, agent_memory) -> Dict[str, Any]:
        """Extract detailed progress metrics from agent memory"""
        metrics = {
            "tools_used": [],
            "knowledge_operations": [],
            "processing_time": 0,
            "completion_status": "in_progress"
        }
        
        if hasattr(agent_memory, 'steps'):
            for step in agent_memory.steps:
                step_type = type(step).__name__
                
                # Track tools used
                if step_type == "ToolCallStep" and hasattr(step, 'tool_name'):
                    metrics["tools_used"].append(step.tool_name)
                
                # Track knowledge operations
                if hasattr(step, 'output') and step.output:
                    output_str = str(step.output).lower()
                    if any(op in output_str for op in ["created", "updated", "linked", "analyzed"]):
                        metrics["knowledge_operations"].append({
                            "type": step_type,
                            "description": self.get_intelligent_summary(step),
                            "timestamp": getattr(step, 'timestamp', datetime.now().isoformat())
                        })
                        
        return metrics


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
        self.progress_summarizer = ProgressSummarizer()
        
        # Enhanced knowledge graph
        self.enhanced_graph = get_enhanced_knowledge_graph()
        self.file_watcher = get_knowledge_graph_watcher()
        
        # Set up directory structure
        self.setup_directories(dir)
        
        self._setup_model()
    
    def setup_directories(self, dir: str = None):
        """
        Set up the directory structure for notes and knowledge base
        
        Args:
            dir: Base directory for the knowledge system
        """
        if dir is None:
            dir = os.getcwd()  # Use current working directory as default
        
        self.base_dir = Path(dir).resolve()
        self.notes_dir = self.base_dir
        self.knowledge_base_dir = self.base_dir / '.knowledge_base'
        
        # Create directories if they don't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Set environment variables for the knowledge components
        os.environ['NOTES_DIRECTORY'] = str(self.notes_dir)
        os.environ['KNOWLEDGE_BASE_PATH'] = str(self.knowledge_base_dir)
        
        print(f"📁 Simple Knowledge System initialized:")
        print(f"   📝 Notes directory: {self.notes_dir}")
        print(f"   🧠 Knowledge base: {self.knowledge_base_dir}")
        print(f"   🔗 Basic wiki-links and note organization enabled")
        
        # Initialize knowledge tools manager with the custom directory
        _knowledge_tools_manager.setup_directories(str(self.notes_dir), str(self.knowledge_base_dir))
    
    def _setup_model(self):
        """Setup the LLM model for the agents with support for multiple providers"""
        try:
            # Check for OpenRouter API key first (highest priority - access to all models)
            openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            if openrouter_api_key:
                # Use specified OpenRouter model or default to Claude 3.5 Sonnet
                openrouter_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
                try:
                    # Set OpenRouter environment variables as per documentation
                    os.environ["OPENROUTER_API_KEY"] = openrouter_api_key
                    os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"
                    
                    # Add openrouter/ prefix if not already present
                    if not openrouter_model.startswith("openrouter/"):
                        openrouter_model = f"openrouter/{openrouter_model}"
                    
                    self.model = LiteLLMModel(
                        model_id=openrouter_model,
                        api_key=openrouter_api_key
                    )
                    self.model_name = openrouter_model
                    print(f"✅ Using OpenRouter model: {openrouter_model}")
                    return
                except Exception as e:
                    print(f"⚠️  Error setting up OpenRouter model: {e}")
            
            # Check for Anthropic API key second (Claude Sonnet models)
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_api_key:
                # Use Claude Sonnet model if specified or default to claude-3-5-sonnet
                claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
                if any(sonnet in claude_model.lower() for sonnet in ["sonnet", "claude-3-5", "claude-3"]):
                    try:
                        self.model = LiteLLMModel(
                            model_id=claude_model,
                            api_key=anthropic_api_key
                        )
                        self.model_name = claude_model
                        print(f"✅ Using Anthropic Claude model: {claude_model}")
                        return
                    except Exception as e:
                        print(f"⚠️  Error setting up Anthropic model: {e}")
            
            # Try to use HuggingFace model third
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                self.model = InferenceClientModel(
                    model_id=self.model_name,
                    token=hf_token
                )
                print(f"✅ Using HuggingFace model: {self.model_name}")
                return
            
            # Try OpenAI as fourth option
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                self.model = LiteLLMModel(
                    model_id=openai_model,
                    api_key=openai_api_key
                )
                self.model_name = openai_model
                print(f"✅ Using OpenAI model: {openai_model}")
                return
            
            # Final fallback to HuggingFace without token (rate limited but free)
            try:
                fallback_model = "microsoft/DialoGPT-medium"
                self.model = InferenceClientModel(
                    model_id=fallback_model
                )
                self.model_name = fallback_model
                print(f"✅ Using fallback HuggingFace model: {fallback_model}")
            except Exception as e2:
                print(f"❌ Even fallback model failed: {e2}")
                # Create a basic model for testing
                self.model = InferenceClientModel(
                    model_id="microsoft/DialoGPT-medium"
                )
                
        except Exception as e:
            print(f"❌ Error setting up model: {e}")
            # Final fallback
            self.model = InferenceClientModel(
                model_id="microsoft/DialoGPT-medium"
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
            description="""A focused knowledge management worker for simple note organization:
- Process user input and find appropriate note locations
- Create minimal new notes or update existing ones
- Maintain wiki-links [[note name]] and basic relationships
- Search existing notes to avoid duplication
- Place information in multiple relevant locations when appropriate
- Keep knowledge graph updated with new connections
- Focus on user input - do not add external knowledge or research

IMPORTANT: Only work with the user's input. Do not expand, research, or add external knowledge. Simply organize what the user provides.""",
            provide_run_summary=True,
        )
        
        # Create Knowledge Manager Agent (CodeAgent) that manages the worker
        self.manager_agent = CodeAgent(
            model=self.model,
            tools=[],  # Manager focuses on coordination and simple note management
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
        print("🤖 Simple Knowledge Agent System Ready!")
        print(f"   📚 Note Worker: {self.knowledge_worker.name}")
        print(f"   🧠 Note Manager: {self.manager_agent.name}")
        print(f"   🔗 Graph: {len(self.enhanced_graph.nodes_by_id)} notes, {len(self.enhanced_graph.edges_by_id)} connections")
        print(f"   👀 File watcher: {'Active' if self.file_watcher.is_running else 'Inactive'}")

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
        prompt = self._create_manager_prompt(message, conversation_history)
        
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
    
    def _create_manager_prompt(self, message: str, conversation_history: List[ChatMessage] = None) -> str:
        """Create a focused prompt for the simple knowledge manager agent"""
        # Get graph statistics
        graph_stats = {}
        try:
            graph_stats = asyncio.run(self.enhanced_graph.get_statistics())
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
            "- search_knowledge: Find existing relevant notes",
            "- create_knowledge_note: Create new notes from user input",
            "- update_knowledge_note: Update existing notes",
            "- find_related_notes: Find connections for wiki-links",
            "- get_all_notes: Overview of existing notes",
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
    
    async def stream_response(self, message: str, conversation_history: List[ChatMessage] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream the simple note organization agent's processing steps with intelligent progress tracking
        """
        if not self.initialized:
            await self.initialize()
        
        # Initialize progress tracking
        self.progress_summarizer.start_operation("knowledge_management", 5)
        
        # Phase 1: Initialization
        self.progress_summarizer.advance_phase("initializing", 3)
        yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
        
        self.progress_summarizer.add_step("Setting up note management system")
        yield {"type": "status", "message": "🚀 Initializing Note Management System..."}
        
        # Create prompts
        manager_prompt = self._create_manager_prompt(message, conversation_history)
        worker_prompt = self._create_worker_prompt(message, conversation_history)
        
        self.progress_summarizer.add_step("Analyzing user input")
        yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
        
        self.progress_summarizer.add_step("Preparing note organization strategy")
        yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
        
        # Phase 2: Analysis
        self.progress_summarizer.advance_phase("analyzing", 2)
        yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
        
        try:
            self.progress_summarizer.add_step("Coordinating with note manager")
            yield {"type": "status", "message": "🧠 Note Manager coordinating request..."}
            yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
            
            # Phase 3: Processing
            self.progress_summarizer.advance_phase("processing", 6)
            yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
            
            # Try hierarchical approach first
            result = None
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
                    self.progress_summarizer.add_step("Executing note organization coordination")
                    yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
                    
                    result = self.manager_agent.ask_managed_agent(
                        agent=self.knowledge_worker,
                        request=worker_request,
                        timeout=30
                    )
                else:
                    self.progress_summarizer.add_step("Running note worker directly")
                    yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
                    result = self.knowledge_worker.run(worker_prompt)
                    
            except Exception as e:
                self.progress_summarizer.add_step(f"Fallback to direct note worker: {str(e)[:50]}...")
                yield {"type": "status", "message": f"🔄 Falling back to direct note worker: {str(e)[:50]}..."}
                yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
                result = self.knowledge_worker.run(worker_prompt)
            
            # Stream the worker's steps with intelligent summaries
            if hasattr(self.knowledge_worker, 'memory') and hasattr(self.knowledge_worker.memory, 'steps'):
                total_steps = len(self.knowledge_worker.memory.steps)
                for i, step in enumerate(self.knowledge_worker.memory.steps):
                    intelligent_summary = self.progress_summarizer.get_intelligent_summary(step)
                    self.progress_summarizer.add_step(intelligent_summary, {
                        "step_type": type(step).__name__,
                        "step_index": i,
                        "total_steps": total_steps
                    })
                    
                    yield {
                        "type": "step", 
                        "step": i,
                        "agent": "enhanced_worker",
                        "action": type(step).__name__,
                        "content": str(getattr(step, 'output', '')),
                        "summary": intelligent_summary,
                        "progress": (i + 1) / total_steps * 100
                    }
                    
                    # Update progress every few steps
                    if i % 2 == 0:
                        yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
            
            # Phase 4: Organization
            self.progress_summarizer.advance_phase("organizing", 2)
            yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
            
            self.progress_summarizer.add_step("Organizing note placement")
            yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
            
            # Extract progress metrics
            if hasattr(self.knowledge_worker, 'memory'):
                metrics = self.progress_summarizer.extract_progress_metrics(self.knowledge_worker.memory)
                yield {"type": "metrics", "data": metrics}
            
            # Phase 5: Finalization
            self.progress_summarizer.advance_phase("finalizing", 2)
            yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
            
            self.progress_summarizer.add_step("Preparing note organization response")
            yield {"type": "progress", "data": self.progress_summarizer.get_progress_summary()}
            
            # Final response
            response = self._parse_agent_response(result, message)
            
            self.progress_summarizer.add_step("Response complete")
            final_progress = self.progress_summarizer.get_progress_summary()
            final_progress["overall_progress"] = 100
            yield {"type": "progress", "data": final_progress}
            
            yield {"type": "complete", "response": response.model_dump()}
            
        except Exception as e:
            yield {"type": "error", "message": str(e), "progress": self.progress_summarizer.get_progress_summary()}
    
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
        """Get all notes from the enhanced system"""
        if not self.initialized:
            await self.initialize()
        
        try:
            notes = []
            for node in self.enhanced_graph.nodes_by_id.values():
                notes.append({
                    "title": node.title,
                    "content": node.content,
                    "category": node.category,
                    "tags": node.tags,
                    "path": node.file_path,
                    "updated_at": node.updated_at,
                    "metadata": node.metadata
                })
            return notes
        except Exception as e:
            print(f"Error getting all notes: {e}")
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
                    description="""A focused knowledge management worker for simple note organization:
- Process user input and find appropriate note locations
- Create minimal new notes or update existing ones
- Maintain wiki-links [[note name]] and basic relationships
- Search existing notes to avoid duplication
- Place information in multiple relevant locations when appropriate
- Keep knowledge graph updated with new connections
- Focus on user input - do not add external knowledge or research

IMPORTANT: Only work with the user's input. Do not expand, research, or add external knowledge. Simply organize what the user provides.""",
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