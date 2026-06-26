import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader } from 'lucide-react';

export default function ChatInterface({ apiUrl, documentId }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const endRef = useRef(null);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    async function handleSend() {
        if (!input.trim() || loading) return;
        const q = input.trim();
        setInput('');
        setMessages((prev) => [...prev, { role: 'user', content: q }]);
        setLoading(true);

        try {
            const res = await fetch(`${apiUrl}/ask-question`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: q, document_id: documentId || null }),
            });
            if (res.ok) {
                const data = await res.json();
                setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }]);
            }
        } catch (err) {
            setMessages((prev) => [...prev, { role: 'assistant', content: '❌ Error: ' + err.message }]);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="chat-container">
            <div className="chat-messages">
                {messages.map((msg, i) => (
                    <div key={i} className={`message ${msg.role}`}>
                        <div className="message-avatar">
                            {msg.role === 'assistant' ? <Bot size={16} /> : <User size={16} />}
                        </div>
                        <div className="message-bubble">{msg.content}</div>
                    </div>
                ))}
                {loading && (
                    <div className="message assistant">
                        <div className="message-avatar"><Bot size={16} /></div>
                        <div className="message-bubble"><Loader size={16} className="spinner" /></div>
                    </div>
                )}
                <div ref={endRef} />
            </div>
            <div className="chat-input-wrapper">
                <input
                    className="input"
                    placeholder="Ask about this document..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    disabled={loading}
                />
                <button className="btn btn-primary" onClick={handleSend} disabled={loading || !input.trim()}>
                    <Send size={18} />
                </button>
            </div>
        </div>
    );
}
