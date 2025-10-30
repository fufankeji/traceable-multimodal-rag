import { useState } from "react";

// Simple test version to check if rendering works
export default function App() {
  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#0a0e1a',
      color: '#e8edf5'
    }}>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '1rem' }}>多模态文档检索 RAG</h1>
        <p style={{ color: '#94a3b8' }}>前端应用正在运行...</p>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginTop: '1rem' }}>
          如果您看到这个页面，说明 React 和 Vite 已经正常工作
        </p>
      </div>
    </div>
  );
}
