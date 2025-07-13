import React, { useState, useEffect, useCallback } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Node,
  Edge,
  Connection,
  BackgroundVariant,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  RefreshCw,
  FileText,
  Calendar,
  Tag,
  GitBranch,
  Link,
  Eye,
  EyeOff,
  Zap,
  Search,
} from "lucide-react";
import { Input } from "@/components/ui/input";

interface GraphNode {
  id: string;
  content: string;
  category: string;
  metadata: {
    title?: string;
    tags?: string[];
    created_at?: string;
    updated_at?: string;
    file_path?: string;
    content_hash?: string;
    parent_id?: string;
    children_ids?: string[];
  };
}

interface GraphEdge {
  source: string;
  target: string;
  weight?: number;
  relation_type?: string;
  metadata?: {
    type?: string;
    display?: string;
    line_number?: number;
    context?: string;
  };
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: {
    total_nodes: number;
    total_edges: number;
    categories: string[];
    tags: string[];
  };
}

interface SelectedNode {
  id: string;
  title: string;
  content: string;
  category: string;
  metadata: GraphNode["metadata"];
  backlinks: any[];
  outgoingLinks: any[];
}

// Enhanced category colors with better contrast
const getCategoryColor = (category: string): string => {
  const colors: Record<string, string> = {
    "Ideas to Develop": "#ff6b6b",
    Personal: "#4ecdc4",
    Research: "#45b7d1",
    "Reading List": "#96ceb4",
    Projects: "#ffc107",
    Learning: "#9b59b6",
    "Quick Notes": "#95a5a6",
    Technical: "#e74c3c",
    Business: "#f39c12",
  };
  return colors[category] || "#6c757d";
};

// Relationship type colors and styles
const getRelationshipStyle = (relationType: string) => {
  const styles: Record<string, any> = {
    parent_of: {
      stroke: "#2563eb",
      strokeWidth: 3,
      strokeDasharray: "5,5",
      markerEnd: { type: MarkerType.ArrowClosed, color: "#2563eb" },
    },
    child_of: {
      stroke: "#7c3aed",
      strokeWidth: 2,
      markerEnd: { type: MarkerType.ArrowClosed, color: "#7c3aed" },
    },
    supports: {
      stroke: "#059669",
      strokeWidth: 2,
      markerEnd: { type: MarkerType.ArrowClosed, color: "#059669" },
    },
    contradicts: {
      stroke: "#dc2626",
      strokeWidth: 2,
      strokeDasharray: "3,3",
      markerEnd: { type: MarkerType.ArrowClosed, color: "#dc2626" },
    },
    references: {
      stroke: "#6b7280",
      strokeWidth: 1,
      markerEnd: { type: MarkerType.Arrow, color: "#6b7280" },
    },
    depends_on: {
      stroke: "#ea580c",
      strokeWidth: 2,
      markerEnd: { type: MarkerType.ArrowClosed, color: "#ea580c" },
    },
    wiki_link: {
      stroke: "#8b5cf6",
      strokeWidth: 1,
      markerEnd: { type: MarkerType.Arrow, color: "#8b5cf6" },
    },
    related_to: {
      stroke: "#64748b",
      strokeWidth: 1,
      markerEnd: { type: MarkerType.Arrow, color: "#64748b" },
    },
  };

  return (
    styles[relationType] || {
      stroke: "#999",
      strokeWidth: 1,
      markerEnd: { type: MarkerType.Arrow, color: "#999" },
    }
  );
};

const createReactFlowElements = (
  graphData: GraphData,
  showHierarchy: boolean = true,
  relationshipFilter: string[] = []
) => {
  let nodes: Node[] = [];
  let edges: Edge[] = [];

  if (showHierarchy) {
    // Hierarchical layout
    nodes = createHierarchicalNodes(graphData);
  } else {
    // Circular layout
    nodes = createCircularNodes(graphData);
  }

  // Filter and create edges
  edges = graphData.edges
    .filter(
      (edge) =>
        relationshipFilter.length === 0 ||
        relationshipFilter.includes(edge.relation_type || "related_to")
    )
    .map((edge, index) => {
      const style = getRelationshipStyle(edge.relation_type || "related_to");
      return {
        id: `edge-${index}`,
        source: edge.source,
        target: edge.target,
        type: "smoothstep",
        style: style,
        animated: edge.relation_type === "wiki_link",
        label: edge.relation_type?.replace("_", " ") || "",
        labelStyle: { fontSize: "10px", fill: style.stroke },
        markerEnd: style.markerEnd,
        data: {
          relationType: edge.relation_type,
          metadata: edge.metadata,
        },
      };
    });

  return { nodes, edges };
};

