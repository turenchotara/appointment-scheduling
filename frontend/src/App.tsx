import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

// API configuration - easy to change in one place
const API_ENDPOINT = '/chat'

function generateSessionId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<string>(() => generateSessionId())
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-focus message box when response arrives
  useEffect(() => {
    if (!isLoading && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isLoading])

  const handleReloadSession = () => {
    setSessionId(generateSessionId())
    setMessages([])
  }

  const handleDownloadHistory = () => {
    if (messages.length === 0) {
      alert('No chat history to download.')
      return
    }

    // Create a formatted chat history
    const chatHistory = {
      sessionId,
      exportedAt: new Date().toISOString(),
      messageCount: messages.length,
      messages: messages.map((msg, index) => ({
        index: index + 1,
        role: msg.role,
        content: msg.content,
        timestamp: new Date().toISOString(), // Approximate timestamp
      })),
    }

    // Create text format
    const textFormat = `Chat History Export
Session ID: ${sessionId}
Exported: ${new Date().toLocaleString()}
Total Messages: ${messages.length}

${'='.repeat(60)}

${messages
  .map(
    (msg, index) =>
      `[${index + 1}] ${msg.role.toUpperCase()}\n${msg.content}\n${'-'.repeat(60)}`
  )
  .join('\n\n')}
`

    // Create JSON format
    const jsonFormat = JSON.stringify(chatHistory, null, 2)

    // Create and download JSON file
    const jsonBlob = new Blob([jsonFormat], { type: 'application/json' })
    const jsonUrl = URL.createObjectURL(jsonBlob)
    const jsonLink = document.createElement('a')
    jsonLink.href = jsonUrl
    jsonLink.download = `chat-history-${sessionId}-${Date.now()}.json`
    document.body.appendChild(jsonLink)
    jsonLink.click()
    document.body.removeChild(jsonLink)
    URL.revokeObjectURL(jsonUrl)

    // Create and download text file
    const textBlob = new Blob([textFormat], { type: 'text/plain' })
    const textUrl = URL.createObjectURL(textBlob)
    const textLink = document.createElement('a')
    textLink.href = textUrl
    textLink.download = `chat-history-${sessionId}-${Date.now()}.txt`
    document.body.appendChild(textLink)
    textLink.click()
    document.body.removeChild(textLink)
    URL.revokeObjectURL(textUrl)
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)

    try {
      // Build query parameters
      const params = new URLSearchParams({
        user_query: userMessage,
        session_id: sessionId,
      })
      
      const response = await fetch(`${API_ENDPOINT}?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Backend returns { result: { msg: "...", reason: "..." } } or { result: "..." }
      let assistantMessage = 'No response received'
      
      if (data.result) {
        // Check if result is an object with msg/reason properties
        if (typeof data.result === 'object' && data.result !== null) {
          assistantMessage = data.result.msg || data.result.reason || data.result.message || JSON.stringify(data.result)
        } else if (typeof data.result === 'string') {
          assistantMessage = data.result
        }
      } else if (data.message) {
        assistantMessage = typeof data.message === 'string' ? data.message : JSON.stringify(data.message)
      } else if (data.response) {
        assistantMessage = typeof data.response === 'string' ? data.response : JSON.stringify(data.response)
      }
      
      // Ensure we always have a string for ReactMarkdown
      if (typeof assistantMessage !== 'string') {
        assistantMessage = String(assistantMessage)
      }
      
      // Hide loading indicator and add message
      setIsLoading(false)
      setMessages((prev) => [...prev, { role: 'assistant', content: assistantMessage }])
    } catch (error) {
      console.error('Error sending message:', error)
      // Hide loading indicator and add error message
      setIsLoading(false)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        },
      ])
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <h1>Chat Assistant</h1>
          <div className="header-buttons">
            <button
              onClick={handleDownloadHistory}
              className="download-button"
              disabled={messages.length === 0}
              title="Download chat history"
            >
              Download History
            </button>
            <button onClick={handleReloadSession} className="reload-button">
              Reload Session
            </button>
          </div>
        </div>

        <div className="messages-container">
          {messages.length === 0 && (
            <div className="empty-state">
              <p>Start a conversation by typing a message below.</p>
            </div>
          )}
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-content">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message assistant loading-message">
              <div className="message-content">
                <div className="loading-indicator">Thinking...</div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
            rows={3}
            disabled={isLoading}
            className="message-input"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="send-button"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default App

