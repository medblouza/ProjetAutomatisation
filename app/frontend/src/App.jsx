import React, { useState } from 'react';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { NotificationProvider } from './hooks/useNotification';
import DashboardLayout from './layouts/DashboardLayout';

// Pages
import Login from './pages/Login';
import DPExplorer from './pages/DPExplorer';
import Dropbox from './pages/Dropbox';
import SharedFolder from './pages/SharedFolder';
import Wireframe from './pages/Wireframe';
import StyleExtractor from './pages/StyleExtractor';
import SiteGenerator from './pages/SiteGenerator';
import CDCList from './pages/CDCList';

const DashboardSwitcher = () => {
  const { auth } = useAuth();
  const [activeTab, setActiveTab] = useState('dp');

  // If user is not authenticated, force login screen
  if (!auth) {
    return <Login />;
  }

  // Choose the page panel matching active navigation item
  const renderContent = () => {
    switch (activeTab) {
      case 'dp':
        return <DPExplorer />;
      case 'dbx':
        return <Dropbox />;
      case 'drive':
        return <SharedFolder />;
      case 'wireframe':
        return <Wireframe />;
      case 'style':
        return <StyleExtractor />;
      case 'sitegen':
        return <SiteGenerator />;
      case 'cdc':
        return <CDCList />;
      default:
        return <DPExplorer />;
    }
  };

  return (
    <DashboardLayout activeTab={activeTab} setActiveTab={setActiveTab}>
      {renderContent()}
    </DashboardLayout>
  );
};

export default function App() {
  return (
    <NotificationProvider>
      <AuthProvider>
        <DashboardSwitcher />
      </AuthProvider>
    </NotificationProvider>
  );
}
