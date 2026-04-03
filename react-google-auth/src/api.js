import axios from 'axios';

// Pull the URL from the .env file
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * Phase 2 & 3: Sends the Google access token to Django and awaits the server's session token.
 */
export const sendGoogleTokenToDjango = async (accessToken) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/auth/google/`, {
      // dj-rest-auth expects the token in this specific field
      access_token: accessToken,
    });
    return response.data;
  } catch (error) {
    console.error("Error authenticating with Django:", error.response || error);
    throw error;
  }
};