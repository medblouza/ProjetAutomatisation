import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotification } from '../hooks/useNotification';
import { apiService } from '../services/api';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { 
  Palette, 
  Sparkles, 
  HelpCircle, 
  Layers, 
  Layout, 
  Download,
  RotateCcw,
  CheckCircle,
  FileCode,
  AlertTriangle,
  ChevronUp,
  ChevronDown
} from 'lucide-react';

export const Wireframe = () => {
  const { cleanedData } = useAuth();
  const { addToast } = useNotification();

  // Local states
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');
  const [lastWireframe, setLastWireframe] = useState(() => {
    const saved = localStorage.getItem('dp_explorer_last_wireframe');
    return saved ? JSON.parse(saved) : null;
  });

  const [expandSitemap, setExpandSitemap] = useState(true);
  const [expandStructure, setExpandStructure] = useState(false);

  // Sync wireframe with localStorage to persist between tabs
  useEffect(() => {
    if (lastWireframe) {
      localStorage.setItem('dp_explorer_last_wireframe', JSON.stringify(lastWireframe));
    } else {
      localStorage.removeItem('dp_explorer_last_wireframe');
    }
  }, [lastWireframe]);

  if (!cleanedData) {
    return (
      <Card className="max-w-2xl mx-auto border-border/80">
        <CardContent className="flex flex-col items-center justify-center text-center py-16">
          <div className="h-16 w-16 rounded-2xl bg-secondary/80 flex items-center justify-center text-muted-foreground/60 mb-4 animate-pulse">
            <Layout className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-bold text-foreground">Données manquantes</h3>
          <p className="text-sm text-muted-foreground mt-2 max-w-sm leading-relaxed">
            Pour générer le wireframe, veuillez d'abord récupérer les informations client et exécuter l'action 
            <strong className="text-primary font-semibold select-none"> Nettoyer données</strong> dans l'onglet 📊 
            <span className="font-semibold text-foreground">DP Explorer</span>.
          </p>
        </CardContent>
      </Card>
    );
  }

  const branding = cleanedData.branding || {};
  const colors = branding.colors || [];
  const styles = branding.style || [];
  const pages = cleanedData.pages || [];

  const handleGenerate = async () => {
    setLoading(true);
    setProgress(0);
    setStatusText('Initialisation du générateur...');

    const n = pages.length;
    if (n === 0) {
      addToast('Aucune page détectée dans les données nettoyées.', 'error');
      setLoading(false);
      return;
    }

    try {
      // Simulate frontend preparation phases
      for (let i = 0; i < n; i++) {
        const pct = Math.floor((i / n) * 60) + 10;
        setProgress(pct);
        setStatusText(`🤖 Analyse structurelle de « ${pages[i].name} »... (${i + 1}/${n})`);
        await new Promise(r => setTimeout(r, 400));
      }

      setProgress(75);
      setStatusText('📐 Assemblage et finalisation de la structure...');
      await new Promise(r => setTimeout(r, 600));

      setProgress(85);
      setStatusText('🎨 Envoi des spécifications à l\'IA...');
      
      // Make real API call
      const result = await apiService.generateWireframe(cleanedData);

      setProgress(95);
      setStatusText('💅 Finalisation du code HTML...');
      await new Promise(r => setTimeout(r, 500));

      setProgress(100);
      setStatusText('✅ Wireframe généré avec succès !');
      
      setLastWireframe(result);
      addToast(`Le projet « ${result.project_name} » a été généré (${result.pages_count} pages).`, 'success');
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || 'Erreur lors de la génération du wireframe. Le serveur a peut-être expiré.';
      addToast(msg, 'error');
      setProgress(0);
      setStatusText('');
    } finally {
      setLoading(false);
    }
  };

  const downloadHtml = () => {
    if (!lastWireframe) return;
    const element = document.createElement('a');
    const file = new Blob([lastWireframe.html], { type: 'text/html' });
    element.href = URL.createObjectURL(file);
    element.download = `wireframe_${lastWireframe.project_name.replace(/\s+/g, '_')}.html`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleReset = () => {
    setLastWireframe(null);
    setProgress(0);
    setStatusText('');
  };

  return (
    <div className="space-y-6">
      {/* Source Data Specs Card */}
      <Card>
        <CardHeader>
          <CardTitle>Spécifications du Projet</CardTitle>
          <CardDescription>Visualisation du profil de marque extrait du cahier des charges client.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Metadata Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl border border-border/80 bg-secondary/30">
              <p className="text-xs font-bold text-muted-foreground uppercase select-none">Client</p>
              <h4 className="text-base font-extrabold text-foreground mt-1 truncate">{cleanedData.company_name || '—'}</h4>
            </div>

            <div className="p-4 rounded-xl border border-border/80 bg-secondary/30">
              <p className="text-xs font-bold text-muted-foreground uppercase select-none">Nombre de pages</p>
              <h4 className="text-base font-extrabold text-foreground mt-1">{pages.length}</h4>
            </div>

            <div className="p-4 rounded-xl border border-border/80 bg-secondary/30">
              <p className="text-xs font-bold text-muted-foreground uppercase select-none">Style d'interface</p>
              <h4 className="text-base font-extrabold text-foreground mt-1 truncate">
                {styles.length > 0 ? styles.map(s => s.name).join(', ') : 'Standard'}
              </h4>
            </div>
          </div>

          {/* Color Palettes Swatch */}
          {colors.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-bold text-muted-foreground uppercase select-none">Palette Couleurs Détectée</p>
              <div className="flex flex-wrap gap-3">
                {colors.map((hex, index) => (
                  <div key={index} className="flex items-center gap-2 px-3 py-1.5 border border-border/80 bg-card rounded-xl shadow-sm">
                    <div 
                      className="h-5 w-5 rounded-md border border-black/10 shrink-0" 
                      style={{ backgroundColor: hex }} 
                    />
                    <span className="text-xs font-mono text-muted-foreground select-all">{hex}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sitemap Accordion */}
          <div className="border border-border/60 rounded-xl bg-card overflow-hidden">
            <button
              onClick={() => setExpandSitemap(!expandSitemap)}
              className="w-full flex items-center justify-between p-4 hover:bg-secondary/20 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Layers className="h-4.5 w-4.5 text-muted-foreground" />
                <span className="text-sm font-bold text-foreground">Sitemap Détecté ({pages.length} pages)</span>
              </div>
              {expandSitemap ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
            </button>
            {expandSitemap && (
              <div className="p-4 border-t border-border/40 bg-muted/10 divide-y divide-border/40">
                {pages.map((page, idx) => (
                  <div key={idx} className="py-2.5 first:pt-0 last:pb-0">
                    <h5 className="text-sm font-bold text-foreground">{idx + 1}. {page.name}</h5>
                    {page.content && (
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2 leading-relaxed">
                        {page.content}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action trigger button */}
          {!lastWireframe && (
            <Button 
              onClick={handleGenerate} 
              loading={loading}
              className="w-full py-6 text-sm"
              size="lg"
            >
              <Sparkles className="h-4.5 w-4.5 mr-2" />
              Générer le Wireframe
            </Button>
          )}

          {/* Progressive Loader */}
          {loading && (
            <div className="space-y-2 border border-border/80 bg-secondary/25 p-4 rounded-xl animate-pulse">
              <div className="flex items-center justify-between text-xs text-muted-foreground font-semibold">
                <span>{statusText}</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Wireframe results box */}
      {lastWireframe && (
        <div className="space-y-6 animate-fade-in">
          <Card>
            <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4">
              <div>
                <CardTitle className="text-emerald-700 dark:text-emerald-400 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Wireframe Généré
                </CardTitle>
                <CardDescription>Le wireframe est assemblé et prêt pour consultation.</CardDescription>
              </div>
              <div className="flex gap-2 w-full sm:w-auto">
                <Button onClick={downloadHtml} variant="primary" className="flex-1 sm:flex-none">
                  <Download className="h-4 w-4 mr-2" />
                  Télécharger (.html)
                </Button>
                <Button onClick={handleReset} variant="secondary" className="shrink-0">
                  <RotateCcw className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Structure Expander */}
              <div className="border border-border/60 rounded-xl bg-card overflow-hidden">
                <button
                  onClick={() => setExpandStructure(!expandStructure)}
                  className="w-full flex items-center justify-between p-4 hover:bg-secondary/20 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <FileCode className="h-4.5 w-4.5 text-muted-foreground" />
                    <span className="text-sm font-bold text-foreground">Structure HTML générée par l'agent</span>
                  </div>
                  {expandStructure ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
                </button>
                {expandStructure && (
                  <div className="p-4 border-t border-border/40 bg-muted/10 space-y-4">
                    {lastWireframe.pages?.map((page, idx) => (
                      <div key={idx} className="space-y-1.5 p-3 rounded-lg border border-border/60 bg-card">
                        <p className="text-xs font-bold text-foreground uppercase tracking-wide">📄 {page.name}</p>
                        <div className="flex flex-col gap-1 pl-4">
                          {page.sections?.map((sec, sidx) => (
                            <span key={sidx} className="text-[11px] text-muted-foreground font-mono">
                              <span className="text-primary font-bold">[{sec.type.toUpperCase()}]</span> {sec.name} ({sec.height ? `${sec.height}px` : 'auto'}) {sec.description ? `· ${sec.description}` : ''}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Interactive IFrame Mockup */}
              <div className="space-y-2">
                <h4 className="text-sm font-bold text-foreground">Aperçu interactif</h4>
                <div className="w-full border border-border rounded-2xl overflow-hidden shadow-inner bg-card h-[750px]">
                  <iframe
                    title="Wireframe Live Mockup"
                    srcDoc={lastWireframe.html}
                    className="w-full h-full bg-white text-black"
                    sandbox="allow-scripts"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Wireframe;
