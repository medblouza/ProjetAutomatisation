import axios from 'axios';

// Base URL is empty to use the Vite dev server proxy in development,
// or fallback to localhost:8000 if needed.
const API_BASE = '';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 600000, // Large timeout for site-gen / wireframe generation (up to 10 min)
});

export const apiService = {
  // Authentication & Client Data
  login: async (username, password) => {
    const response = await client.post('/login', { username, password });
    return response.data;
  },

  getInfo: async (auth, code) => {
    const response = await client.post('/info', {
      username: auth.username,
      password: auth.password,
      code,
    });
    return response.data;
  },

  generateCdc: async (auth, code) => {
    // Longer timeout specifically for cdc generation
    const response = await client.post('/generate-cdc', {
      username: auth.username,
      password: auth.password,
      code,
    }, { timeout: 600000 });
    return response.data;
  },

  cleanData: async (auth, code) => {
    const response = await client.post('/clean', {
      username: auth.username,
      password: auth.password,
      code,
    });
    return response.data;
  },

  downloadDocx: async (content, filename) => {
    const response = await client.post('/api/download-docx', { content, filename }, {
      responseType: 'blob',
      timeout: 30000
    });
    return response.data;
  },

  // Dropbox Endpoints
  getDropboxAuthUrl: async () => {
    const response = await client.get('/dropbox/auth-url', { timeout: 10000 });
    return response.data;
  },

  callbackDropbox: async (code, state) => {
    const response = await client.post('/dropbox/callback', { code, state }, { timeout: 15000 });
    return response.data;
  },

  listDropboxFiles: async (accessToken, path) => {
    const response = await client.post('/dropbox/list', {
      access_token: accessToken,
      path: path,
      recursive: false,
    }, { timeout: 30000 });
    return response.data;
  },

  searchDropboxFiles: async (accessToken, query) => {
    const response = await client.post('/dropbox/search', {
      access_token: accessToken,
      query: query,
      path: '',
    }, { timeout: 30000 });
    return response.data;
  },

  downloadDropboxFile: async (accessToken, path) => {
    const response = await client.post('/dropbox/download', {
      access_token: accessToken,
      path: path,
    }, {
      responseType: 'blob',
      timeout: 60000,
    });
    return response.data;
  },

  checkDropboxAssets: async (accessToken, path) => {
    const response = await client.post('/dropbox/check-assets', {
      access_token: accessToken,
      path: path,
    }, { timeout: 120000 });
    return response.data;
  },

  // Style Extractor Tab (API routes prefix is /api)
  extractStyle: async (files) => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    const response = await client.post('/api/style/extract', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    });
    return response.data;
  },

  // Site Gen Tab
  /*analyzeDoc: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await client.post('/api/cdc/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000,
    });
    return response.data;
  },*/

  generateDesign: async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await client.post(
        "/api/design/generate-file",
        formData,
        {
            headers: {
                "Content-Type": "multipart/form-data"
            },
            timeout: 300000
        }
    );

    return response.data;
  },

  generateSite: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await client.post('/api/site-gen/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000, // 5 minutes
    });
    return response.data;
  },

  // Design Pipeline
generateDesignFromFile: async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await client.post(
    '/api/design/generate-file',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 600000,
    }
  );

  return response.data;
},

generateWebsiteFromDesign: async (designJson) => {
  const response = await client.post(
    '/api/web-generator/generate',
    designJson,
    {
      timeout: 600000,
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  return response.data;
},

  // Wireframe tab
  generateWireframe: async (cleanedData) => {
    const response = await client.post('/api/generate-wireframe', {
      cleaned_data: cleanedData,
    }, { timeout: 180000 });
    return response.data;
  },

  // ── CDC & DesignJSON tab ─────────────────────────────────
  /**
   * Retourne la liste de tous les CDC (id, company_name, created_at).
   * Le contenu Markdown est exclu pour rester léger.
   */
  getCdcList: async () => {
    const response = await client.get('/api/cdc', { timeout: 15000 });
    return response.data;
  },

  /**
   * Retourne le CDC complet (avec contenu Markdown) pour un id donné.
   */
  getCdcById: async (id) => {
    const response = await client.get(`/api/cdc/${id}`, { timeout: 15000 });
    return response.data;
  },

  /**
   * Crée un nouveau CDC.
   */
  createCdc: async (data) => {
    const response = await client.post('/api/cdc', data, { timeout: 15000 });
    return response.data;
  },

  /**
   * Met à jour un CDC existant.
   */
  updateCdc: async (id, data) => {
    const response = await client.put(`/api/cdc/${id}`, data, { timeout: 15000 });
    return response.data;
  },

  /**
   * Supprime un CDC.
   */
  deleteCdc: async (id) => {
    const response = await client.delete(`/api/cdc/${id}`, { timeout: 15000 });
    return response.data;
  },

  /**
   * Retourne la liste de tous les DesignJSON (id, filename, company_name, created_at).
   */
  getDesignJsonList: async () => {
    const response = await client.get('/api/design-jsons', { timeout: 15000 });
    return response.data;
  },

  /**
   * Retourne le DesignJSON complet (avec contenu JSON) pour un id donné.
   */
  getDesignJsonById: async (id) => {
    const response = await client.get(`/api/design-jsons/${id}`, { timeout: 15000 });
    return response.data;
  },

  /**
   * Crée un nouveau DesignJSON.
   */
  createDesignJson: async (data) => {
    const response = await client.post('/api/design-jsons', data, { timeout: 15000 });
    return response.data;
  },

  /**
   * Met à jour un DesignJSON existant.
   */
  updateDesignJson: async (id, data) => {
    const response = await client.put(`/api/design-jsons/${id}`, data, { timeout: 15000 });
    return response.data;
  },

  /**
   * Supprime un DesignJSON.
   */
  deleteDesignJson: async (id) => {
    const response = await client.delete(`/api/design-jsons/${id}`, { timeout: 15000 });
    return response.data;
  },
};
export default apiService;
