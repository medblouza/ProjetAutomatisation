import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotification } from '../hooks/useNotification';
import { apiService } from '../services/api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { 
  Folder, 
  File, 
  FileText, 
  Image as ImageIcon, 
  Video, 
  Music, 
  FileArchive, 
  BarChart, 
  Terminal,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Search,
  CheckSquare,
  AlertTriangle,
  Play,
  Download,
  AlertCircle,
  HelpCircle,
  FolderOpen,
  Box
} from 'lucide-react';

export const Dropbox = () => {
  const { dbxAccessToken, setDbxAccessToken, logoutDropbox } = useAuth();
  const { addToast } = useNotification();

  // Auth local states
  const [authUrl, setAuthUrl] = useState('');
  const [authState, setAuthState] = useState('');
  const [authCode, setAuthCode] = useState('');
  const [loadingAuth, setLoadingAuth] = useState(false);
  const [loadingCallback, setLoadingCallback] = useState(false);

  // File explorer states
  const [files, setFiles] = useState([]);
  const [currentPath, setCurrentPath] = useState('');
  const [pathHistory, setPathHistory] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  
  // Image preview cache to prevent refetching multiple times
  const [imagePreviews, setImagePreviews] = useState({});

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingSearch, setLoadingSearch] = useState(false);

  // Filter states
  const [filterType, setFilterType] = useState('Tout');
  const [filterName, setFilterName] = useState('');

  // Asset auto-check report states
  const [report, setReport] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [reportFilterStatus, setReportFilterStatus] = useState('Tout');
  const [reportFilterCat, setReportFilterCat] = useState('Tout');

  // Trigger login OAuth
  const handleConnect = async () => {
    setLoadingAuth(true);
    try {
      const data = await apiService.getDropboxAuthUrl();
      setAuthUrl(data.auth_url);
      setAuthState(data.state);
      addToast('URL d\'authentification générée ! Veuillez suivre les instructions.', 'info');
    } catch (err) {
      console.error(err);
      addToast('Impossible de se connecter à l\'API Dropbox', 'error');
    } finally {
      setLoadingAuth(false);
    }
  };

  // Submit Callback Code
  const handleVerifyCode = async () => {
    if (!authCode.trim()) {
      addToast('Veuillez entrer le code d\'autorisation', 'warning');
      return;
    }

    setLoadingCallback(true);
    try {
      const data = await apiService.callbackDropbox(authCode.trim(), authState);
      setDbxAccessToken(data.access_token);
      addToast('Connecté à Dropbox avec succès !', 'success');
      // Load root files immediately
      loadFiles('', data.access_token);
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || 'Code d\'authentification invalide';
      addToast(msg, 'error');
    } finally {
      setLoadingCallback(false);
    }
  };

  // Load Folder Files
  const loadFiles = async (path, token = dbxAccessToken) => {
    if (!token) return;
    setLoadingFiles(true);
    try {
      const data = await apiService.listDropboxFiles(token, path);
      setFiles(data.files || []);
      setCurrentPath(path);
      // Reset report and searches when moving between folders
      setReport(null);
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || 'Impossible de lister les fichiers';
      addToast(msg, 'error');
    } finally {
      setLoadingFiles(false);
    }
  };

  // Search Files
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      addToast('Veuillez entrer une requête de recherche', 'warning');
      return;
    }
    setLoadingSearch(true);
    try {
      const data = await apiService.searchDropboxFiles(dbxAccessToken, searchQuery.trim());
      setFiles(data.files || []);
      addToast(`${data.total || 0} résultat(s) trouvé(s) pour « ${searchQuery} »`, 'info');
    } catch (err) {
      console.error(err);
      addToast('Erreur lors de la recherche des fichiers', 'error');
    } finally {
      setLoadingSearch(false);
    }
  };

  // Auto Check Assets
  const handleAutoCheck = async () => {
    setLoadingReport(true);
    try {
      const data = await apiService.checkDropboxAssets(dbxAccessToken, currentPath);
      setReport(data);
      addToast('Analyse des assets terminée avec succès !', 'success');
    } catch (err) {
      console.error(err);
      addToast('Erreur lors de l\'analyse automatique des assets', 'error');
    } finally {
      setLoadingReport(false);
    }
  };

  // Download File
  const handleDownload = async (path, name) => {
    addToast(`Téléchargement de ${name}...`, 'info');
    try {
      const blob = await apiService.downloadDropboxFile(dbxAccessToken, path);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      addToast('Erreur lors du téléchargement du fichier', 'error');
    }
  };

  // Fetch Image Preview URL
  const fetchImagePreview = async (path) => {
    if (imagePreviews[path]) return;
    try {
      const blob = await apiService.downloadDropboxFile(dbxAccessToken, path);
      const url = URL.createObjectURL(blob);
      setImagePreviews(prev => ({ ...prev, [path]: url }));
    } catch (err) {
      console.error(err);
    }
  };

  // Back to parent folder
  const handleBack = () => {
    if (pathHistory.length === 0) return;
    const newHistory = [...pathHistory];
    newHistory.pop();
    setPathHistory(newHistory);
    
    // Calculate parent path
    const parts = currentPath.split('/');
    parts.pop();
    const parentPath = parts.join('/');
    loadFiles(parentPath);
  };

  // Open folder
  const handleOpenFolder = (name, path) => {
    setPathHistory(prev => [...prev, name]);
    loadFiles(path);
  };

  // File size formatter
  const formatBytes = (bytes) => {
    if (!bytes) return '—';
    const sizes = ['o', 'Ko', 'Mo', 'Go'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${parseFloat((bytes / Math.pow(1024, i)).toFixed(1))} ${sizes[i]}`;
  };

  // Helper icons
  const getFileIcon = (file) => {
    if (file.is_folder) return <Folder className="h-10 w-10 text-amber-400 dark:text-amber-500" />;
    const name = file.name.toLowerCase();
    if (name.endsWith('.pdf')) return <FileText className="h-10 w-10 text-rose-500" />;
    if (name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.webp') || name.endsWith('.gif')) {
      return <ImageIcon className="h-10 w-10 text-sky-500" />;
    }
    if (name.endsWith('.mp4') || name.endsWith('.mov')) return <Video className="h-10 w-10 text-indigo-500" />;
    if (name.endsWith('.mp3') || name.endsWith('.wav')) return <Music className="h-10 w-10 text-violet-500" />;
    if (name.endsWith('.zip') || name.endsWith('.tar') || name.endsWith('.gz')) return <FileArchive className="h-10 w-10 text-amber-600" />;
    if (name.endsWith('.xlsx') || name.endsWith('.xls') || name.endsWith('.csv')) return <BarChart className="h-10 w-10 text-emerald-500" />;
    return <File className="h-10 w-10 text-slate-400" />;
  };

  // Automatically fetch previews for images in file view
  useEffect(() => {
    if (files.length > 0 && dbxAccessToken) {
      const imageExts = ['.png', '.jpg', '.jpeg', '.webp', '.gif'];
      files.forEach(f => {
        if (!f.is_folder && imageExts.some(ext => f.name.toLowerCase().endsWith(ext))) {
          fetchImagePreview(f.path);
        }
      });
    }
  }, [files]);

  // Load root files on mount if token is ready
  useEffect(() => {
    if (dbxAccessToken && files.length === 0) {
      loadFiles('');
    }
  }, [dbxAccessToken]);

  // Render auth screen if no token
  if (!dbxAccessToken) {
    return (
      <Card className="max-w-2xl mx-auto border-border/80">
        <CardHeader>
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 mb-3">
            <Box className="h-6 w-6" />
          </div>
          <CardTitle>Connexion Dropbox</CardTitle>
          <CardDescription>
            Associez votre compte Dropbox pour parcourir les dossiers partagés clients, télécharger les images de référence et effectuer des audits d'assets.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {!authUrl ? (
            <div className="flex flex-col items-center py-6 text-center">
              <Button onClick={handleConnect} loading={loadingAuth} size="lg">
                Se connecter à Dropbox
              </Button>
              <p className="text-xs text-muted-foreground mt-3">
                Vous serez redirigé vers l'authentification officielle Dropbox pour récupérer votre code temporaire.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-4 bg-muted/20 border border-border/60 rounded-xl space-y-2">
                <h4 className="text-sm font-bold text-foreground">Étape de connexion :</h4>
                <ol className="text-xs text-muted-foreground list-decimal pl-4 space-y-1.5 leading-relaxed">
                  <li>
                    <a 
                      href={authUrl} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary hover:underline font-semibold inline-flex items-center gap-0.5"
                    >
                      Cliquez ici pour autoriser l'accès Dropbox
                      <HelpCircle className="h-3 w-3 inline" />
                    </a>
                  </li>
                  <li>Connectez-vous et autorisez l'application.</li>
                  <li>Copiez le code d'autorisation affiché à l'écran.</li>
                  <li>Collez le code dans le champ de saisie ci-dessous.</li>
                </ol>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 items-end">
                <div className="flex-1">
                  <Input
                    id="dbx-code"
                    label="Code d'autorisation Dropbox"
                    placeholder="Entrez le code d'accès (ex: sl.AbCd...)"
                    value={authCode}
                    onChange={(e) => setAuthCode(e.target.value)}
                  />
                </div>
                <Button 
                  onClick={handleVerifyCode} 
                  loading={loadingCallback}
                  className="w-full sm:w-auto shrink-0"
                >
                  Valider
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Filtered files list
  const filteredFiles = files.filter(f => {
    // Type filter
    if (filterType === 'Dossiers' && !f.is_folder) return false;
    if (filterType === 'Fichiers' && f.is_folder) return false;
    
    // Name filter
    if (filterName.trim() && !f.name.toLowerCase().includes(filterName.toLowerCase())) return false;
    
    return true;
  });

  // Filtered assets report list
  const getFilteredAssets = () => {
    if (!report || !report.assets) return [];
    return report.assets.filter(a => {
      // Status filter
      if (reportFilterStatus === '✅ Validés' && a.status !== 'ok') return false;
      if (reportFilterStatus === '⚠️ Attention' && a.status !== 'warning') return false;
      if (reportFilterStatus === '⛔ Bloqués' && a.status !== 'error') return false;
      if (reportFilterStatus === '❓ À classer' && !a.needs_manual) return false;

      // Category filter
      if (reportFilterCat !== 'Tout' && a.category !== reportFilterCat) return false;

      return true;
    });
  };

  const handleUpdateCategory = (path, newCat) => {
    if (!report) return;
    setReport(prev => {
      const updated = prev.assets.map(a => {
        if (a.path === path) {
          return {
            ...a,
            category: newCat,
            needs_manual: false,
            badge: '⚡',
            label: 'Manuel',
            issues: [],
            suggestions: [],
            status: 'ok'
          };
        }
        return a;
      });
      
      // Re-calculate metrics
      const total = updated.length;
      const ok = updated.filter(a => a.status === 'ok').length;
      const warnings = updated.filter(a => a.status === 'warning').length;
      const errors = updated.filter(a => a.status === 'error').length;
      const needs_manual = updated.filter(a => a.needs_manual).length;

      return { ...prev, assets: updated, total, ok, warnings, errors, needs_manual };
    });
    addToast('Catégorie mise à jour avec succès', 'success');
  };

  return (
    <div className="space-y-6">
      {/* File Explorer Search Panel */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-4 space-y-0">
          <div>
            <CardTitle>Explorateur de Fichiers</CardTitle>
            <CardDescription>
              Naviguez et gérez les ressources directement stockées sur Dropbox.
            </CardDescription>
          </div>
          <Button onClick={logoutDropbox} variant="secondary" size="sm">
            <LogOut className="h-4 w-4 mr-2" />
            Déconnecter
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Path Header / Breadcrumbs */}
          <div className="p-3.5 bg-secondary/60 rounded-xl border border-border/60 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground font-semibold select-none">
            <span onClick={() => loadFiles('')} className="cursor-pointer hover:text-foreground">🏠 Racine</span>
            {pathHistory.map((folder, index) => (
              <React.Fragment key={index}>
                <span>›</span>
                <span 
                  onClick={() => {
                    const truncatedHistory = pathHistory.slice(0, index + 1);
                    setPathHistory(truncatedHistory);
                    const calculatedPath = '/' + truncatedHistory.join('/');
                    loadFiles(calculatedPath);
                  }}
                  className="cursor-pointer hover:text-foreground truncate max-w-[120px]"
                >
                  {folder}
                </span>
              </React.Fragment>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 flex flex-col sm:flex-row gap-2">
              <Input
                id="dbx-path"
                placeholder="Entrez un chemin de dossier (ex: /Projet/Assets)"
                value={currentPath}
                onChange={(e) => setCurrentPath(e.target.value)}
                className="flex-1"
              />
              <div className="flex gap-2 w-full sm:w-auto shrink-0">
                <Button 
                  onClick={() => loadFiles(currentPath)} 
                  loading={loadingFiles}
                  variant="outline"
                  className="flex-1 sm:flex-none"
                >
                  <FolderOpen className="h-4 w-4 mr-2" />
                  Lister
                </Button>
                <Button 
                  onClick={handleAutoCheck} 
                  loading={loadingReport}
                  className="flex-1 sm:flex-none"
                >
                  <CheckSquare className="h-4 w-4 mr-2" />
                  Auto-check
                </Button>
                {pathHistory.length > 0 && (
                  <Button 
                    onClick={handleBack} 
                    variant="outline"
                    className="shrink-0"
                    title="Dossier parent"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>

            {/* Search Input */}
            <div className="flex gap-2">
              <Input
                id="dbx-search"
                placeholder="Rechercher sur Dropbox..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
              />
              <Button onClick={handleSearch} loading={loadingSearch} variant="secondary" className="shrink-0">
                <Search className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Auto Check Report Box */}
      {report && (
        <Card className="border-indigo-500/20 bg-indigo-50/5 dark:bg-indigo-950/5 animate-fade-in">
          <CardHeader>
            <CardTitle className="text-indigo-600 dark:text-indigo-400 flex items-center gap-2">
              <CheckSquare className="h-5 w-5" />
              Rapport Auto-check Assets
            </CardTitle>
            <CardDescription>Analyse critique des assets graphiques du dossier.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Report Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
              <div className="p-4 border border-border/80 bg-card rounded-xl text-center">
                <p className="text-xs font-bold text-muted-foreground uppercase select-none">Total Assets</p>
                <h4 className="text-2xl font-black text-foreground mt-1">{report.total}</h4>
              </div>
              <div className="p-4 border border-border/80 bg-card rounded-xl text-center">
                <p className="text-xs font-bold text-emerald-500 uppercase select-none">✅ Validés</p>
                <h4 className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">{report.ok}</h4>
              </div>
              <div className="p-4 border border-border/80 bg-card rounded-xl text-center">
                <p className="text-xs font-bold text-amber-500 uppercase select-none">⚠️ Attention</p>
                <h4 className="text-2xl font-black text-amber-600 dark:text-amber-400 mt-1">{report.warnings}</h4>
              </div>
              <div className="p-4 border border-border/80 bg-card rounded-xl text-center">
                <p className="text-xs font-bold text-rose-500 uppercase select-none">⛔ Bloqués</p>
                <h4 className="text-2xl font-black text-rose-600 dark:text-rose-400 mt-1">{report.errors}</h4>
              </div>
              <div className="p-4 border border-border/80 bg-card rounded-xl text-center col-span-2 md:col-span-1">
                <p className="text-xs font-bold text-blue-500 uppercase select-none">❓ À classer</p>
                <h4 className="text-2xl font-black text-blue-600 dark:text-blue-400 mt-1">{report.needs_manual}</h4>
              </div>
            </div>

            {/* Filter settings */}
            <div className="flex flex-col sm:flex-row gap-4 border-t border-border/40 pt-4">
              <div className="flex-1 space-y-1">
                <label className="text-xs font-bold text-muted-foreground select-none uppercase tracking-wide">Filtrer par Statut</label>
                <select
                  value={reportFilterStatus}
                  onChange={(e) => setReportFilterStatus(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-input bg-card text-foreground text-sm"
                >
                  <option>Tout</option>
                  <option>✅ Validés</option>
                  <option>⚠️ Attention</option>
                  <option>⛔ Bloqués</option>
                  <option>❓ À classer</option>
                </select>
              </div>

              <div className="flex-1 space-y-1">
                <label className="text-xs font-bold text-muted-foreground select-none uppercase tracking-wide">Filtrer par Catégorie</label>
                <select
                  value={reportFilterCat}
                  onChange={(e) => setReportFilterCat(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-input bg-card text-foreground text-sm"
                >
                  <option>Tout</option>
                  <option>logo</option>
                  <option>icon</option>
                  <option>image</option>
                  <option>banner</option>
                  <option>video</option>
                  <option>svg</option>
                  <option>doc</option>
                  <option>unknown</option>
                </select>
              </div>
            </div>

            {/* Report entries list */}
            <div className="space-y-4 border-t border-border/40 pt-4">
              {getFilteredAssets().length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">Aucun asset correspondant aux filtres.</p>
              ) : (
                getFilteredAssets().map((asset, index) => (
                  <div 
                    key={index}
                    className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4 rounded-xl border border-border/60 bg-card hover:shadow-sm transition-all"
                  >
                    <div className="flex items-center gap-3.5 min-w-0">
                      <div className="text-2xl font-black select-none shrink-0">{asset.badge}</div>
                      <div className="min-w-0">
                        <p className="text-sm font-bold text-foreground truncate max-w-xs md:max-w-md">{asset.name}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {asset.category} — {asset.extension} — {formatBytes(asset.size)} — {asset.dimensions ? `${asset.dimensions[0]}x${asset.dimensions[1]}px` : 'No dims'}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-col md:items-end gap-1.5 w-full md:w-auto">
                      {asset.needs_manual ? (
                        <div className="flex items-center gap-2 w-full md:w-auto">
                          <select
                            defaultValue="logo"
                            id={`override-${index}`}
                            className="px-2.5 py-1.5 text-xs border border-input bg-card rounded-lg"
                          >
                            <option value="logo">logo</option>
                            <option value="icon">icon</option>
                            <option value="image">image</option>
                            <option value="banner">banner</option>
                            <option value="video">video</option>
                            <option value="doc">doc</option>
                          </select>
                          <Button 
                            onClick={() => {
                              const select = document.getElementById(`override-${index}`);
                              handleUpdateCategory(asset.path, select.value);
                            }} 
                            size="sm"
                          >
                            Confirmer
                          </Button>
                        </div>
                      ) : (
                        <>
                          {asset.issues && asset.issues.length > 0 ? (
                            <div className="space-y-1 max-w-xs text-left md:text-right">
                              {asset.issues.map((issue, idx) => (
                                <p key={idx} className="text-xs text-amber-500 font-bold flex items-center md:justify-end gap-1 select-none">
                                  <AlertTriangle className="h-3 w-3 shrink-0" />
                                  {issue}
                                </p>
                              ))}
                              {asset.suggestions && asset.suggestions.map((sug, idx) => (
                                <p key={idx} className="text-[10px] text-muted-foreground select-none">
                                  💡 {sug}
                                </p>
                              ))}
                            </div>
                          ) : (
                            <Badge variant="success">Conforme</Badge>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Files Grid View */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2">
            <div>
              <CardTitle>Fichiers ({filteredFiles.length})</CardTitle>
              <CardDescription>Visualisation en temps réel du contenu du dossier.</CardDescription>
            </div>

            {/* In-view filters */}
            <div className="flex flex-col sm:flex-row gap-2 shrink-0">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-lg border border-input bg-card text-foreground"
              >
                <option>Tout</option>
                <option>Dossiers</option>
                <option>Fichiers</option>
              </select>
              <Input
                id="inline-search"
                placeholder="Filtrer par nom..."
                value={filterName}
                onChange={(e) => setFilterName(e.target.value)}
                className="px-3 py-1 text-xs max-w-44"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loadingFiles ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, idx) => (
                <div key={idx} className="border border-border rounded-xl p-4 space-y-3 bg-card animate-pulse">
                  <div className="h-32 bg-muted/60 rounded-lg" />
                  <div className="h-4 w-3/4 bg-muted/60 rounded" />
                  <div className="h-3 w-1/2 bg-muted/60 rounded" />
                </div>
              ))}
            </div>
          ) : filteredFiles.length === 0 ? (
            <div className="text-center py-12">
              <Folder className="h-12 w-12 text-muted-foreground/30 mx-auto mb-3" />
              <h4 className="text-sm font-bold text-foreground">Dossier vide</h4>
              <p className="text-xs text-muted-foreground mt-1">Aucun fichier trouvé ou ne correspond aux filtres.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              {filteredFiles.map((file, index) => {
                const isImage = imagePreviews[file.path];
                
                return (
                  <Card key={index} className="overflow-hidden flex flex-col h-full hover:border-primary/20 group">
                    {/* Media preview/Icon box */}
                    <div className="h-36 bg-secondary/30 flex items-center justify-center border-b border-border/40 relative overflow-hidden shrink-0">
                      {isImage ? (
                        <img 
                          src={imagePreviews[file.path]} 
                          alt={file.name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        getFileIcon(file)
                      )}
                    </div>

                    {/* File metadata */}
                    <div className="p-4 flex-1 flex flex-col justify-between gap-3 min-w-0">
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-foreground truncate" title={file.name}>
                          {file.name}
                        </p>
                        <p className="text-[10px] text-muted-foreground mt-1">
                          {file.is_folder ? 'Dossier' : `${formatBytes(file.size)} • ${file.modified ? file.modified.substring(0, 10) : '—'}`}
                        </p>
                      </div>

                      {/* Operations */}
                      {file.is_folder ? (
                        <Button 
                          onClick={() => handleOpenFolder(file.name, file.path)}
                          variant="secondary"
                          size="sm"
                          className="w-full"
                        >
                          Ouvrir
                        </Button>
                      ) : (
                        <Button 
                          onClick={() => handleDownload(file.path, file.name)}
                          variant="outline"
                          size="sm"
                          className="w-full"
                        >
                          <Download className="h-3.5 w-3.5 mr-1.5" />
                          Télécharger
                        </Button>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Dropbox;
