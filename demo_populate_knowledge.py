#!/usr/bin/env python3
"""
Demo script to populate the knowledge base with sample data for testing
"""
import asyncio
import os
from pathlib import Path
from agent.knowledge_agent import KnowledgeAgent

# Sample notes data to create
SAMPLE_NOTES = [
    {
        "title": "Introduction to Machine Learning",
        "content": """Machine Learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.

Key concepts:
- Supervised Learning: Learning with labeled data
- Unsupervised Learning: Finding patterns in unlabeled data  
- Reinforcement Learning: Learning through interaction and rewards

Applications include image recognition, natural language processing, and recommendation systems.""",
        "category": "Learning",
        "tags": ["AI", "ML", "technology"]
    },
    {
        "title": "Python Best Practices",
        "content": """Collection of Python programming best practices:

1. Follow PEP 8 style guide
2. Use virtual environments for project isolation
3. Write docstrings for functions and classes
4. Handle exceptions properly with try/except blocks
5. Use list comprehensions for simple transformations
6. Leverage built-in functions like map(), filter(), zip()
7. Use type hints for better code documentation

Remember: "Readability counts" - The Zen of Python""",
        "category": "Technical",
        "tags": ["Python", "programming", "best-practices"]
    },
    {
        "title": "Project Ideas for AI Assistant",
        "content": """Ideas for enhancing the AI assistant:

1. Add voice interface capabilities
2. Integrate with calendar and scheduling
3. Create specialized domain experts (coding, writing, research)
4. Add memory persistence across sessions
5. Implement multi-modal understanding (text, images, documents)
6. Create workflow automation features
7. Add collaborative features for team use

These could make the assistant more useful for daily productivity.""",
        "category": "Ideas to Develop",
        "tags": ["AI", "assistant", "productivity", "features"]
    },
    {
        "title": "Knowledge Management Research",
        "content": """Research findings on effective knowledge management systems:

Key principles:
- Information should be easily discoverable
- Context and relationships matter more than isolated facts
- Regular review and updating prevents knowledge decay
- Visual representations help understanding
- Collaborative knowledge building improves quality

Tools and methods:
- Mind mapping for visual organization
- Tagging systems for flexible categorization
- Graph databases for relationship modeling
- Search and recommendation engines
- Version control for knowledge evolution""",
        "category": "Research",
        "tags": ["knowledge-management", "research", "organization"]
    },
    {
        "title": "Reading List - AI and Technology",
        "content": """Books and articles to read:

Books:
1. "Artificial Intelligence: A Modern Approach" by Russell & Norvig
2. "The Hundred-Page Machine Learning Book" by Andriy Burkov
3. "Design Patterns" by Gang of Four
4. "Clean Code" by Robert Martin

Articles:
- "Attention Is All You Need" (Transformer paper)
- "BERT: Pre-training of Deep Bidirectional Transformers"
- "GPT-3: Language Models are Few-Shot Learners"

Websites:
- Towards Data Science (Medium)
- AI Research papers on arXiv
- GitHub trending repositories""",
        "category": "Reading List",
        "tags": ["reading", "AI", "books", "research-papers"]
    },
    {
        "title": "Personal Learning Goals",
        "content": """My learning objectives for this year:

Technical Skills:
- Master advanced Python features and design patterns
- Learn cloud computing (AWS/Azure/GCP)
- Understand microservices architecture
- Get familiar with MLOps and model deployment

Soft Skills:
- Improve technical writing and documentation
- Practice public speaking and presentations
- Develop project management skills
- Build better collaboration habits

Projects:
- Build a personal knowledge management system
- Create an open-source contribution
- Write technical blog posts
- Mentor junior developers""",
        "category": "Personal",
        "tags": ["goals", "learning", "career", "skills"]
    },
    {
        "title": "Current Project: Knowledge Graph System",
        "content": """Working on building an intelligent knowledge management system:

Features implemented:
✓ Chat interface with AI agent
✓ Automatic note categorization
✓ Hash-based content tracking
✓ Vector embeddings for similarity search
✓ Knowledge graph visualization

Next steps:
- Improve graph layout algorithms
- Add relationship detection between notes
- Implement collaborative features
- Create mobile app interface
- Add export/import capabilities

Technical stack:
- Backend: Python, FastAPI, NetworkX, ChromaDB
- Frontend: React, TypeScript, ReactFlow, Tailwind CSS
- AI: LLM integration with multiple providers""",
        "category": "Projects",
        "tags": ["project", "knowledge-graph", "AI", "development"]
    }
]

async def populate_knowledge_base():
    """Populate the knowledge base with sample data"""
    
    print("🚀 Populating Knowledge Base with Sample Data")
    print("=" * 50)
    
    # Initialize agent with default directory
    agent = KnowledgeAgent()
    await agent.initialize()
    
    print(f"✅ Knowledge Agent initialized")
    
    created_notes = []
    
    for i, note_data in enumerate(SAMPLE_NOTES, 1):
        print(f"\n{i}. Creating note: {note_data['title']}")
        
        try:
            # For now, let's use the tools directly since we don't have API keys
            # This simulates what the agent would do
            from agent.knowledge_tools import _knowledge_tools_manager
            await _knowledge_tools_manager.initialize()
            
            # Create note using the notes manager directly
            note = await _knowledge_tools_manager.notes_manager.create_note(
                title=note_data['title'],
                content=note_data['content'],
                category=note_data['category'],
                tags=note_data.get('tags', [])
            )
            
            # Add to knowledge graph
            await _knowledge_tools_manager.knowledge_graph.add_node(
                content=note_data['content'],
                category=note_data['category'],
                metadata={
                    "title": note_data['title'],
                    "source": "demo_script",
                    "content_type": "note",
                    "tags": note_data.get('tags', []),
                    "note_path": note.path
                }
            )
            
            created_notes.append(note)
            print(f"   ✅ Created: {note.path}")
            
        except Exception as e:
            print(f"   ❌ Error creating note: {e}")
    
    print(f"\n🎉 Successfully created {len(created_notes)} notes!")
    
    # Show summary
    print("\n📊 Knowledge Base Summary:")
    print(f"   📝 Total notes: {len(created_notes)}")
    
    categories = {}
    for note in created_notes:
        category = note.category
        categories[category] = categories.get(category, 0) + 1
    
    print("   📂 Categories:")
    for category, count in categories.items():
        print(f"      • {category}: {count} notes")
    
    print("\n🌐 Knowledge Graph:")
    try:
        graph_data = await agent.get_knowledge_graph()
        if 'nodes' in graph_data:
            print(f"   🔸 Nodes: {len(graph_data['nodes'])}")
            print(f"   🔗 Edges: {len(graph_data.get('edges', []))}")
        else:
            print("   ⚠️  Graph data structure unexpected")
    except Exception as e:
        print(f"   ❌ Error getting graph data: {e}")
    
    print("\n🎯 Next Steps:")
    print("1. Start the frontend: cd frontend && npm run dev")
    print("2. Start the backend: cd backend && uv run python main.py")
    print("3. Open http://localhost:5173 and click on the 'Knowledge Graph' tab")
    print("4. You should see the sample notes as nodes in the graph!")

if __name__ == "__main__":
    asyncio.run(populate_knowledge_base()) 