import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

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
    const saved = localStorage.getItem('dp_explorer_cleaned_data');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (username, password) => {
    const userAuth = { username, password };
    setAuth(userAuth);
    localStorage.setItem('dp_explorer_auth', JSON.stringify(userAuth));
  };

  const logout = () => {
    setAuth(null);
    setCleanedData(null);
    localStorage.removeItem('dp_explorer_auth');
    localStorage.removeItem('dp_explorer_cleaned_data');
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
