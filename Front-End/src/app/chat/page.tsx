'use client';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { fetchWithAuth } from '@/lib/api';
import Link from 'next/link';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{source: string, page: string | number}>;
  route_name?: string;
  confidence?: number;
  warnings?: string[];
  isError?: boolean;
};

export default function ChatPage() {
  const { user, token, logout } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState<any[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const loadSessions = async () => {
    try {
      const res = await fetchWithAuth('/chat/sessions');
      setSessions(res);
    } catch (err) {
      console.error("Failed to load sessions", err);
    }
  };

  useEffect(() => {
    if (!token) {
       router.push('/');
    } else {
       loadSessions();
    }
  }, [token, router]);

  const loadSessionDetails = async (sessionId: string) => {
    try {
      setLoading(true);
      const res = await fetchWithAuth(`/chat/sessions/${sessionId}`);
      const mappedMessages = res.messages.map((m: any) => ({
        role: m.role,
        content: m.content,
        citations: m.citations,
        route_name: m.route_name,
        warnings: m.warnings,
        isError: false
      }));
      setMessages(mappedMessages);
      setActiveSessionId(sessionId);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this chat?")) return;
    try {
      await fetchWithAuth(`/chat/sessions/${sessionId}`, { method: 'DELETE' });
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
      loadSessions();
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
     if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
     }
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage = query.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setQuery('');
    setLoading(true);

    try {
      const res = await fetchWithAuth('/chat/query', {
        method: 'POST',
        body: JSON.stringify({ query: userMessage, session_id: activeSessionId })
      });
      
      if (!activeSessionId && res.session_id) {
         setActiveSessionId(res.session_id);
         loadSessions();
      }
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: res.answer,
        citations: res.source_documents,
        route_name: res.route_name,
        confidence: res.confidence,
        warnings: res.guardrail_warnings,
        isError: res.answer.includes("blocked by security") || res.answer.includes("Unauthorized")
      }]);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: err.message || 'System error. Please try again.', isError: true }]);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="layout-container">
      <div className="sidebar">
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem', color: 'var(--accent-color)' }}>FinBot AI</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
             <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--accent-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                {user.username.charAt(0).toUpperCase()}
             </div>
             <div>
                <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>@{user.username}</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', textTransform: 'capitalize' }}>{user.role.replace('_', ' ')}</div>
             </div>
          </div>
          {user.role === 'c_level' && (
              <div style={{ marginTop: '0.75rem' }}>
                  <Link href="/admin" style={{ color: 'var(--warning-color)', textDecoration: 'none', fontSize: '0.85rem' }}>
                      ⚙️ Access Admin Panel
                  </Link>
              </div>
          )}
        </div>
        <div style={{ padding: '1.5rem', flex: 1, overflowY: 'auto' }}>
          <button 
             onClick={() => { setActiveSessionId(null); setMessages([]); setQuery(''); }} 
             disabled={loading}
             style={{ width: '100%', padding: '0.75rem', background: 'var(--accent-color)', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', marginBottom: '1.5rem' }}
          >
             + New Chat
          </button>
          
          <h3 style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>Recent Chats</h3>
          {sessions.length === 0 ? (
             <div style={{ marginTop: '1rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>No recent chats.</div>
          ) : (
             <ul style={{ listStyle: 'none', padding: 0, marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                {sessions.map(s => (
                   <li key={s.id} onClick={() => loadSessionDetails(s.id)} style={{ padding: '0.75rem 0.5rem', background: activeSessionId === s.id ? 'var(--panel-bg)' : 'transparent', borderRadius: '6px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: activeSessionId === s.id ? '1px solid var(--border-color)' : '1px solid transparent' }}>
                      <div style={{ fontSize: '0.9rem', color: activeSessionId === s.id ? 'var(--accent-color)' : 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '80%' }}>
                         {s.title}
                      </div>
                      <button onClick={(e) => handleDeleteSession(e, s.id)} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', opacity: 0.6 }} title="Delete Chat">✖</button>
                   </li>
                ))}
             </ul>
          )}
        </div>
        <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
          <button onClick={() => { logout(); router.push('/') }} style={{ width: '100%', padding: '0.75rem', background: 'var(--bg-color)', color: 'var(--text-secondary)', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
            Sign Out
          </button>
        </div>
      </div>

      <div className="main-content">
        <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: '2rem 15%', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {messages.length === 0 && (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ fontSize: '3rem' }}>🏦</div>
              <h2>How can I help you today?</h2>
              <p>Ask a question about {user.collections.join(', ')}</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <div style={{ 
                maxWidth: '85%', 
                background: m.role === 'user' ? 'var(--accent-color)' : 'var(--panel-bg)',
                padding: '1.5rem',
                borderRadius: '8px',
                border: m.role === 'user' ? 'none' : '1px solid var(--border-color)'
              }}>
                {m.role === 'assistant' && m.warnings && m.warnings.length > 0 && (
                  <div style={{ marginBottom: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {m.warnings.map((w, wi) => (
                      <div key={wi} style={{ padding: '0.75rem', background: 'var(--warning-bg)', borderLeft: '3px solid var(--warning-color)', color: 'var(--warning-color)', fontSize: '0.85rem', borderRadius: '0 4px 4px 0' }}>
                        {w}
                      </div>
                    ))}
                  </div>
                )}
                
                {m.role === 'assistant' && m.route_name && (
                   <div style={{ marginBottom: '1.25rem' }}>
                     <span style={{ fontSize: '0.75rem', padding: '0.3rem 0.8rem', background: 'var(--bg-color)', border: '1px solid var(--border-color)', borderRadius: '16px', color: 'var(--text-secondary)' }}>
                       ⚡ {m.route_name.replace('_', ' ').toUpperCase()} ({(m.confidence! * 100).toFixed(1)}%)
                     </span>
                   </div>
                )}

                <div style={{ lineHeight: '1.6', color: m.isError ? 'var(--danger-color)' : 'var(--text-primary)', whiteSpace: 'pre-wrap', fontSize: '0.95rem' }}>
                  {m.content}
                </div>

                {m.role === 'assistant' && m.citations && m.citations.length > 0 && (
                  <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                    <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Citations</h4>
                    <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                      {m.citations.map((c, ci) => (
                        <li key={ci}>{c.source} {c.page ? `(Page: ${c.page})` : ''}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div style={{ padding: '1.5rem 15%', background: 'var(--bg-color)', borderTop: '1px solid var(--border-color)' }}>
          <form onSubmit={handleSend} style={{ display: 'flex', gap: '1rem' }}>
            <input 
              type="text" 
              value={query} 
              onChange={e => setQuery(e.target.value)} 
              placeholder="Message FinBot..." 
              style={{ flex: 1, padding: '1rem', background: 'var(--panel-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)', outline: 'none', fontSize: '0.95rem' }}
              disabled={loading}
              autoFocus
            />
            <button type="submit" className="btn-primary" disabled={loading} style={{ padding: '0 2rem' }}>
              {loading ? '...' : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
