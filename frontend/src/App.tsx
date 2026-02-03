import { useState } from 'react'
import { ChatPanel } from './ChatPanel'
import './App.css'

function App() {
  const [chatOpen, setChatOpen] = useState(false)
  const [chatFullscreen, setChatFullscreen] = useState(false)
  const [isClosing, setIsClosing] = useState(false)

  const toggleChat = () => setChatOpen((prev) => !prev)
  const closeChat = () => {
    if (isClosing) return
    setIsClosing(true)
  }
  const handlePopupAnimationEnd = () => {
    if (isClosing) {
      setChatOpen(false)
      setIsClosing(false)
    }
  }
  const toggleFullscreen = () => setChatFullscreen((prev) => !prev)

  return (
    <div className="app">
      <main className="app-main">
        <div className="app-hero">
          <h1 className="app-hero-title">Appointment Scheduling</h1>
          <p className="app-hero-subtitle">
            Book appointments, check availability, and get help from our assistant.
          </p>
          <p className="app-hero-hint">
            Click the assistant icon on the right to start a conversation.
          </p>
        </div>
      </main>

      {/* Close FAB: bottom-right viewport, circle, blue; white X only when chat open, soft blue glow */}
      <button
        type="button"
        className={`chat-fab ${chatOpen ? 'chat-fab--close' : ''} ${isClosing ? 'chat-fab--hidden' : ''}`}
        onClick={chatOpen ? closeChat : toggleChat}
        aria-label={chatOpen ? 'Close chat' : 'Open chat'}
        title={chatOpen ? 'Close' : 'Open chat'}
      >
        {chatOpen ? (
          <span className="chat-fab-icon" aria-hidden>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.75" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </span>
        ) : (
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        )}
      </button>

      {/* Chat popup - right side */}
      {chatOpen && (
        <div className={`chat-popup-wrapper ${isClosing ? 'chat-popup-wrapper--closing' : ''}`}>
          <div className="chat-popup-backdrop" onClick={closeChat} aria-hidden="true" />
          <div
            className={`chat-popup ${isClosing ? 'chat-popup--closing' : ''}`}
            onAnimationEnd={handlePopupAnimationEnd}
          >
            <ChatPanel
              isFullscreen={chatFullscreen}
              onToggleFullscreen={toggleFullscreen}
              onClose={closeChat}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default App
