import Head from 'next/head';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import { Sidebar, API } from './index';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../../components/AuthContext';
import { Send, Bot, User, Loader, Mic, MicOff, FileText, History, Plus, Trash2, Sparkles } from 'lucide-react';

export default function ChatPage() {
    const router = useRouter();
    const { docId } = router.query;
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [documents, setDocuments] = useState([]);
    const [selectedDoc, setSelectedDoc] = useState('');
    const [recording, setRecording] = useState(false);
    const [conversationId, setConversationId] = useState(null);
    const [conversations, setConversations] = useState([]);
    const [showHistory, setShowHistory] = useState(false);
    const [followUps, setFollowUps] = useState([]);
    const { authFetch } = useAuth();
    const endRef = useRef(null);
    const recognitionRef = useRef(null);

    useEffect(() => {
        if (docId) setSelectedDoc(docId);
    }, [docId]);

    useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
    useEffect(() => {
        authFetch(`${API}/documents`).then(r => r.json()).then(setDocuments).catch(() => { });
        loadConversations();
    }, []);

    async function loadConversations() {
        try {
            const res = await authFetch(`${API}/conversations`);
            if (res.ok) setConversations(await res.json());
        } catch (e) { }
    }

    async function loadConversation(id) {
        try {
            const res = await authFetch(`${API}/conversations/${id}`);
            if (res.ok) {
                const data = await res.json();
                setConversationId(id);
                setSelectedDoc(data.document_id || '');
                setMessages(data.messages || []);
                setShowHistory(false);
                setFollowUps([]);
            }
        } catch (e) { }
    }

    async function deleteConversation(id) {
        try {
            await authFetch(`${API}/conversations/${id}`, { method: 'DELETE' });
            setConversations(prev => prev.filter(c => c.id !== id));
            if (conversationId === id) newChat();
        } catch (e) { }
    }

    function newChat() {
        setConversationId(null);
        setMessages([]);
        setShowHistory(false);
        setFollowUps([]);
    }

    // Voice setup
    useEffect(() => {
        if (typeof window !== 'undefined') {
            const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SR) {
                const r = new SR(); r.continuous = false; r.interimResults = false; r.lang = 'en-US';
                r.onresult = (e) => { setInput(e.results[0][0].transcript); setRecording(false); };
                r.onerror = () => setRecording(false);
                r.onend = () => setRecording(false);
                recognitionRef.current = r;
            }
        }
    }, []);

    function toggleVoice() {
        if (!recognitionRef.current) return;
        if (recording) { recognitionRef.current.stop(); setRecording(false); }
        else { recognitionRef.current.start(); setRecording(true); }
    }

    async function handleSend(customInput = null) {
        const q = (customInput || input).trim();
        if (!q || loading) return;
        if (!customInput) setInput('');
        setFollowUps([]); // Clear suggestions

        setMessages(p => [...p, { role: 'user', content: q }]);
        setLoading(true);

        try {
            // Append a placeholder assistant response
            setMessages(p => [...p, { role: 'assistant', content: '', sources: [], confidence: null }]);

            const res = await authFetch(`${API}/chat/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: q,
                    conversation_id: conversationId,
                    document_id: selectedDoc || null,
                }),
            });

            if (!res.ok) {
                setMessages(p => {
                    const next = [...p];
                    next[next.length - 1] = { role: 'assistant', content: '❌ Error getting answer from chat server.' };
                    return next;
                });
                setLoading(false);
                return;
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    const cleaned = line.trim();
                    if (cleaned.startsWith('data: ')) {
                        const dataStr = cleaned.slice(6);
                        try {
                            const chunk = JSON.parse(dataStr);
                            if (chunk.type === 'conversation_id') {
                                setConversationId(chunk.conversation_id);
                            } else if (chunk.type === 'token') {
                                setMessages(p => {
                                    const next = [...p];
                                    const last = next[next.length - 1];
                                    next[next.length - 1] = { ...last, content: last.content + chunk.content };
                                    return next;
                                });
                            } else if (chunk.type === 'sources') {
                                setMessages(p => {
                                    const next = [...p];
                                    const last = next[next.length - 1];
                                    next[next.length - 1] = { ...last, sources: chunk.sources };
                                    return next;
                                });
                            } else if (chunk.type === 'confidence') {
                                setMessages(p => {
                                    const next = [...p];
                                    const last = next[next.length - 1];
                                    next[next.length - 1] = { ...last, confidence: chunk.confidence };
                                    return next;
                                });
                            } else if (chunk.type === 'follow_ups') {
                                setFollowUps(chunk.follow_ups || []);
                            }
                        } catch (err) {
                            console.error('SSE JSON parse failed:', err);
                        }
                    }
                }
            }
            loadConversations(); // refresh conversations preview list
        } catch (err) {
            setMessages(p => {
                const next = [...p];
                next[next.length - 1] = { role: 'assistant', content: '❌ ' + err.message };
                return next;
            });
        } finally {
            setLoading(false);
        }
    }

    const confLevel = (s) => s >= 70 ? 'high' : s >= 40 ? 'medium' : 'low';
    const confColor = (s) => s >= 70 ? 'emerald' : s >= 40 ? 'orange' : 'rose';

    return (
        <>
            <Head><title>AI Chat — DocIntel AI</title></Head>
            <div className="app-layout">
                <Sidebar currentPath="/app/chat" />
                <main className="main-content" style={{ display: 'flex', flexDirection: 'column' }}>
                    <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', SystemItems: 'flex-start' }}>
                        <div>
                            <h2>💬 AI Chat</h2>
                            <p>Ask questions — type or speak • {conversationId ? '🟢 Conversation active' : '🆕 New conversation'}</p>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <button className="btn btn-secondary btn-sm" onClick={() => setShowHistory(!showHistory)}>
                                <History size={14} /> History ({conversations.length})
                            </button>
                            <button className="btn btn-primary btn-sm" onClick={newChat}>
                                <Plus size={14} /> New Chat
                            </button>
                        </div>
                    </div>

                    {/* Conversation history panel */}
                    {showHistory && (
                        <div className="card" style={{ marginBottom: '16px', maxHeight: '200px', overflowY: 'auto' }}>
                            {conversations.length === 0 ? (
                                <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>No conversations yet</p>
                            ) : conversations.map(c => (
                                <div key={c.id} style={{ display: 'flex', SystemItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderRadius: 'var(--radius-sm)', cursor: 'pointer', transition: 'all 0.15s', background: c.id === conversationId ? 'rgba(59,130,246,0.1)' : 'transparent' }}
                                    onClick={() => loadConversation(c.id)}
                                    onMouseEnter={e => { if (c.id !== conversationId) e.currentTarget.style.background = 'var(--bg-glass-hover)'; }}
                                    onMouseLeave={e => { if (c.id !== conversationId) e.currentTarget.style.background = 'transparent'; }}
                                >
                                    <div>
                                        <div style={{ fontSize: '14px', fontWeight: 500 }}>{c.title}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{c.message_count} messages</div>
                                    </div>
                                    <button className="btn btn-icon btn-sm" style={{ background: 'transparent', border: 'none' }}
                                        onClick={(e) => { e.stopPropagation(); deleteConversation(c.id); }}>
                                        <Trash2 size={14} style={{ color: 'var(--accent-rose)' }} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Document selector */}
                    {documents.length > 0 && (
                        <select className="input" style={{ maxWidth: 400, marginBottom: 16 }} value={selectedDoc} onChange={e => setSelectedDoc(e.target.value)}>
                            <option value="">All documents</option>
                            {documents.map(d => <option key={d.id} value={d.id}>📄 {d.original_name}</option>)}
                        </select>
                    )}

                    <div className="chat-container" style={{ flex: 1 }}>
                        <div className="chat-messages">
                            {!messages.length && (
                                <div className="empty-state">
                                    <div className="empty-state-icon">🤖</div>
                                    <h3>Ask me anything about your documents</h3>
                                    <p>Follow-up questions work too — I remember the conversation!</p>
                                </div>
                            )}
                            {messages.map((m, i) => (
                                <div key={i} className={`message ${m.role}`}>
                                    <div className="message-avatar">{m.role === 'assistant' ? <Bot size={16} /> : <User size={16} />}</div>
                                    <div>
                                        <div className="message-bubble markdown-body"><ReactMarkdown>{m.content}</ReactMarkdown></div>
                                        {m.confidence !== undefined && m.confidence > 0 && (
                                            <div className="confidence-meter">
                                                <span>Confidence:</span>
                                                <div className="confidence-bar"><div className={`confidence-fill ${confLevel(m.confidence)}`} style={{ width: `${m.confidence}%` }} /></div>
                                                <span style={{ color: `var(--accent-${confColor(m.confidence)})` }}>{m.confidence}%</span>
                                            </div>
                                        )}
                                        {m.sources?.length > 0 && (
                                            <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                                {m.sources.slice(0, 3).map((s, j) => (
                                                    <span key={j} style={{ fontSize: 11, padding: '2px 8px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-full)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                                                        <FileText size={10} style={{ verticalAlign: 'middle', marginRight: 3 }} />Chunk {s.chunk_index}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {loading && !messages[messages.length - 1]?.content && (
                                <div className="message assistant">
                                    <div className="message-avatar"><Bot size={16} /></div>
                                    <div className="message-bubble"><div className="spinner" /></div>
                                </div>
                            )}
                            
                            {/* Suggestion Chips UI */}
                            {followUps.length > 0 && (
                                <div className="follow-up-container" style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', SystemItems: 'center', gap: '6px' }}>
                                        <Sparkles size={14} style={{ color: 'var(--accent-purple)' }} /> Smart Follow-ups:
                                    </div>
                                    <div className="follow-ups-grid" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                        {followUps.map((q, idx) => (
                                            <button key={idx} className="btn btn-secondary btn-sm suggestion-chip" onClick={() => handleSend(q)} style={{ borderRadius: 'var(--radius-full)', background: 'var(--bg-glass)', border: '1px solid var(--border-color)', padding: '6px 14px', fontSize: '13px', transition: 'all 0.15s' }}>
                                                💡 {q}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div ref={endRef} />
                        </div>
                        <div className="chat-input-wrapper">
                            <button className={`btn btn-icon ${recording ? 'voice-btn recording' : 'btn-secondary voice-btn'}`} onClick={toggleVoice}>{recording ? <MicOff size={18} /> : <Mic size={18} />}</button>
                            <input className="input" placeholder={recording ? '🎙️ Listening...' : 'Ask about your documents...'} value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSend()} disabled={loading} />
                            <button className="btn btn-primary" onClick={() => handleSend()} disabled={loading || !input.trim()}><Send size={18} /></button>
                        </div>
                    </div>
                </main>
            </div>
        </>
    );
}
