import '../styles/globals.css';
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          backgroundColor: '#0b0f19',
          color: '#f3f4f6',
          fontFamily: 'Inter, sans-serif',
          padding: '20px',
          textAlign: 'center'
        }}>
          <h2 style={{ color: '#ef4444', marginBottom: '10px' }}>Something went wrong.</h2>
          <p style={{ color: '#9ca3af', marginBottom: '20px', maxWidth: '500px' }}>
            {this.state.error?.message || "An unexpected frontend error occurred. Please refresh or try again."}
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold',
              transition: 'background-color 0.2s'
            }}
            onMouseOver={(e) => e.target.style.backgroundColor = '#2563eb'}
            onMouseOut={(e) => e.target.style.backgroundColor = '#3b82f6'}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

import { AuthProvider, useAuth } from '../components/AuthContext';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

function RouteGuard({ children }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const path = router.pathname;

  useEffect(() => {
    if (!loading) {
      if (!user && path.startsWith('/app')) {
        router.push('/login');
      } else if (user && path === '/login') {
        router.push('/app');
      }
    }
  }, [user, loading, path, router]);

  if (loading && path.startsWith('/app')) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: '#06080f',
        color: '#f0f4f8',
        fontFamily: 'Inter, sans-serif'
      }}>
        <div className="spinner" />
        <p style={{ marginTop: '16px', color: '#8b9ab5', fontSize: '14px' }}>Loading DocIntel AI...</p>
      </div>
    );
  }

  return children;
}

export default function App({ Component, pageProps }) {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <RouteGuard>
          <Component {...pageProps} />
        </RouteGuard>
      </AuthProvider>
    </ErrorBoundary>
  );
}
