import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X } from 'lucide-react';

export default function DocumentUploader({ onUpload, apiUrl }) {
    const [files, setFiles] = useState([]);

    const onDrop = useCallback((accepted) => {
        setFiles((prev) => [...prev, ...accepted]);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'image/*': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp'],
        },
        maxSize: 50 * 1024 * 1024,
    });

    function removeFile(index) {
        setFiles((prev) => prev.filter((_, i) => i !== index));
    }

    async function uploadAll() {
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            try {
                const res = await fetch(`${apiUrl}/upload-document`, {
                    method: 'POST',
                    body: formData,
                });
                if (res.ok && onUpload) {
                    onUpload(await res.json());
                }
            } catch (err) {
                console.error('Upload error:', err);
            }
        }
        setFiles([]);
    }

    return (
        <div>
            <div
                {...getRootProps()}
                className={`upload-zone ${isDragActive ? 'active' : ''}`}
                id="document-uploader"
            >
                <input {...getInputProps()} />
                <div className="upload-icon">
                    <Upload size={32} color="white" />
                </div>
                <h3>{isDragActive ? 'Drop files here!' : 'Drag & drop documents'}</h3>
                <p>or <span className="highlight">click to browse</span></p>
            </div>

            {files.length > 0 && (
                <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {files.map((file, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                            <FileText size={18} style={{ color: 'var(--accent-blue)' }} />
                            <span style={{ flex: 1, fontSize: '13px' }}>{file.name}</span>
                            <button onClick={() => removeFile(i)} className="btn btn-icon btn-secondary" style={{ width: '28px', height: '28px' }}>
                                <X size={14} />
                            </button>
                        </div>
                    ))}
                    <button className="btn btn-primary" onClick={uploadAll} style={{ marginTop: '8px' }}>
                        Upload {files.length} file{files.length > 1 ? 's' : ''}
                    </button>
                </div>
            )}
        </div>
    );
}