const createHierarchicalNodes = (graphData: GraphData): Node[] => {
  const nodes: Node[] = [];
  const nodeMap = new Map<string, GraphNode>();

  // Create node map
  graphData.nodes.forEach((node) => {
    nodeMap.set(node.id, node);
  });

  // Find root nodes (nodes with no parent)
  const rootNodes = graphData.nodes.filter(
    (node) => !node.metadata.parent_id || !nodeMap.has(node.metadata.parent_id)
  );

  // Build hierarchy recursively
  const buildHierarchy = (
    nodeId: string,
    x: number,
    y: number,
    level: number
  ) => {
    const node = nodeMap.get(nodeId);
    if (!node) return;

    nodes.push({
      id: node.id,
      type: "default",
      position: { x, y },
      data: {
        label: node.metadata.title || node.content.substring(0, 50) + "...",
        category: node.category,
        originalNode: node,
        level: level,
      },
      style: {
        background: getCategoryColor(node.category),
        color: "white",
        border: level === 0 ? "3px solid #1f2937" : "2px solid #374151",
        borderRadius: "8px",
        padding: "12px",
        fontSize: level === 0 ? "14px" : "12px",
        fontWeight: level === 0 ? "bold" : "normal",
        textAlign: "center",
        width: level === 0 ? 220 : 180,
        height: level === 0 ? 100 : 80,
        boxShadow:
          level === 0
            ? "0 4px 6px rgba(0, 0, 0, 0.1)"
            : "0 2px 4px rgba(0, 0, 0, 0.1)",
      },
    });

    // Add children
    const children = node.metadata.children_ids || [];
    const childSpacing = 300;
    const startX = x - ((children.length - 1) * childSpacing) / 2;

    children.forEach((childId, index) => {
      buildHierarchy(
        childId,
        startX + index * childSpacing,
        y + 150,
        level + 1
      );
    });
  };

  // Layout root nodes
  const rootSpacing = 400;
  const startX = 400 - ((rootNodes.length - 1) * rootSpacing) / 2;

  rootNodes.forEach((rootNode, index) => {
    buildHierarchy(rootNode.id, startX + index * rootSpacing, 100, 0);
  });

  return nodes;
};

