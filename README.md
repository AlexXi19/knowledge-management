# Knowledge Management Frontend

An intelligent knowledge management system with a React frontend featuring chat interface and interactive knowledge graph visualization.

## ✨ Features

### 🗨️ **Chat Interface**

- Interactive chat with AI knowledge agent
- Real-time message processing
- Conversation history
- Automatic knowledge categorization
- Smart note creation and organization

### 🕸️ **Knowledge Graph Visualization** ⭐ NEW!

- Interactive node-and-edge graph visualization using ReactFlow
- Color-coded nodes by category (Learning, Research, Projects, etc.)
- Click nodes to view detailed note content in modal popup
- Automatic graph layout with circular positioning
- Real-time graph updates when new notes are created
- Minimap and zoom controls for easy navigation

## 🏗️ **Architecture**

### Frontend Stack

- **React 19** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Radix UI** for accessible components
- **ReactFlow** for knowledge graph visualization
- **Lucide React** for icons

### UI Components

- Tabs interface for switching between Chat and Knowledge Graph
- Modal dialogs for note content display
- Loading states and error handling
- Responsive design for all screen sizes

## 🚀 **Getting Started**

### Prerequisites

- Node.js 18+
- npm or bun
- Backend service running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:5173

### Backend Integration

The frontend connects to the backend API at `http://localhost:8000` with the following endpoints:

- `POST /chat` - Chat with the AI agent
- `GET /knowledge/graph` - Get knowledge graph data
- `GET /notes` - Get all notes
- `GET /knowledge/search` - Search knowledge base

## 📊 **Knowledge Graph Features**

### Node Visualization

- **Color Coding**: Each category has a unique color
  - Ideas to Develop: Red (#ff6b6b)
  - Personal: Teal (#4ecdc4)
  - Research: Blue (#45b7d1)
  - Reading List: Green (#96ceb4)
  - Projects: Yellow (#ffc107)
  - Learning: Purple (#9b59b6)
  - Quick Notes: Gray (#95a5a6)
  - Technical: Red (#e74c3c)
  - Business: Orange (#f39c12)

### Interactive Features

- **Click to View**: Click any node to see full note content
- **Modal Display**: Rich note details in popup modal with:
  - Note title and category
  - Full content with formatting
  - Creation and update timestamps
  - Tags and metadata
  - File path information

### Graph Controls

- **Zoom & Pan**: Mouse wheel to zoom, drag to pan
- **Minimap**: Overview of entire graph in corner
- **Fit View**: Automatic fitting of graph to viewport
- **Refresh**: Manual refresh button to reload graph data

## 🎨 **User Interface**

### Layout

```
┌─────────────────────────────────────────┐
│ Knowledge Manager                       │
├─────────────────────────────────────────┤
│ [Chat] [Knowledge Graph] ← Tabs         │
├─────────────────────────────────────────┤
│                                         │
│  Chat Interface OR Knowledge Graph      │
│                                         │
│                                         │
└─────────────────────────────────────────┘
```

### Chat Tab

- Message bubbles with user/agent distinction
- Input field with send button
- Typing indicators
- Conversation history

### Knowledge Graph Tab

- Full-screen graph visualization
- Info panel showing node/edge counts
- Refresh button for manual updates
- Interactive node selection

## 🔧 **Development**

### Project Structure

```
src/
├── components/
│   ├── KnowledgeGraph.tsx  ← Graph visualization
│   └── ui/                 ← Radix UI components
├── App.tsx                 ← Main app with tabs
├── main.tsx               ← App entry point
└── index.css              ← Global styles
```

### Key Components

#### `App.tsx`

- Main application component with tab navigation
- Chat interface implementation
- API integration for chat functionality

#### `KnowledgeGraph.tsx`

- ReactFlow-based graph visualization
- Node click handling and modal display
- API integration for graph data
- Color-coded category visualization
- Loading and error states

### API Integration

```typescript
// Fetch knowledge graph data
const response = await fetch('http://localhost:8000/knowledge/graph');
const data = await response.json();

// Convert to ReactFlow format
const nodes = data.graph.nodes.map(node => ({
  id: node.id,
  position: { x: ..., y: ... },
  data: { label: node.metadata.title },
  style: { background: getCategoryColor(node.category) }
}));
```

## 🎯 **Usage**

### Creating Knowledge

1. Use the **Chat** tab to interact with the AI agent
2. Ask it to create notes: _"Create a note about machine learning"_
3. The agent will categorize and store your knowledge
4. Switch to **Knowledge Graph** tab to visualize

### Viewing Knowledge Graph

1. Click the **Knowledge Graph** tab
2. See your notes as colored nodes
3. Click any node to view its content
4. Use minimap and controls to navigate
5. Click **Refresh** to update with new notes

### Modal Content View

When you click a node, you'll see:

- Note title and category badge
- Full note content with formatting
- Creation and update dates
- Associated tags
- File path where note is stored

## 🛠️ **Configuration**

### Environment Variables

```bash
# Backend API URL (default: http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000
```

### Customization

- **Colors**: Edit `getCategoryColor()` in `KnowledgeGraph.tsx`
- **Layout**: Modify node positioning algorithm
- **Styling**: Update Tailwind classes or CSS variables

## 📝 **Notes**

- The knowledge graph displays nodes from the backend's knowledge graph endpoint
- Edges between nodes represent relationships detected by the AI
- Graph updates automatically when new notes are created via chat
- Modal content shows the full note information stored in the backend
- The system works even without API keys (for testing the UI)

## 🔄 **Recent Updates**

### Version 2.0 - Knowledge Graph Visualization

- ✅ Added interactive knowledge graph visualization
- ✅ Implemented ReactFlow-based node-edge display
- ✅ Created modal popup for note content viewing
- ✅ Added color-coded category visualization
- ✅ Integrated with backend knowledge graph API
- ✅ Added tab navigation between Chat and Graph views
- ✅ Implemented loading states and error handling

The frontend now provides a complete knowledge management experience with both conversational and visual interfaces! 🎉
