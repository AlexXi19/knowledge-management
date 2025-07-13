import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Send, User, Bot, Network, MessageSquare } from "lucide-react";
import KnowledgeGraph from "./components/KnowledgeGraph";

interface Message {
  id: string;
  content: string;
  sender: "user" | "agent";
  timestamp: Date;
}

const SAMPLE_MESSAGES: Message[] = [
  {
    id: "1",
    content:
      "Hi! I'm your knowledge management agent. Share thoughts, paste links, or add research - I'll organize everything for you.",
    sender: "agent",
    timestamp: new Date(Date.now() - 3600000),
  },
  {
    id: "2",
    content: "Creating your own future vs. waiting for it to happen",
    sender: "user",
    timestamp: new Date(Date.now() - 1800000),
  },
  {
    id: "3",
    content:
      'Added to "Ideas to Develop" and "Personal". This is a great reflection on agency vs. passivity. Want to explore this further?',
    sender: "agent",
    timestamp: new Date(Date.now() - 1790000),
  },
];

function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>(SAMPLE_MESSAGES);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
    setIsTyping(true);

    try {
      // Send message to backend
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
    } catch (error) {
      console.error("Error sending message:", error);

      // Fallback to mock response
      const fallbackResponse: Message = {
        id: (Date.now() + 1).toString(),
        content:
          "I'm having trouble connecting to the backend. Please make sure the server is running on http://localhost:8000",
        sender: "agent",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, fallbackResponse]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <ScrollArea className="flex-1 p-6">
        <div className="space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
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
                  <p className="text-sm leading-relaxed">{message.content}</p>
                </div>

                <p className="text-xs text-muted-foreground mt-1 px-1">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                <Bot size={16} className="text-muted-foreground" />
              </div>
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
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim()}
            size="lg"
            className="h-12 px-6"
          >
            <Send size={16} />
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function KnowledgeManager() {
  return (
    <div className="flex h-screen bg-background text-foreground">
      <div className="flex-1 flex flex-col max-w-6xl mx-auto">
        {/* Header */}
        <div className="border-b border-border p-6">
          <h1 className="text-xl font-medium">Knowledge Manager</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Chat with your AI agent or visualize your knowledge graph
          </p>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="chat" className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-2 mx-6 mt-4">
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare size={16} />
              Chat
            </TabsTrigger>
            <TabsTrigger value="graph" className="flex items-center gap-2">
              <Network size={16} />
              Knowledge Graph
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chat" className="flex-1 mt-0">
            <ChatInterface />
          </TabsContent>

          <TabsContent value="graph" className="flex-1 mt-0 p-6">
            <KnowledgeGraph />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
