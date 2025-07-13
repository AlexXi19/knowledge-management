"""
Action Reporter for streaming updates in the knowledge management system
"""
from typing import Any
from datetime import datetime


class ActionReporter:
    """
    Simple action reporter for user-friendly streaming updates
    """
    
    def __init__(self):
        self.actions = []
        self.current_action = None
        
    def start_action(self, action: str, details: str = None):
        """Start a new action"""
        self.current_action = {
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.actions.append(self.current_action)
        
    def update_action(self, details: str):
        """Update current action details"""
        if self.current_action:
            self.current_action["details"] = details
            
    def complete_action(self, result: str = None):
        """Complete current action"""
        if self.current_action:
            self.current_action["completed"] = True
            if result:
                self.current_action["result"] = result
                
    def get_action_summary(self) -> str:
        """Get a simple summary of actions taken"""
        if not self.actions:
            return "No actions taken"
        
        summary_parts = []
        for action in self.actions[-3:]:  # Last 3 actions
            action_text = action["action"]
            if action.get("details"):
                action_text += f": {action['details']}"
            summary_parts.append(action_text)
        
        return " → ".join(summary_parts)
        
    def get_intelligent_summary(self, agent_step: Any) -> str:
        """Generate simple, user-friendly summaries of agent steps"""
        try:
            step_type = type(agent_step).__name__
            step_content = str(getattr(agent_step, 'output', ''))
            
            # Extract tool usage
            if hasattr(agent_step, 'tool_name'):
                tool_name = agent_step.tool_name
                if tool_name == "search_knowledge":
                    return f"Searched existing notes"
                elif tool_name == "create_knowledge_note":
                    return f"Created new note"
                elif tool_name == "update_knowledge_note":
                    return f"Updated existing note"
                elif tool_name == "browse_web_content":
                    return f"Browsed web content"
                elif tool_name == "find_related_notes":
                    return f"Found related notes"
                else:
                    return f"Used {tool_name}"
            
            # Simple step descriptions
            if step_type == "ToolCallStep" or step_type == "ToolCall":
                return "Using knowledge tools"
            elif step_type == "ThinkingStep" or step_type == "ThoughtStep":
                return "Planning approach"
            elif step_type == "CodeStep":
                return "Processing content"
            elif step_type == "OutputStep":
                return "Organizing information"
            else:
                return "Working on your request"
                
        except Exception as e:
            return "Processing" 