import React, { useState, useEffect } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { sendGoogleTokenToDjango } from './api';

function App() {
  // Check local storage on startup (mirrors Flutter's SharedPreferences)
  const [djangoToken, setDjangoToken] = useState(localStorage.getItem('django_token'));
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Phase 1: Initialize the Google Login flow
  const loginWithGoogle = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setIsLoading(true);
      setError(null);
      
      try {
        console.log("Phase 1 Complete: Received Google Access Token");
        
        // Phase 2 & 3: Send token to Django and get the server session token back
        const data = await sendGoogleTokenToDjango(tokenResponse.access_token);
        
        // dj-rest-auth default TokenAuthentication returns the token in the 'key' field
        const serverToken = data.key; 
        
        setDjangoToken(serverToken);
        localStorage.setItem('django_token', serverToken);
        
        console.log("Phase 3 Complete: Authenticated with Django!");
      } catch (err) {
        setError("Failed to verify login with the backend server.");
      } finally {
        setIsLoading(false);
      }
    },
    onError: (errorResponse) => {
      setError("User cancelled or Google login failed.");
      console.log(errorResponse);
    },
  });

  const handleLogout = () => {
    setDjangoToken(null);
    localStorage.removeItem('django_token');
  };

  // --- UI Rendering ---

  // Simple inline styles for the intern task
  const containerStyle = { fontFamily: 'sans-serif', textAlign: 'center', marginTop: '50px' };
  const buttonStyle = { padding: '10px 20px', fontSize: '16px', cursor: 'pointer' };

  if (isLoading) {
    return <div style={containerStyle}><h2>Loading authentication...</h2></div>;
  }

  return (
    <div style={containerStyle}>
      <h1>React Intern Task: Google OAuth</h1>
      
      {error && <p style={{ color: 'red' }}>{error}</p>}

      {djangoToken ? (
        <div>
          <h2 style={{ color: 'green' }}>Welcome to the Dashboard!</h2>
          <p>Your Django Session Key:</p>
          <code style={{ background: '#eee', padding: '5px', display: 'block', margin: '20px auto', width: '300px' }}>
            {djangoToken}
          </code>
          <button style={buttonStyle} onClick={handleLogout}>Logout</button>
        </div>
      ) : (
        <div>
          <p>Click below to start the Flutter-style 3-step OAuth flow.</p>
          <button style={buttonStyle} onClick={() => loginWithGoogle()}>
            Sign in with Google
          </button>
        </div>
      )}
    </div>
  );
}

export default App;