import { useState, useEffect } from 'react';
import { FileText, Brain, Sparkles } from 'lucide-react';

export default function DocumentViewer({ documentId, apiUrl }) {
    const [doc, setDoc] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (documentId) fetchDocument();
    }, [documentId]);

    async function fetchDocument() {
        setLoading(true);
        try {
            const res = await fetch(`${apiUrl}/documents/${documentId}`);
            if (res.ok) setDoc(await res.json());
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    if (loading) return <div className="loading-bar" />;
    if (!doc) return <p style={{ color: 'var(--text-muted)' }}>Document not found</p>;

    return (
        <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '24px' }}>
                <div className={`doc-type-icon ${doc.file_type}`}>
                    <FileText size={20} />
                </div>
                <div>
                    <h3 style={{ fontSize: '18px', fontWeight: 700 }}>{doc.original_name}</h3>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        <span className={`tag tag-${doc.classification || 'other'}`}>{doc.classification || 'other'}</span>
                        <span style={{ marginLeft: '10px' }}>{doc.chunk_count} chunks</span>
                    </div>
                </div>
            </div>

            {doc.summary && (
                <div className="report-section">
                    <h3><Sparkles size={16} /> Summary</h3>
                    <pre>{doc.summary}</pre>
                </div>
            )}

            {doc.extracted_data && (
                <div className="report-section">
                    <h3><Brain size={16} /> Extracted Data</h3>
                    <pre>{JSON.stringify(doc.extracted_data, null, 2)}</pre>
                </div>
            )}

            {doc.text_content && (
                <div className="report-section">
                    <h3><FileText size={16} /> Text Preview</h3>
                    <pre>{doc.text_content}</pre>
                </div>
            )}
        </div>
    );
}
