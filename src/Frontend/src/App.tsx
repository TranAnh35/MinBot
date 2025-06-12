import { useState } from 'react';
import { Header } from './components/Layouts/Header';
import { ChatBot } from './components/Chat/ChatBot';
import { DocumentUploader } from './components/DocumentUploader';
import { SettingsModal } from './components/Settings/SettingsModal';

function App() {
  const [showUploader, setShowUploader] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showConversations, setShowConversations] = useState(false);
  const [apiKey, setApiKey] = useState('');

  const handleConversationsClick = () => {
    setShowConversations(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        onUploadClick={() => setShowUploader(true)} 
        onSettingsClick={() => setShowSettings(true)}
        onConversationsClick={handleConversationsClick}
      />
      <ChatBot 
        uploadedFiles={[]} 
        selectedFiles={[]} 
        onFileSelect={() => {}} 
        onUploadClick={() => {}}
        showConversations={showConversations}
        onCloseConversations={() => setShowConversations(false)}
      />
      
      {showUploader && (
        <DocumentUploader
          onClose={() => setShowUploader(false)}
        />
      )}
      {showSettings && (
        <SettingsModal
          isOpen={showSettings}
          onClose={() => setShowSettings(false)}
          apiKey={apiKey}
          onSaveApiKey={setApiKey}
        />
      )}
    </div>
  );
}

export default App;