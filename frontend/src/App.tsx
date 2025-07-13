import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Send,
  User,
  Bot,
  Activity,
  Brain,
  Database,
  Link,
  FileText,
  BarChart3,
  Network,
  X,
} from "lucide-react";
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";

interface Message {
  id: string;
  content: string;
  sender: "user" | "agent";
  timestamp: Date;
  progress?: ProgressData;
  steps?: StepData[];
  metrics?: MetricsData;
}

interface ProgressData {
  overall_progress: number;
  current_phase: string;
  phase_description: string;
  phase_progress: number;
  total_phases: number;
  operation_type: string;
  detailed_steps: DetailedStep[];
  current_step: number;
  steps_in_phase: number;
}

interface DetailedStep {
  phase: string;
  step: number;
  description: string;
  details: any;
  timestamp: string;
}

interface StepData {
  step: number;
  agent: string;
  action: string;
  content: string;
  summary: string;
  progress: number;
}

interface MetricsData {
  tools_used: string[];
  knowledge_operations: any[];
  processing_time: number;
  completion_status: string;
}

interface KnowledgeGraphNode {
  id: string;
  title: string;
  category: string;
  content: string;
  tags: string[];
  file_path: string;
  updated_at: string;
}

interface KnowledgeGraphEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
}

interface KnowledgeGraphData {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

const SAMPLE_MESSAGES: Message[] = [
  {
    id: "1",
    content:
      "Hi! I'm your simple knowledge management agent. I can help you organize your thoughts and ideas into connected notes with wiki-links [[note name]]. Share anything you're thinking about - I'll place it in the right location without adding extra information!",
    sender: "agent",
    timestamp: new Date(Date.now() - 3600000),
  },
];

const ProgressIndicator = ({ progress }: { progress: ProgressData }) => {
  const phaseIcons = {
    initializing: <Activity className="w-4 h-4" />,
    analyzing: <Brain className="w-4 h-4" />,
    processing: <Database className="w-4 h-4" />,
    organizing: <Link className="w-4 h-4" />,
    finalizing: <FileText className="w-4 h-4" />,
  };

  return (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          {phaseIcons[progress.current_phase as keyof typeof phaseIcons] || (
            <Activity className="w-4 h-4" />
          )}
          {progress.phase_description}
        </CardTitle>
        <CardDescription className="text-xs">
          Phase {Object.keys(phaseIcons).indexOf(progress.current_phase) + 1} of{" "}
          {progress.total_phases}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Overall Progress</span>
              <span>{Math.round(progress.overall_progress)}%</span>
            </div>
            <Progress value={progress.overall_progress} className="h-2" />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Current Phase</span>
              <span>{Math.round(progress.phase_progress)}%</span>
            </div>
            <Progress value={progress.phase_progress} className="h-1" />
          </div>

          {progress.detailed_steps.length > 0 && (
            <div className="space-y-1">
              <div className="text-xs font-medium">Recent Steps:</div>
              {progress.detailed_steps.slice(-3).map((step, index) => (
                <div
                  key={index}
                  className="text-xs text-muted-foreground pl-2 border-l-2 border-muted"
                >
                  {step.description}
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const MetricsPanel = ({ metrics }: { metrics: MetricsData }) => {
  return (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <BarChart3 className="w-4 h-4" />
          Knowledge Operations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {metrics.tools_used.length > 0 && (
            <div>
              <div className="text-xs font-medium mb-2">Tools Used:</div>
              <div className="flex flex-wrap gap-1">
                {metrics.tools_used.map((tool, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {tool}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {metrics.knowledge_operations.length > 0 && (
            <div>
              <div className="text-xs font-medium mb-2">
                Knowledge Operations:
              </div>
              <div className="space-y-1">
                {metrics.knowledge_operations.slice(-5).map((op, index) => (
                  <div
                    key={index}
                    className="text-xs text-muted-foreground pl-2 border-l-2 border-muted"
                  >
                    {op.description}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center gap-2 text-xs">
            <Badge
              variant={
                metrics.completion_status === "completed"
                  ? "default"
                  : "outline"
              }
            >
              {metrics.completion_status}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const KnowledgeGraphViewer = ({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) => {
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const loadKnowledgeGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8000/knowledge/graph");
      if (!response.ok) {
        throw new Error("Failed to fetch knowledge graph");
      }
      const data = await response.json();
      setGraphData(data.graph);

      // Convert knowledge graph data to ReactFlow format with better positioning
      const nodeSpacing = 200;
      const gridCols = Math.ceil(Math.sqrt(data.graph.nodes.length));
      const gridRows = Math.ceil(data.graph.nodes.length / gridCols);

      const reactFlowNodes: Node[] = data.graph.nodes.map(
        (node: KnowledgeGraphNode, index: number) => {
          // Calculate grid position with some randomness to avoid strict grid
          const col = index % gridCols;
          const row = Math.floor(index / gridCols);

          // Add some random offset to make it more organic
          const randomOffsetX = (Math.random() - 0.5) * 60;
          const randomOffsetY = (Math.random() - 0.5) * 60;

          return {
            id: node.id,
            position: {
              x: col * nodeSpacing + 100 + randomOffsetX,
              y: row * nodeSpacing + 100 + randomOffsetY,
            },
            data: {
              label: node.title,
              category: node.category,
              tags: node.tags,
              content:
                node.content.substring(0, 100) +
                (node.content.length > 100 ? "..." : ""),
              updated_at: node.updated_at,
            },
            style: {
              backgroundColor: getCategoryColor(node.category),
              color: "#000",
              border: "2px solid #000",
              borderRadius: "8px",
              padding: "10px",
              minWidth: "120px",
              maxWidth: "200px",
            },
            type: "default",
          };
        }
      );

      const reactFlowEdges: Edge[] = data.graph.edges.map(
        (edge: KnowledgeGraphEdge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: edge.relationship_type,
          markerEnd: {
            type: MarkerType.ArrowClosed,
          },
          style: {
            stroke: "#666",
          },
          labelStyle: {
            fontSize: "10px",
            fontWeight: "bold",
          },
        })
      );

      setNodes(reactFlowNodes);
      setEdges(reactFlowEdges);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  const getCategoryColor = (category: string): string => {
    const colors: { [key: string]: string } = {
      "Quick Notes": "#fef3c7",
      Learning: "#dbeafe",
      Projects: "#d1fae5",
      Ideas: "#fce7f3",
      Research: "#e0e7ff",
      Tasks: "#fed7d7",
      References: "#e2e8f0",
      Personal: "#fef0e7",
      Technical: "#e6fffa",
      Business: "#f0fff4",
    };
    return colors[category] || "#f3f4f6";
  };

  useEffect(() => {
    if (isOpen) {
      loadKnowledgeGraph();
    }
  }, [isOpen, loadKnowledgeGraph]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] p-0">
        <DialogHeader className="p-6 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                <Network className="w-5 h-5" />
                Knowledge Graph
              </DialogTitle>
              <DialogDescription>
                Interactive visualization of your knowledge network
              </DialogDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => loadKnowledgeGraph()}
            >
              Refresh
            </Button>
          </div>
        </DialogHeader>

        <div className="flex-1 h-[70vh] relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/50 z-10">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span>Loading knowledge graph...</span>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/50 z-10">
              <div className="text-center">
                <p className="text-destructive mb-2">
                  Error loading graph: {error}
                </p>
                <Button onClick={() => loadKnowledgeGraph()}>Try Again</Button>
              </div>
            </div>
          )}

          {!loading && !error && (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              connectionMode={ConnectionMode.Loose}
              fitView
              className="bg-background"
            >
              <Background />
              <Controls />
            </ReactFlow>
          )}
        </div>

        {graphData && (
          <div className="p-6 pt-4 border-t">
            <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
              <span>📊 {graphData.nodes.length} notes</span>
              <span>🔗 {graphData.edges.length} connections</span>
              <span>
                📂 {new Set(graphData.nodes.map((n) => n.category)).size}{" "}
                categories
              </span>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default function KnowledgeManager() {
  const [messages, setMessages] = useState<Message[]>(SAMPLE_MESSAGES);
  const [inputValue, setInputValue] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentProgress, setCurrentProgress] = useState<ProgressData | null>(
    null
  );
  const [currentSteps, setCurrentSteps] = useState<StepData[]>([]);
  const [currentMetrics, setCurrentMetrics] = useState<MetricsData | null>(
    null
  );
  const [showKnowledgeGraph, setShowKnowledgeGraph] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentProgress]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputValue("");
    setIsStreaming(true);
    setCurrentProgress(null);
    setCurrentSteps([]);
    setCurrentMetrics(null);

    try {
      // Use Server-Sent Events for streaming
      const eventSource = new EventSource(`http://localhost:8000/chat/stream`, {
        // Note: EventSource doesn't support POST directly, so we'll use a different approach
      });

      // Since EventSource doesn't support POST, we'll use fetch with streaming
      const response = await fetch("http://localhost:8000/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: inputValue,
          conversation_history: messages.slice(-10).map((msg) => ({
            content: msg.content,
            sender: msg.sender,
            timestamp: msg.timestamp.toISOString(),
          })),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get streaming response");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.substring(6));

                if (data.type === "progress") {
                  setCurrentProgress(data.data);
                } else if (data.type === "step") {
                  setCurrentSteps((prev) => [...prev, data]);
                } else if (data.type === "metrics") {
                  setCurrentMetrics(data.data);
                } else if (data.type === "complete") {
                  const agentResponse: Message = {
                    id: (Date.now() + 1).toString(),
                    content: data.response.response,
                    sender: "agent",
                    timestamp: new Date(),
                    progress: currentProgress || undefined,
                    steps: currentSteps.length > 0 ? currentSteps : undefined,
                    metrics: currentMetrics || undefined,
                  };
                  setMessages((prev) => [...prev, agentResponse]);
                  setCurrentProgress(null);
                  setCurrentSteps([]);
                  setCurrentMetrics(null);
                } else if (data.type === "error") {
                  throw new Error(data.message);
                }
              } catch (e) {
                console.error("Error parsing SSE data:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);

      // Fallback to regular POST request
      try {
        const response = await fetch("http://localhost:8000/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: inputValue,
            conversation_history: messages.slice(-10).map((msg) => ({
              content: msg.content,
              sender: msg.sender,
              timestamp: msg.timestamp.toISOString(),
            })),
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to get response from backend");
        }

        const data = await response.json();

        const agentResponse: Message = {
          id: (Date.now() + 1).toString(),
          content: data.response,
          sender: "agent",
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, agentResponse]);
      } catch (fallbackError) {
        console.error("Fallback also failed:", fallbackError);

        const fallbackResponse: Message = {
          id: (Date.now() + 1).toString(),
          content:
            "I'm having trouble connecting to the backend. Please make sure the server is running on http://localhost:8000",
          sender: "agent",
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, fallbackResponse]);
      }
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground">
      <div className="flex-1 flex flex-col max-w-4xl mx-auto">
        {/* Header */}
        <div className="border-b border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-medium">Simple Knowledge Manager</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Organize your thoughts and ideas into connected notes
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => setShowKnowledgeGraph(true)}
              className="flex items-center gap-2"
            >
              <Network className="w-4 h-4" />
              Knowledge Graph
            </Button>
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-6">
          <div className="space-y-6">
            {messages.map((message) => (
              <div key={message.id} className="space-y-3">
                <div
                  className={`flex gap-3 ${
                    message.sender === "user" ? "flex-row-reverse" : "flex-row"
                  }`}
                >
                  <div
                    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      message.sender === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {message.sender === "user" ? (
                      <User size={16} />
                    ) : (
                      <Bot size={16} />
                    )}
                  </div>

                  <div
                    className={`max-w-lg ${
                      message.sender === "user" ? "text-right" : "text-left"
                    }`}
                  >
                    <div
                      className={`rounded-2xl px-4 py-3 ${
                        message.sender === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-foreground"
                      }`}
                    >
                      <p className="text-sm leading-relaxed">
                        {message.content}
                      </p>
                    </div>

                    <p className="text-xs text-muted-foreground mt-1 px-1">
                      {message.timestamp.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>

                {/* Show progress, steps, and metrics for agent messages */}
                {message.sender === "agent" && (
                  <div className="ml-11 space-y-2">
                    {message.progress && (
                      <ProgressIndicator progress={message.progress} />
                    )}
                    {message.metrics && (
                      <MetricsPanel metrics={message.metrics} />
                    )}
                    {message.steps && message.steps.length > 0 && (
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium">
                            Processing Steps
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            {message.steps.slice(-5).map((step, index) => (
                              <div
                                key={index}
                                className="text-xs border-l-2 border-muted pl-2"
                              >
                                <div className="font-medium">
                                  {step.summary}
                                </div>
                                <div className="text-muted-foreground">
                                  {step.action}
                                </div>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                )}
              </div>
            ))}

            {/* Live progress indicators */}
            {isStreaming && (
              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                    <Bot size={16} className="text-muted-foreground" />
                  </div>
                  <div className="flex-1">
                    {currentProgress && (
                      <ProgressIndicator progress={currentProgress} />
                    )}
                    {currentMetrics && (
                      <MetricsPanel metrics={currentMetrics} />
                    )}

                    {!currentProgress && (
                      <div className="bg-muted rounded-2xl px-4 py-3">
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-pulse" />
                          <div
                            className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-pulse"
                            style={{ animationDelay: "0.2s" }}
                          />
                          <div
                            className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-pulse"
                            style={{ animationDelay: "0.4s" }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input */}
        <div className="border-t border-border p-6">
          <div className="flex gap-3">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type anything - thoughts, links, research..."
              className="flex-1 h-12 bg-muted border-0 text-base"
              disabled={isStreaming}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isStreaming}
              size="lg"
              className="h-12 px-6"
            >
              <Send size={16} />
            </Button>
          </div>
        </div>
      </div>

      {/* Knowledge Graph Dialog */}
      <KnowledgeGraphViewer
        isOpen={showKnowledgeGraph}
        onClose={() => setShowKnowledgeGraph(false)}
      />
    </div>
  );
}
