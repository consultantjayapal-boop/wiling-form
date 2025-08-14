import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const App = () => {
  const [currentView, setCurrentView] = useState('auth');
  const [authMode, setAuthMode] = useState('login');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [language, setLanguage] = useState('english');
  const [wills, setWills] = useState([]);
  const [currentWill, setCurrentWill] = useState(null);
  const [loading, setLoading] = useState(false);

  // Auth state
  const [formData, setFormData] = useState({
    email: '',
    mobile: '',
    password: '',
    confirmPassword: '',
    username: ''
  });

  // Will creation state
  const [willForm, setWillForm] = useState({
    title: '',
    language: 'english',
    content: '',
    aiAssisted: false
  });

  // Message state
  const [messageForm, setMessageForm] = useState({
    recipientName: '',
    recipientEmail: '',
    recipientPhone: '',
    messageText: '',
    preference: 'email'
  });

  // File upload state
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);

  // Translation object
  const translations = {
    english: {
      appTitle: 'Will Writing App',
      login: 'Login',
      signup: 'Sign Up',
      email: 'Email',
      mobile: 'Mobile',
      password: 'Password',
      confirmPassword: 'Confirm Password',
      username: 'Username (Email/Mobile)',
      createWill: 'Create Will',
      writeWill: 'Write a Will',
      selectLanguage: 'Select Language',
      recordAudio: 'Record Audio',
      recordVideo: 'Record Video',
      uploadFile: 'Upload File',
      sendMessage: 'Send Message',
      aiAssistance: 'AI Assistance',
      myWills: 'My Wills',
      logout: 'Logout',
      save: 'Save',
      cancel: 'Cancel',
      loading: 'Loading...',
      recipientName: 'Recipient Name',
      recipientEmail: 'Recipient Email',
      recipientPhone: 'Recipient Phone',
      messageText: 'Message',
      preference: 'Preference',
      whatsapp: 'WhatsApp',
      call: 'Call',
      willTitle: 'Will Title',
      willContent: 'Will Content',
      getAIHelp: 'Get AI Help',
      startRecording: 'Start Recording',
      stopRecording: 'Stop Recording'
    },
    hindi: {
      appTitle: 'वसीयत लेखन ऐप',
      login: 'लॉगिन',
      signup: 'साइन अप',
      email: 'ईमेल',
      mobile: 'मोबाइल',
      password: 'पासवर्ड',
      confirmPassword: 'पासवर्ड की पुष्टि करें',
      username: 'उपयोगकर्ता नाम (ईमेल/मोबाइल)',
      createWill: 'वसीयत बनाएं',
      writeWill: 'वसीयत लिखें',
      selectLanguage: 'भाषा चुनें',
      recordAudio: 'ऑडियो रिकॉर्ड करें',
      recordVideo: 'वीडियो रिकॉर्ड करें',
      uploadFile: 'फाइल अपलोड करें',
      sendMessage: 'संदेश भेजें',
      aiAssistance: 'AI सहायता',
      myWills: 'मेरी वसीयतें',
      logout: 'लॉगआउट',
      save: 'सेव करें',
      cancel: 'रद्द करें',
      loading: 'लोड हो रहा है...',
      recipientName: 'प्राप्तकर्ता का नाम',
      recipientEmail: 'प्राप्तकर्ता का ईमेल',
      recipientPhone: 'प्राप्तकर्ता का फोन',
      messageText: 'संदेश',
      preference: 'प्राथमिकता',
      whatsapp: 'व्हाट्सऐप',
      call: 'कॉल',
      willTitle: 'वसीयत का शीर्षक',
      willContent: 'वसीयत की सामग्री',
      getAIHelp: 'AI की मदद लें',
      startRecording: 'रिकॉर्डिंग शुरू करें',
      stopRecording: 'रिकॉर्डिंग बंद करें'
    },
    telugu: {
      appTitle: 'వీలునామా రాయడం యాప్',
      login: 'లాగిన్',
      signup: 'సైన్ అప్',
      email: 'ఇమెయిల్',
      mobile: 'మొబైల్',
      password: 'పాస్‌వర్డ్',
      confirmPassword: 'పాస్‌వర్డ్ నిర్ధారించండి',
      username: 'వినియోగదారు పేరు (ఇమెయిల్/మొబైల్)',
      createWill: 'వీలునామా సృష్టించండి',
      writeWill: 'వీలునామా రాయండి',
      selectLanguage: 'భాష ఎంచుకోండి',
      recordAudio: 'ఆడియో రికార్డ్ చేయండి',
      recordVideo: 'వీడియో రికార్డ్ చేయండి',
      uploadFile: 'ఫైల్ అప్‌లోడ్ చేయండి',
      sendMessage: 'సందేశం పంపండి',
      aiAssistance: 'AI సహాయం',
      myWills: 'నా వీలునామాలు',
      logout: 'లాగ్‌అవుట్',
      save: 'సేవ్ చేయండి',
      cancel: 'రద్దు చేయండి',
      loading: 'లోడ్ అవుతోంది...',
      recipientName: 'గ్రహీత పేరు',
      recipientEmail: 'గ్రహీత ఇమెయిల్',
      recipientPhone: 'గ్రహీత ఫోన్',
      messageText: 'సందేశం',
      preference: 'ప్రాధాన్యత',
      whatsapp: 'వాట్సాప్',
      call: 'కాల్',
      willTitle: 'వీలునామా శీర్షిక',
      willContent: 'వీలునామా కంటెంట్',
      getAIHelp: 'AI సహాయం పొందండి',
      startRecording: 'రికార్డింగ్ ప్రారంభించండి',
      stopRecording: 'రికార్డింగ్ ఆపండి'
    }
  };

  const t = translations[language];

  // Initialize axios with token
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserProfile();
      fetchWills();
      setCurrentView('dashboard');
    }
  }, [token]);

  // API functions
  const apiCall = async (method, endpoint, data = null) => {
    try {
      setLoading(true);
      const config = {
        method,
        url: `${API_BASE_URL}/api${endpoint}`,
        data
      };
      
      if (token) {
        config.headers = { Authorization: `Bearer ${token}` };
      }
      
      const response = await axios(config);
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      throw error.response?.data?.detail || error.message;
    } finally {
      setLoading(false);
    }
  };

  const fetchUserProfile = async () => {
    try {
      const data = await apiCall('GET', '/user/profile');
      setUser(data);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    }
  };

  const fetchWills = async () => {
    try {
      const data = await apiCall('GET', '/wills/list');
      setWills(data.wills);
    } catch (error) {
      console.error('Failed to fetch wills:', error);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      const endpoint = authMode === 'login' ? '/auth/login' : '/auth/signup';
      const payload = authMode === 'login' 
        ? { username: formData.username, password: formData.password }
        : { 
            email: formData.email, 
            mobile: formData.mobile, 
            password: formData.password, 
            confirm_password: formData.confirmPassword 
          };

      const data = await apiCall('POST', endpoint, payload);
      
      if (data.success) {
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
        setCurrentView('dashboard');
      }
    } catch (error) {
      alert(error);
    }
  };

  const handleCreateWill = async (e) => {
    e.preventDefault();
    try {
      const data = await apiCall('POST', '/wills/create', {
        title: willForm.title,
        language: willForm.language,
        content: willForm.content,
        ai_assisted: willForm.aiAssisted
      });
      
      if (data.success) {
        alert('Will created successfully!');
        if (data.ai_suggestions) {
          alert(`AI Suggestion: ${data.ai_suggestions}`);
        }
        fetchWills();
        setWillForm({ title: '', language: 'english', content: '', aiAssisted: false });
      }
    } catch (error) {
      alert(error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    try {
      const data = await apiCall('POST', '/messages/send', {
        recipient_name: messageForm.recipientName,
        recipient_email: messageForm.recipientEmail,
        recipient_phone: messageForm.recipientPhone,
        message_text: messageForm.messageText,
        preference: messageForm.preference,
        will_id: currentWill?.id
      });
      
      if (data.success) {
        alert('Message sent successfully!');
        setMessageForm({
          recipientName: '',
          recipientEmail: '',
          recipientPhone: '',
          messageText: '',
          preference: 'email'
        });
      }
    } catch (error) {
      alert(error);
    }
  };

  const handleFileUpload = async (files, fileType) => {
    if (!currentWill) {
      alert('Please select a will first');
      return;
    }

    for (let file of files) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_type', fileType);

        const response = await axios.post(
          `${API_BASE_URL}/api/files/upload/${currentWill.id}`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
              Authorization: `Bearer ${token}`
            }
          }
        );

        if (response.data.success) {
          alert(`File ${file.name} uploaded successfully!`);
        }
      } catch (error) {
        alert(`Failed to upload ${file.name}: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const startRecording = async (type) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: type === 'video'
      });

      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (event) => {
        chunks.push(event.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { 
          type: type === 'video' ? 'video/webm' : 'audio/webm' 
        });
        const file = new File([blob], `recording.${type === 'video' ? 'webm' : 'webm'}`, {
          type: blob.type
        });
        handleFileUpload([file], type);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      setMediaRecorder(recorder);
      recorder.start();
      setRecording(true);
    } catch (error) {
      alert('Recording not supported or permission denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && recording) {
      mediaRecorder.stop();
      setRecording(false);
      setMediaRecorder(null);
    }
  };

  const getAIAssistance = async () => {
    if (!willForm.content) {
      alert('Please enter some content first');
      return;
    }

    try {
      const data = await apiCall('POST', '/ai/assist', {
        query: `Help me improve this will content: ${willForm.content}`,
        language: willForm.language,
        will_context: willForm.content
      });

      if (data.success) {
        alert(`AI Suggestion: ${data.response}`);
      }
    } catch (error) {
      alert('AI assistance is currently unavailable');
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setCurrentView('auth');
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  // Render functions
  const renderAuth = () => (
    <div className="auth-container">
      <div className="auth-header">
        <h1>{t.appTitle}</h1>
        <div className="language-selector">
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="english">English</option>
            <option value="hindi">हिंदी</option>
            <option value="telugu">తెలుగు</option>
          </select>
        </div>
      </div>

      <div className="auth-tabs">
        <button 
          className={authMode === 'login' ? 'active' : ''} 
          onClick={() => setAuthMode('login')}
        >
          {t.login}
        </button>
        <button 
          className={authMode === 'signup' ? 'active' : ''} 
          onClick={() => setAuthMode('signup')}
        >
          {t.signup}
        </button>
      </div>

      <form onSubmit={handleAuth} className="auth-form">
        {authMode === 'signup' ? (
          <>
            <input
              type="email"
              placeholder={t.email}
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
            />
            <input
              type="tel"
              placeholder={t.mobile}
              value={formData.mobile}
              onChange={(e) => setFormData({...formData, mobile: e.target.value})}
              required
            />
            <input
              type="password"
              placeholder={t.password}
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
            <input
              type="password"
              placeholder={t.confirmPassword}
              value={formData.confirmPassword}
              onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
              required
            />
          </>
        ) : (
          <>
            <input
              type="text"
              placeholder={t.username}
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              required
            />
            <input
              type="password"
              placeholder={t.password}
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
          </>
        )}
        <button type="submit" disabled={loading}>
          {loading ? t.loading : (authMode === 'login' ? t.login : t.signup)}
        </button>
      </form>
    </div>
  );

  const renderDashboard = () => (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>{t.appTitle}</h1>
        <div className="header-actions">
          <div className="language-selector">
            <select value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="english">English</option>
              <option value="hindi">हिंदी</option>
              <option value="telugu">తెలుగు</option>
            </select>
          </div>
          <button onClick={logout} className="logout-btn">{t.logout}</button>
        </div>
      </div>

      <div className="dashboard-nav">
        <button 
          className={currentView === 'dashboard' ? 'active' : ''} 
          onClick={() => setCurrentView('dashboard')}
        >
          {t.myWills}
        </button>
        <button 
          className={currentView === 'create-will' ? 'active' : ''} 
          onClick={() => setCurrentView('create-will')}
        >
          {t.createWill}
        </button>
        <button 
          className={currentView === 'send-message' ? 'active' : ''} 
          onClick={() => setCurrentView('send-message')}
        >
          {t.sendMessage}
        </button>
      </div>

      <div className="dashboard-content">
        {currentView === 'dashboard' && renderWillsList()}
        {currentView === 'create-will' && renderCreateWill()}
        {currentView === 'send-message' && renderSendMessage()}
      </div>
    </div>
  );

  const renderWillsList = () => (
    <div className="wills-list">
      <h2>{t.myWills}</h2>
      {wills.length === 0 ? (
        <p>No wills created yet. Create your first will!</p>
      ) : (
        <div className="wills-grid">
          {wills.map((will) => (
            <div 
              key={will.id} 
              className={`will-card ${currentWill?.id === will.id ? 'selected' : ''}`}
              onClick={() => setCurrentWill(will)}
            >
              <h3>{will.title}</h3>
              <p><strong>Language:</strong> {will.language}</p>
              <p><strong>Created:</strong> {new Date(will.created_at).toLocaleDateString()}</p>
              {will.ai_suggestions && (
                <p className="ai-badge">AI Assisted</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderCreateWill = () => (
    <div className="create-will">
      <h2>{t.writeWill}</h2>
      
      <form onSubmit={handleCreateWill} className="will-form">
        <input
          type="text"
          placeholder={t.willTitle}
          value={willForm.title}
          onChange={(e) => setWillForm({...willForm, title: e.target.value})}
          required
        />
        
        <div className="form-group">
          <label>{t.selectLanguage}:</label>
          <select 
            value={willForm.language} 
            onChange={(e) => setWillForm({...willForm, language: e.target.value})}
          >
            <option value="english">English</option>
            <option value="hindi">Hindi</option>
            <option value="telugu">Telugu</option>
          </select>
        </div>

        <textarea
          placeholder={t.willContent}
          value={willForm.content}
          onChange={(e) => setWillForm({...willForm, content: e.target.value})}
          rows="8"
        />

        <div className="form-actions">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={willForm.aiAssisted}
              onChange={(e) => setWillForm({...willForm, aiAssisted: e.target.checked})}
            />
            {t.getAIHelp}
          </label>
          
          <button type="button" onClick={getAIAssistance} className="ai-btn">
            {t.aiAssistance}
          </button>
        </div>

        <button type="submit" disabled={loading} className="submit-btn">
          {loading ? t.loading : t.save}
        </button>
      </form>

      {/* File Upload Section */}
      <div className="file-upload-section">
        <h3>Add Files to Will</h3>
        
        <div className="upload-options">
          <div className="upload-option">
            <input
              type="file"
              accept="audio/*"
              multiple
              onChange={(e) => handleFileUpload(Array.from(e.target.files), 'audio')}
              id="audio-upload"
              style={{display: 'none'}}
            />
            <label htmlFor="audio-upload" className="upload-btn">
              {t.uploadFile} (Audio)
            </label>
          </div>

          <div className="upload-option">
            <input
              type="file"
              accept="video/*"
              multiple
              onChange={(e) => handleFileUpload(Array.from(e.target.files), 'video')}
              id="video-upload"
              style={{display: 'none'}}
            />
            <label htmlFor="video-upload" className="upload-btn">
              {t.uploadFile} (Video)
            </label>
          </div>

          <div className="upload-option">
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              multiple
              onChange={(e) => handleFileUpload(Array.from(e.target.files), 'documents')}
              id="document-upload"
              style={{display: 'none'}}
            />
            <label htmlFor="document-upload" className="upload-btn">
              {t.uploadFile} (Document)
            </label>
          </div>
        </div>

        <div className="recording-options">
          <button
            type="button"
            onClick={() => recording ? stopRecording() : startRecording('audio')}
            className={`record-btn ${recording ? 'recording' : ''}`}
          >
            {recording ? t.stopRecording : t.recordAudio}
          </button>

          <button
            type="button"
            onClick={() => recording ? stopRecording() : startRecording('video')}
            className={`record-btn ${recording ? 'recording' : ''}`}
          >
            {recording ? t.stopRecording : t.recordVideo}
          </button>
        </div>
      </div>
    </div>
  );

  const renderSendMessage = () => (
    <div className="send-message">
      <h2>{t.sendMessage}</h2>
      
      <form onSubmit={handleSendMessage} className="message-form">
        <input
          type="text"
          placeholder={t.recipientName}
          value={messageForm.recipientName}
          onChange={(e) => setMessageForm({...messageForm, recipientName: e.target.value})}
          required
        />
        
        <input
          type="email"
          placeholder={t.recipientEmail}
          value={messageForm.recipientEmail}
          onChange={(e) => setMessageForm({...messageForm, recipientEmail: e.target.value})}
          required
        />
        
        <input
          type="tel"
          placeholder={t.recipientPhone}
          value={messageForm.recipientPhone}
          onChange={(e) => setMessageForm({...messageForm, recipientPhone: e.target.value})}
          required
        />
        
        <textarea
          placeholder={t.messageText}
          value={messageForm.messageText}
          onChange={(e) => setMessageForm({...messageForm, messageText: e.target.value})}
          rows="5"
          required
        />
        
        <div className="form-group">
          <label>{t.preference}:</label>
          <select 
            value={messageForm.preference} 
            onChange={(e) => setMessageForm({...messageForm, preference: e.target.value})}
          >
            <option value="email">Email</option>
            <option value="whatsapp">{t.whatsapp}</option>
            <option value="call">{t.call}</option>
          </select>
        </div>

        <button type="submit" disabled={loading} className="submit-btn">
          {loading ? t.loading : t.sendMessage}
        </button>
      </form>
    </div>
  );

  return (
    <div className="App">
      {token ? renderDashboard() : renderAuth()}
    </div>
  );
};

export default App;