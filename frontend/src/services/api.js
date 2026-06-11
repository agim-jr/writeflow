// frontend/src/services/api.js
import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";
export const WS_BASE_URL = "ws://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

// Community Posts
export const canPostToday = async () => {
  // Changed from /community/can-post-today to /community/can-post
  const response = await api.get("/community/can-post");
  return response.data;
};

export const createPost = async (postData) => {
  // Removed /api/v1 prefix (already in baseURL)
  const response = await api.post("/community/posts", postData);
  return response.data;
};

export const getPosts = async () => {
  // Removed /api/v1 prefix (already in baseURL)
  const response = await api.get("/community/posts");
  return response.data;
};

export const addReaction = async (postId, reactionType) => {
  // Updated to match backend reaction endpoint
  const response = await api.post(`/community/posts/${postId}/react`, {
    reaction_type: reactionType,
  });
  return response.data;
};

export const removeReaction = async (postId) => {
  // New function to remove reaction
  const response = await api.delete(`/community/posts/${postId}/react`);
  return response.data;
};

export const deletePost = async (postId) => {
  const response = await api.delete(`/community/posts/${postId}`);
  return response.data;
};

export default api;