const createCircularNodes = (graphData: GraphData): Node[] => {
  return graphData.nodes.map((node, index) => ({
    id: node.id,
    type: "default",
    position: {
      x: Math.cos((index * 2 * Math.PI) / graphData.nodes.length) * 350 + 500,
      y: Math.sin((index * 2 * Math.PI) / graphData.nodes.length) * 350 + 400,
    },
    data: {
      label: node.metadata.title || node.content.substring(0, 50) + "...",
      category: node.category,
      originalNode: node,
    },
    style: {
      background: getCategoryColor(node.category),
      color: "white",
      border: "2px solid #222",
      borderRadius: "8px",
      padding: "10px",
      fontSize: "12px",
      fontWeight: "bold",
      textAlign: "center",
      width: 180,
      height: 80,
    },
  }));
};

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [showHierarchy, setShowHierarchy] = useState(true);
  const [relationshipFilter, setRelationshipFilter] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const relationshipTypes = [
    "parent_of",
    "child_of",
    "supports",
    "contradicts",
    "references",
    "depends_on",
    "wiki_link",
    "related_to",
  ];

  const fetchGraphData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/knowledge/graph");
      if (!response.ok) {
        throw new Error("Failed to fetch knowledge graph");
      }

      const data = await response.json();
      setGraphData(data.graph || data);

      // Convert to ReactFlow format
      const { nodes: flowNodes, edges: flowEdges } = createReactFlowElements(
        data.graph || data,
        showHierarchy,
        relationshipFilter
      );
      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error occurred");
      console.error("Error fetching graph data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
  }, []);

  useEffect(() => {
    if (graphData) {
      const { nodes: flowNodes, edges: flowEdges } = createReactFlowElements(
        graphData,
        showHierarchy,
        relationshipFilter
      );
      setNodes(flowNodes);
      setEdges(flowEdges);
    }
  }, [showHierarchy, relationshipFilter, graphData]);

  const onConnect = useCallback(
    (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback(
    async (event: React.MouseEvent, node: Node) => {
      const originalNode = node.data.originalNode as GraphNode;

      try {
        // Fetch additional node details (backlinks, outgoing links)
        const [backlinksRes, outgoingRes] = await Promise.all([
          fetch(`http://localhost:8000/knowledge/backlinks/${node.id}`),
          fetch(`http://localhost:8000/knowledge/outgoing/${node.id}`),
        ]);

        const backlinks = backlinksRes.ok ? await backlinksRes.json() : [];
        const outgoingLinks = outgoingRes.ok ? await outgoingRes.json() : [];

        setSelectedNode({
          id: node.id,
          title: originalNode.metadata.title || "Untitled",
          content: originalNode.content,
          category: originalNode.category,
          metadata: originalNode.metadata,
          backlinks: backlinks.backlinks || [],
          outgoingLinks: outgoingLinks.outgoing_links || [],
        });
      } catch (error) {
        console.error("Error fetching node details:", error);
        setSelectedNode({
          id: node.id,
          title: originalNode.metadata.title || "Untitled",
          content: originalNode.content,
          category: originalNode.category,
          metadata: originalNode.metadata,
          backlinks: [],
          outgoingLinks: [],
        });
      }
    },
    []
  );

  const toggleRelationshipFilter = (relType: string) => {
    setRelationshipFilter((prev) =>
      prev.includes(relType)
        ? prev.filter((r) => r !== relType)
        : [...prev, relType]
    );
  };

  const filteredNodes = nodes.filter((node) => {
    if (!searchQuery) return true;
    const originalNode = node.data.originalNode as GraphNode;
    return (
      originalNode.metadata.title
        ?.toLowerCase()
        .includes(searchQuery.toLowerCase()) ||
      originalNode.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      originalNode.category.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  const formatDate = (dateString?: string) => {
    if (!dateString) return "Unknown";
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">
            Loading enhanced knowledge graph...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-red-500 mb-4">Error: {error}</p>
          <Button onClick={fetchGraphData} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <FileText className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground mb-4">
            No knowledge graph data available
          </p>
          <p className="text-sm text-muted-foreground mb-4">
            Start chatting with the AI agent to create notes and build your
            knowledge graph.
          </p>
          <Button onClick={fetchGraphData} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      {/* Controls Panel */}
      <div className="absolute top-4 left-4 right-4 z-10 flex gap-4">
        <div className="bg-background/80 backdrop-blur-sm p-4 rounded-lg border flex-1">
          <div className="flex items-center gap-4 mb-3">
            <h3 className="font-semibold">Enhanced Knowledge Graph</h3>
            <Button onClick={fetchGraphData} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>

          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{graphData.nodes.length} nodes</span>
            <span>{graphData.edges.length} connections</span>
            <span>{graphData.stats?.categories?.length || 0} categories</span>
          </div>
        </div>

        <div className="bg-background/80 backdrop-blur-sm p-4 rounded-lg border">
          <div className="flex items-center gap-2 mb-3">
            <GitBranch className="w-4 h-4" />
            <span className="font-semibold text-sm">Layout</span>
          </div>
          <div className="flex gap-2">
            <Button
              variant={showHierarchy ? "default" : "outline"}
              size="sm"
              onClick={() => setShowHierarchy(true)}
            >
              Hierarchy
            </Button>
            <Button
              variant={!showHierarchy ? "default" : "outline"}
              size="sm"
              onClick={() => setShowHierarchy(false)}
            >
              Circular
            </Button>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="absolute top-20 left-4 right-4 z-10">
        <div className="bg-background/80 backdrop-blur-sm p-3 rounded-lg border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      </div>

      {/* Relationship Filter */}
      <div className="absolute top-32 left-4 right-4 z-10">
        <div className="bg-background/80 backdrop-blur-sm p-3 rounded-lg border">
          <div className="flex items-center gap-2 mb-2">
            <Link className="w-4 h-4" />
            <span className="font-semibold text-sm">Relationship Types</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {relationshipTypes.map((relType) => (
              <Button
                key={relType}
                variant={
                  relationshipFilter.includes(relType) ? "default" : "outline"
                }
                size="sm"
                onClick={() => toggleRelationshipFilter(relType)}
                className="text-xs"
              >
                {relType.replace("_", " ")}
              </Button>
            ))}
          </div>
        </div>
      </div>

      <ReactFlow
        nodes={filteredNodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        className="mt-40"
      >
        <Controls />
        <MiniMap
          nodeColor={(node) => getCategoryColor(node.data.category)}
          nodeStrokeWidth={2}
        />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>

      {/* Enhanced Node Detail Modal */}
      <Dialog open={!!selectedNode} onOpenChange={() => setSelectedNode(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              {selectedNode?.title}
            </DialogTitle>
          </DialogHeader>

          {selectedNode && (
            <div className="flex-1 overflow-hidden">
              <Tabs defaultValue="content" className="h-full flex flex-col">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="content">Content</TabsTrigger>
                  <TabsTrigger value="metadata">Metadata</TabsTrigger>
                  <TabsTrigger value="backlinks">Backlinks</TabsTrigger>
                  <TabsTrigger value="outgoing">Outgoing Links</TabsTrigger>
                </TabsList>

                <TabsContent value="content" className="flex-1 overflow-hidden">
                  <div className="space-y-4 h-full">
                    <div className="flex flex-wrap gap-2">
                      <Badge
                        variant="secondary"
                        style={{
                          backgroundColor: getCategoryColor(
                            selectedNode.category
                          ),
                        }}
                      >
                        {selectedNode.category}
                      </Badge>

                      {selectedNode.metadata.tags?.map((tag) => (
                        <Badge key={tag} variant="outline">
                          <Tag className="w-3 h-3 mr-1" />
                          {tag}
                        </Badge>
                      ))}
                    </div>

                    <ScrollArea className="h-[400px] w-full border rounded-md p-4">
                      <div className="prose prose-sm max-w-none">
                        <p className="whitespace-pre-wrap">
                          {selectedNode.content}
                        </p>
                      </div>
                    </ScrollArea>
                  </div>
                </TabsContent>

                <TabsContent
                  value="metadata"
                  className="flex-1 overflow-hidden"
                >
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-semibold mb-2">Dates</h4>
                          <div className="space-y-2 text-sm">
                            {selectedNode.metadata.created_at && (
                              <div className="flex items-center gap-1">
                                <Calendar className="w-4 h-4" />
                                Created:{" "}
                                {formatDate(selectedNode.metadata.created_at)}
                              </div>
                            )}
                            {selectedNode.metadata.updated_at && (
                              <div className="flex items-center gap-1">
                                <Calendar className="w-4 h-4" />
                                Updated:{" "}
                                {formatDate(selectedNode.metadata.updated_at)}
                              </div>
                            )}
                          </div>
                        </div>

                        <div>
                          <h4 className="font-semibold mb-2">Hierarchy</h4>
                          <div className="space-y-2 text-sm">
                            {selectedNode.metadata.parent_id && (
                              <div>
                                Parent: {selectedNode.metadata.parent_id}
                              </div>
                            )}
                            {selectedNode.metadata.children_ids &&
                              selectedNode.metadata.children_ids.length > 0 && (
                                <div>
                                  Children:{" "}
                                  {selectedNode.metadata.children_ids.length}
                                </div>
                              )}
                          </div>
                        </div>
                      </div>

                      {selectedNode.metadata.file_path && (
                        <div>
                          <h4 className="font-semibold mb-2">File Path</h4>
                          <code className="text-xs bg-muted p-2 rounded block">
                            {selectedNode.metadata.file_path}
                          </code>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </TabsContent>

                <TabsContent
                  value="backlinks"
                  className="flex-1 overflow-hidden"
                >
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2">
                      {selectedNode.backlinks.length > 0 ? (
                        selectedNode.backlinks.map((link, index) => (
                          <div key={index} className="p-3 border rounded-lg">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium">{link.title}</span>
                              <Badge variant="outline" className="text-xs">
                                {link.relation_type?.replace("_", " ")}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {link.metadata?.context || "No context available"}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p className="text-muted-foreground">
                          No backlinks found
                        </p>
                      )}
                    </div>
                  </ScrollArea>
                </TabsContent>

                <TabsContent
                  value="outgoing"
                  className="flex-1 overflow-hidden"
                >
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2">
                      {selectedNode.outgoingLinks.length > 0 ? (
                        selectedNode.outgoingLinks.map((link, index) => (
                          <div key={index} className="p-3 border rounded-lg">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium">{link.title}</span>
                              <Badge variant="outline" className="text-xs">
                                {link.relation_type?.replace("_", " ")}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {link.metadata?.context || "No context available"}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p className="text-muted-foreground">
                          No outgoing links found
                        </p>
                      )}
                    </div>
                  </ScrollArea>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
