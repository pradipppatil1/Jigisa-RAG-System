'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { fetchWithAuth } from '@/lib/api';
import Link from 'next/link';

export default function EvaluationsPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  
  const [evalData, setEvalData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!user) return router.push('/');
    if (user.role !== 'c_level') {
      router.push('/chat'); // Restrict
    }
  }, [user, router]);

  useEffect(() => {
    if (user?.role === 'c_level') {
        fetchEvalData();
    }
  }, [user]);

  const fetchEvalData = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
        const data = await fetchWithAuth('/evaluation/results');
        setEvalData(data || []);
    } catch (err: any) {
        setErrorMsg(err.message || 'Failed to load evaluation reports.');
    } finally {
        setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
      if (score >= 0.85) return '#10b981'; // Green
      if (score >= 0.70) return '#f59e0b'; // Yellow/Orange
      return '#ef4444'; // Red
  };

  if (!user || user.role !== 'c_level') return null;

  return (
    <div className="layout-container">
      <div className="sidebar" style={{ width: '240px' }}>
         <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ margin: 0, fontSize: '1.25rem', color: 'var(--accent-color)' }}>FinBot Admin</h2>
          {user && <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: 0 }}>Logged in as: <strong>{user.username}</strong></p>}
         </div>
         <div style={{ padding: '1.5rem', flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <Link href="/admin" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>
                    Core Dashboard
                </Link>
                <Link href="/admin/evaluations" style={{ color: 'var(--accent-color)', textDecoration: 'none', fontWeight: 600 }}>
                    Evaluation Reports
                </Link>
            </div>
            
            <div style={{ marginTop: 'auto' }}>
                <Link href="/chat" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>
                    &larr; Back to Chat
                </Link>
            </div>
         </div>
         <div style={{ padding: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
            <button onClick={() => { logout(); router.push('/') }} style={{ width: '100%', padding: '0.75rem', background: 'var(--bg-color)', color: 'var(--text-secondary)', borderRadius: '6px', border: '1px solid var(--border-color)', cursor: 'pointer', outline: 'none' }}>
               Sign Out
            </button>
         </div>
      </div>
      
      <div className="main-content" style={{ overflowY: 'auto', padding: '3rem 5rem' }}>
         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
             <h1>Ablation Study Reports</h1>
             <button onClick={fetchEvalData} className="btn-primary" style={{ padding: '0.5rem 1rem' }}>Refresh Data</button>
         </div>

         {errorMsg && <div style={{ background: 'var(--danger-color)', color: '#fff', padding: '1rem', borderRadius: '6px', marginBottom: '1.5rem' }}>{errorMsg}</div>}

         {loading ? (
             <div style={{ color: 'var(--text-secondary)' }}>Loading evaluation results...</div>
         ) : evalData.length === 0 ? (
             <div className="login-box" style={{ margin: 0, textAlign: 'center', padding: '3rem' }}>
                 <h2 style={{ color: 'var(--text-secondary)', marginTop: 0 }}>No Data Available</h2>
                 <p style={{ color: 'var(--text-secondary)' }}>Evaluation metrics have not been generated yet.</p>
                 <code style={{ background: 'var(--bg-color)', padding: '0.5rem 1rem', borderRadius: '4px', display: 'inline-block', marginTop: '1rem' }}>cd Back-End && python -m app.evaluation.evaluate</code>
             </div>
         ) : (
             <div style={{ background: 'rgba(255, 255, 255, 0.03)', borderRadius: '12px', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
                 <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                     <thead>
                         <tr style={{ background: 'var(--bg-color)', borderBottom: '2px solid var(--border-color)' }}>
                             <th style={{ padding: '1rem', fontWeight: 600 }}>Configuration</th>
                             <th style={{ padding: '1rem', fontWeight: 600 }}>Faithfulness</th>
                             <th style={{ padding: '1rem', fontWeight: 600 }}>Answer Relevancy</th>
                             <th style={{ padding: '1rem', fontWeight: 600 }}>Context Precision</th>
                             <th style={{ padding: '1rem', fontWeight: 600 }}>Context Recall</th>
                             <th style={{ padding: '1rem', fontWeight: 600 }}>Answer Correctness</th>
                         </tr>
                     </thead>
                     <tbody>
                         {evalData.map((row, idx) => (
                             <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                                 <td style={{ padding: '1rem', fontWeight: 'bold' }}>{row.Configuration || 'Unknown'}</td>
                                 <td style={{ padding: '1rem', color: getScoreColor(row.faithfulness) }}>
                                     {row.faithfulness !== undefined && row.faithfulness !== null ? (row.faithfulness * 100).toFixed(1) + '%' : 'N/A'}
                                 </td>
                                 <td style={{ padding: '1rem', color: getScoreColor(row.answer_relevancy) }}>
                                     {row.answer_relevancy !== undefined && row.answer_relevancy !== null ? (row.answer_relevancy * 100).toFixed(1) + '%' : 'N/A'}
                                 </td>
                                 <td style={{ padding: '1rem', color: getScoreColor(row.context_precision) }}>
                                     {row.context_precision !== undefined && row.context_precision !== null ? (row.context_precision * 100).toFixed(1) + '%' : 'N/A'}
                                 </td>
                                 <td style={{ padding: '1rem', color: getScoreColor(row.context_recall) }}>
                                     {row.context_recall !== undefined && row.context_recall !== null ? (row.context_recall * 100).toFixed(1) + '%' : 'N/A'}
                                 </td>
                                 <td style={{ padding: '1rem', color: getScoreColor(row.answer_correctness) }}>
                                     {row.answer_correctness !== undefined && row.answer_correctness !== null ? (row.answer_correctness * 100).toFixed(1) + '%' : 'N/A'}
                                 </td>
                             </tr>
                         ))}
                     </tbody>
                 </table>
             </div>
         )}
      </div>
    </div>
  );
}
