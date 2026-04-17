'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { fetchWithAuth, uploadFileWithAuth } from '@/lib/api';
import Link from 'next/link';

const AVAILABLE_ROLES = ["employee", "finance", "engineering", "marketing", "c_level"];
const AVAILABLE_COLLECTIONS = ["general", "finance", "engineering", "marketing", "hr"];

export default function AdminPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  
  // Notification states
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Tab State
  const [activeTab, setActiveTab] = useState<'users' | 'knowledge'>('users');

  // Register state
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('employee');
  const [department, setDepartment] = useState('General');

  // Document Upload state
  const [docFile, setDocFile] = useState<File | null>(null);
  const [docCollection, setDocCollection] = useState('engineering');
  const [docRoles, setDocRoles] = useState<string[]>(['c_level']);
  const [uploading, setUploading] = useState(false);

  // Document Delete state
  const [delFilename, setDelFilename] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [delSuccessMsg, setDelSuccessMsg] = useState('');
  const [delErrorMsg, setDelErrorMsg] = useState('');

  useEffect(() => {
    if (!user) return router.push('/');
    if (user.role !== 'c_level') {
      router.push('/chat'); // Restrict
    }
  }, [user, router]);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg('');
    setErrorMsg('');
    try {
      await fetchWithAuth('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password, role, department })
      });
      setSuccessMsg(`User ${username} successfully registered!`);
      setUsername(''); setEmail(''); setPassword('');
    } catch (err: any) {
      setErrorMsg(err.message || 'Registration failed');
    }
  };

  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newRole = e.target.value;
    setRole(newRole);
    const roleDeptMap: Record<string, string> = {
        'employee': 'General',
        'finance': 'Finance',
        'engineering': 'Engineering',
        'marketing': 'Marketing',
        'c_level': 'Executive'
    };
    if (roleDeptMap[newRole]) {
        setDepartment(roleDeptMap[newRole]);
    }
  };

  const handleRoleToggle = (toggleRole: string) => {
    setDocRoles(prev => 
        prev.includes(toggleRole) 
            ? prev.filter(r => r !== toggleRole) 
            : [...prev, toggleRole]
    );
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docFile) return setErrorMsg("Select a file to upload.");
    setSuccessMsg(''); setErrorMsg(''); setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', docFile);
      formData.append('collection', docCollection);
      if (docRoles.length > 0) {
          formData.append('access_roles', docRoles.join(','));
      }
      
      await uploadFileWithAuth('/ingesta/upload', formData);
      setSuccessMsg(`Document uploaded successfully to ${docCollection}!`);
      setDocFile(null);
      const el = document.getElementById('file-upload') as HTMLInputElement;
      if (el) el.value = '';
    } catch (err: any) {
      setErrorMsg(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!delFilename.trim()) return;
    setDelSuccessMsg(''); setDelErrorMsg(''); setDeleting(true);
    try {
      await fetchWithAuth(`/ingesta/document/${delFilename.trim()}`, {
        method: 'DELETE'
      });
      setDelSuccessMsg(`Document ${delFilename} wiped correctly.`);
      setDelFilename('');
    } catch (err: any) {
      setDelErrorMsg(err.message || 'Deletion failed');
    } finally {
      setDeleting(false);
    }
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
                <Link href="/admin" style={{ color: 'var(--accent-color)', textDecoration: 'none', fontWeight: 600 }}>
                    Core Dashboard
                </Link>
                <Link href="/admin/evaluations" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>
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
         <h1>Admin Dashboard</h1>
         
         <div className="admin-tabs">
            <button 
                className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`}
                onClick={() => { setActiveTab('users'); setSuccessMsg(''); setErrorMsg(''); setDelSuccessMsg(''); setDelErrorMsg(''); }}
            >
                User Management
            </button>
            <button 
                className={`tab-btn ${activeTab === 'knowledge' ? 'active' : ''}`}
                onClick={() => { setActiveTab('knowledge'); setSuccessMsg(''); setErrorMsg(''); setDelSuccessMsg(''); setDelErrorMsg(''); }}
            >
                Knowledge Repo Base
            </button>
         </div>

         {successMsg && <div style={{ background: 'var(--success-color)', color: '#fff', padding: '1rem', borderRadius: '6px', marginBottom: '1.5rem' }}>{successMsg}</div>}
         {errorMsg && <div style={{ background: 'var(--danger-color)', color: '#fff', padding: '1rem', borderRadius: '6px', marginBottom: '1.5rem' }}>{errorMsg}</div>}

         {activeTab === 'users' && (
             <div className="login-box" style={{ margin: 0, maxWidth: '600px' }}>
                <h2 style={{ marginTop: 0 }}>Register New User</h2>
                <form onSubmit={handleRegister} className="login-form">
                   <div className="input-group">
                      <label>Username</label>
                      <input type="text" value={username} onChange={e => setUsername(e.target.value)} required />
                   </div>
                   <div className="input-group">
                      <label>Email</label>
                      <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
                   </div>
                   <div className="input-group">
                      <label>Password</label>
                      <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
                   </div>
                   <div style={{ display: 'flex', gap: '1rem' }}>
                       <div className="input-group" style={{ flex: 1 }}>
                          <label>System Role</label>
                          <select 
                             value={role} 
                             onChange={handleRoleChange}
                             style={{ width: '100%', padding: '0.75rem', background: 'var(--bg-color)', color: 'white', border: '1px solid var(--border-color)', borderRadius: '6px' }}
                          >
                             {AVAILABLE_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                          </select>
                       </div>
                       <div className="input-group" style={{ flex: 1 }}>
                          <label>Department</label>
                          <select 
                             value={department} 
                             onChange={e => setDepartment(e.target.value)}
                             style={{ width: '100%', padding: '0.75rem', background: 'var(--bg-color)', color: 'white', border: '1px solid var(--border-color)', borderRadius: '6px' }}
                          >
                             <option value="General">General</option>
                             <option value="Finance">Finance</option>
                             <option value="Engineering">Engineering</option>
                             <option value="Marketing">Marketing</option>
                             <option value="Executive">Executive</option>
                          </select>
                       </div>
                   </div>
                   
                   <button type="submit" className="btn-primary" style={{ marginTop: '1rem' }}>Create User</button>
                </form>
             </div>
         )}

         {activeTab === 'knowledge' && (
             <div style={{ display: 'flex', flexDirection: 'row', gap: '2rem', alignItems: 'flex-start' }}>
                 
                 {/* UPLOAD DOC */}
                 <div className="login-box" style={{ margin: 0, flex: 1 }}>
                    <h2 style={{ marginTop: 0 }}>Upload Document</h2>
                    <form onSubmit={handleUpload} className="login-form">
                       <div className="input-group">
                          <label>Select PDF File</label>
                          <input 
                              id="file-upload"
                              type="file" 
                              accept=".pdf" 
                              onChange={e => setDocFile(e.target.files?.[0] || null)} 
                              required 
                              style={{ padding: '0.5rem 0' }}
                          />
                       </div>
                       
                       <div className="input-group">
                          <label>Target Collection</label>
                          <select 
                             value={docCollection} 
                             onChange={e => setDocCollection(e.target.value)}
                             style={{ width: '100%', padding: '0.75rem', background: 'var(--bg-color)', color: 'white', border: '1px solid var(--border-color)', borderRadius: '6px' }}
                          >
                             {AVAILABLE_COLLECTIONS.map(c => <option key={c} value={c}>{c}</option>)}
                          </select>
                       </div>

                       <div className="input-group">
                          <label style={{ display: 'block', marginBottom: '0.5rem' }}>Explicit Access Roles</label>
                          {/* Clean 1-column Vertical Flex List */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', background: 'var(--bg-color)', padding: '1.25rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                              {AVAILABLE_ROLES.map(r => (
                                  <label key={r} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.9rem', cursor: 'pointer', margin: 0 }}>
                                      <input 
                                          type="checkbox" 
                                          checked={docRoles.includes(r)}
                                          onChange={() => handleRoleToggle(r)}
                                          style={{ margin: 0, cursor: 'pointer', width: 'auto', outline: 'none' }}
                                      />
                                      {r}
                                  </label>
                              ))}
                          </div>
                          <small style={{ color: 'var(--text-secondary)', display: 'block', marginTop: '0.5rem' }}>Selected roles will be explicitly bound to the document metadata.</small>
                       </div>

                       <button type="submit" className="btn-primary" disabled={uploading} style={{ marginTop: '1rem' }}>
                          {uploading ? 'Processing & Ingesting...' : 'Upload & Route'}
                       </button>
                    </form>
                 </div>

                 {/* DELETE DOC */}
                 <div className="login-box" style={{ margin: 0, flex: 1, borderTop: '4px solid var(--danger-color)' }}>
                    <h2 style={{ marginTop: 0, color: 'var(--danger-color)' }}>Danger Zone</h2>
                    
                    {delSuccessMsg && <div style={{ background: 'var(--success-color)', color: '#fff', padding: '1rem', borderRadius: '6px', marginBottom: '1.5rem' }}>{delSuccessMsg}</div>}
                    {delErrorMsg && <div style={{ background: 'var(--danger-color)', color: '#fff', padding: '1rem', borderRadius: '6px', marginBottom: '1.5rem' }}>{delErrorMsg}</div>}
                    <form onSubmit={handleDeleteDoc} className="login-form">
                       <div className="input-group">
                          <label>Delete by Filename</label>
                          <input 
                              type="text" 
                              value={delFilename} 
                              onChange={e => setDelFilename(e.target.value)} 
                              placeholder="e.g., employee_handbook.pdf"
                              required 
                          />
                       </div>
                       <button type="submit" className="btn-primary" disabled={deleting} style={{ marginTop: '0.5rem', background: 'var(--danger-color)' }}>
                          {deleting ? 'Deleting...' : 'Purge Document'}
                       </button>
                    </form>
                 </div>

             </div>
         )}
      </div>
    </div>
  );
}
