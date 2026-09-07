import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

// ─── Liste centralisée de toutes les clés localStorage de pages ───────────────
// Maintenir cette liste à jour si de nouvelles clés sont ajoutées.
const ALL_PAGE_STATE_KEYS = [
  // DPExplorer
  'dp_activeCode',
  'dp_clientInfo',
  'dp_cdcContent',
  'dp_qaScore',
  'dp_cleanedJson',
  // SiteGenerator
  'sg_designJson',
  'sg_jsonText',
  'sg_generatedSite',
  // StyleExtractor
  'se_styleResult',
  // Wireframe
  'dp_explorer_last_wireframe',
  // cleanedData partagé
  'dp_explorer_cleaned_data',
];

const clearAllPageState = () => {
  ALL_PAGE_STATE_KEYS.forEach((key) => localStorage.removeItem(key));
};

export const AuthProvider = ({ children }) => {
  const [auth, setAuth] = useState(() => {
    const saved = localStorage.getItem('dp_explorer_auth');
    return saved ? JSON.parse(saved) : null;
  });

  const [dbxAccessToken, setDbxAccessToken] = useState(() => {
    return localStorage.getItem('dp_explorer_dbx_token') || '';
  });

  // Share cleaned data globally since it is needed by both DP Explorer and Wireframe pages
  const [cleanedData, setCleanedData] = useState(() => {
    // Only restore cleanedData if the user is already authenticated
    const isAuth = !!localStorage.getItem('dp_explorer_auth');
    if (!isAuth) return null;
    const saved = localStorage.getItem('dp_explorer_cleaned_data');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (username, password) => {
    // Effacer toutes les données persistées de la session précédente avant de connecter
    clearAllPageState();
    const userAuth = { username, password };
    setAuth(userAuth);
    setCleanedData(null);
    localStorage.setItem('dp_explorer_auth', JSON.stringify(userAuth));
  };

  const logout = () => {
    setAuth(null);
    setCleanedData(null);
    localStorage.removeItem('dp_explorer_auth');
    // Effacer toutes les données persistées de pages
    clearAllPageState();
  };

  const saveDbxToken = (token) => {
    setDbxAccessToken(token);
    localStorage.setItem('dp_explorer_dbx_token', token);
  };

  const logoutDropbox = () => {
    setDbxAccessToken('');
    localStorage.removeItem('dp_explorer_dbx_token');
  };

  const updateCleanedData = (data) => {
    setCleanedData(data);
    if (data) {
      localStorage.setItem('dp_explorer_cleaned_data', JSON.stringify(data));
    } else {
      localStorage.removeItem('dp_explorer_cleaned_data');
    }
  };

  return (
    <AuthContext.Provider value={{
      auth,
      login,
      logout,
      dbxAccessToken,
      setDbxAccessToken: saveDbxToken,
      logoutDropbox,
      cleanedData,
      setCleanedData: updateCleanedData,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
