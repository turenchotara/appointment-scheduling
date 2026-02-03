import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import ReactMarkdown from 'react-markdown'
import './ChatPanel.css'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: number
}

const API_ENDPOINT = '/chat'

/** Set to true to show the attachment button in the input bar; false to hide it. */
const SHOW_ATTACHMENT_BUTTON = false

const ASSISTANT_NAME = 'Clinic AI'

const INITIAL_MESSAGE: Message = {
  role: 'assistant',
  content: `Hello! I'm your ${ASSISTANT_NAME} assistant. You can ask me to check availability, book appointments, or get help with anything else. How can I help you today?`,
}

function formatMessageTime(ts?: number): string {
  if (ts == null) return ''
  const d = new Date(ts)
  const today = new Date()
  const isToday = d.getDate() === today.getDate() && d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear()
  const time = d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
  return isToday ? `Today, ${time}` : d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })
}

function generateSessionId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

interface ChatPanelProps {
  isFullscreen: boolean
  onToggleFullscreen: () => void
  onClose: () => void
}

export function ChatPanel({ isFullscreen, onToggleFullscreen, onClose }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>(() => [{ ...INITIAL_MESSAGE, timestamp: Date.now() }])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<string>(() => generateSessionId())
  const [isLoading, setIsLoading] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!isLoading && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isLoading])

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    if (menuOpen) document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [menuOpen])

  const handleReloadSession = () => {
    setSessionId(generateSessionId())
    setMessages([{ ...INITIAL_MESSAGE, timestamp: Date.now() }])
    setMenuOpen(false)
  }

  const handleDownloadHistory = () => {
    if (messages.length <= 1) {
      alert('No chat history to download.')
      setMenuOpen(false)
      return
    }
    const chatHistory = {
      sessionId,
      exportedAt: new Date().toISOString(),
      messageCount: messages.length,
      messages: messages.map((msg, index) => ({
        index: index + 1,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp ? new Date(msg.timestamp).toISOString() : new Date().toISOString(),
      })),
    }
    const textFormat = `Chat History Export\nSession ID: ${sessionId}\nExported: ${new Date().toLocaleString()}\nTotal Messages: ${messages.length}\n\n${messages.map((msg, i) => `[${i + 1}] ${msg.role.toUpperCase()}\n${msg.content}`).join('\n\n')}`
    const jsonFormat = JSON.stringify(chatHistory, null, 2)
    const jsonBlob = new Blob([jsonFormat], { type: 'application/json' })
    const jsonUrl = URL.createObjectURL(jsonBlob)
    const a = document.createElement('a')
    a.href = jsonUrl
    a.download = `chat-history-${sessionId}-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(jsonUrl)
    const textBlob = new Blob([textFormat], { type: 'text/plain' })
    const textUrl = URL.createObjectURL(textBlob)
    const a2 = document.createElement('a')
    a2.href = textUrl
    a2.download = `chat-history-${sessionId}-${Date.now()}.txt`
    document.body.appendChild(a2)
    a2.click()
    document.body.removeChild(a2)
    URL.revokeObjectURL(textUrl)
    setMenuOpen(false)
  }

  const getFriendlyErrorMessage = (status: number): string => {
    if (status >= 500) return "Something went wrong on our end. Please try again in a moment."
    if (status === 404) return "The chat service isn't available right now. Please try again later."
    if (status === 403) return "Unable to complete your request. Please try again."
    if (status >= 400) return "Your message couldn't be sent. Please check and try again."
    return "Something went wrong. Please try again."
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return
    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage, timestamp: Date.now() }])
    setIsLoading(true)
    try {
      const params = new URLSearchParams({ user_query: userMessage, session_id: sessionId })
      const response = await fetch(`${API_ENDPOINT}?${params.toString()}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!response.ok) {
        setIsLoading(false)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: getFriendlyErrorMessage(response.status), timestamp: Date.now() },
      ])
        return
      }
      const data = await response.json()
      let assistantMessage = 'No response received'
      if (data.result) {
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
      if (typeof assistantMessage !== 'string') assistantMessage = String(assistantMessage)
      setIsLoading(false)
      setMessages((prev) => [...prev, { role: 'assistant', content: assistantMessage, timestamp: Date.now() }])
    } catch {
      console.error('Error sending message')
      setIsLoading(false)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: "We couldn't send your message. Please check your connection and try again.", timestamp: Date.now() },
      ])
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const panelContent = (
    <div className={`chat-widget-panel ${isFullscreen ? 'chat-widget-panel--fullscreen' : ''}`}>
      <header className="chat-widget-header">
        <div className="chat-widget-header-left">
          <div className="chat-widget-header-logo" aria-hidden>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M2 12h20" />
              <circle cx="12" cy="12" r="4" />
            </svg>
          </div>
          <span className="chat-widget-header-title">{ASSISTANT_NAME}</span>
        </div>
        <div className="chat-widget-header-actions">
          <button
            type="button"
            onClick={onToggleFullscreen}
            className="chat-widget-header-action"
            title={isFullscreen ? 'Exit full screen' : 'Maximize'}
            aria-label={isFullscreen ? 'Exit full screen' : 'Maximize'}
          >
            {isFullscreen ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
              </svg>
            )}
          </button>
          <div className="chat-widget-menu" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen((o) => !o)}
              className="chat-widget-header-action"
              title="More options"
              aria-label="More options"
              aria-expanded={menuOpen}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="5" r="1.5" />
                <circle cx="12" cy="12" r="1.5" />
                <circle cx="12" cy="19" r="1.5" />
              </svg>
            </button>
            {menuOpen && (
              <div className="chat-widget-menu-dropdown">
                <button type="button" onClick={handleDownloadHistory}>
                  Download history
                </button>
                <button type="button" onClick={handleReloadSession}>
                  Reload
                </button>
              </div>
            )}
          </div>
          {isFullscreen}
        </div>
      </header>

      <div className="chat-widget-messages">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`chat-widget-bubble chat-widget-bubble--${msg.role}`}
            title={formatMessageTime(msg.timestamp)}
          >
            <div className="chat-widget-bubble-content">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="chat-widget-bubble chat-widget-bubble--assistant chat-widget-bubble--loading">
            <div className="chat-widget-bubble-content">Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-widget-input-bar">
        <div className="chat-widget-input-wrap">
          {SHOW_ATTACHMENT_BUTTON && (
            <button type="button" className="chat-widget-input-add" aria-label="Add attachment">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            </button>
          )}
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            rows={1}
            disabled={isLoading}
            className="chat-widget-input"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="chat-widget-input-send"
            aria-label="Send"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )

  return isFullscreen ? createPortal(panelContent, document.body) : panelContent
}
