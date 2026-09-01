import React, { useState } from 'react';
import useLocalState from '../hooks/useLocalState';
import { useNotification } from '../hooks/useNotification';
import { apiService } from '../services/api';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { 
  Brush, 
  Upload, 
  Trash2, 
  Copy, 
  Type, 
  Maximize2, 
  Sparkles, 
  ChevronDown, 
  ChevronUp, 
  FileCode,
  Sliders,
  Focus
} from 'lucide-react';

export const StyleExtractor = () => {
  const { addToast } = useNotification();
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [styleResult, setStyleResult] = useLocalState('se_styleResult', null);
  
  const [expandRefs, setExpandRefs] = useState(false);
  const [expandRaw, setExpandRaw] = useState(false);

  const handleFileChange = (e) => {
    const filesList = Array.from(e.target.files);
    
    // Validate image format
    const validFiles = filesList.filter(file => {
      const type = file.type;
      return type === 'image/png' || type === 'image/jpeg' || type === 'image/jpg' || type === 'image/webp';
    });

    if (validFiles.length !== filesList.length) {
      addToast('Certains fichiers ont été rejetés. Seuls PNG, JPG, JPEG et WEBP sont acceptés.', 'warning');
    }

    if (uploadedFiles.length + validFiles.length > 5) {
      addToast('Vous pouvez charger un maximum de 5 images.', 'warning');
      return;
    }

    setUploadedFiles(prev => [...prev, ...validFiles]);
  };

  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleExtract = async () => {
    if (uploadedFiles.length < 1) {
      addToast('Ajoutez au moins 1 image pour lancer l\'extraction', 'warning');
      return;
    }

    setLoading(true);
    try {
      const data = await apiService.extractStyle(uploadedFiles);
      setStyleResult(data);
      addToast('Style extrait avec succès !', 'success');
      setExpandRefs(true);
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || 'Erreur lors de l\'extraction du style visuel';
      addToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    addToast(`Copié : ${text}`, 'success', 2000);
  };

  return (
    <div className="space-y-6">
      {/* File Uploader Card */}
      <Card>
        <CardHeader>
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary mb-3">
            <Brush className="h-6 w-6" />
          </div>
          <CardTitle>Extraction de Style Visuel</CardTitle>
          <CardDescription>
            Importez de 2 à 5 captures d'écran de référence. L'agent IA analysera les couleurs dominantes, la typographie, la densité de l'UI et le style graphique.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Custom Drag & Drop Field */}
          <div className="border-2 border-dashed border-border/80 hover:border-primary/50 transition-colors rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer relative bg-secondary/10">
            <input 
              type="file" 
              multiple 
              accept=".png,.jpg,.jpeg,.webp"
              onChange={handleFileChange}
              className="absolute inset-0 opacity-0 cursor-pointer"
            />
            <Upload className="h-10 w-10 text-muted-foreground/60 mb-2.5" />
            <p className="text-sm font-bold text-foreground">Glissez-déposez des images</p>
            <p className="text-xs text-muted-foreground mt-1">PNG, JPG, JPEG, WEBP (Max 5 fichiers)</p>
          </div>

          {/* Uploaded files listing */}
          {uploadedFiles.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-muted-foreground uppercase select-none">Images Chargées ({uploadedFiles.length})</h4>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                {uploadedFiles.map((file, index) => {
                  const url = URL.createObjectURL(file);
                  return (
                    <div key={index} className="relative rounded-xl border border-border overflow-hidden h-24 bg-secondary">
                      <img 
                        src={url} 
                        alt={file.name} 
                        className="w-full h-full object-cover"
                      />
                      <button
                        onClick={() => removeFile(index)}
                        className="absolute top-1.5 right-1.5 p-1 bg-black/60 hover:bg-rose-600 rounded-lg text-white transition-colors"
                        title="Supprimer"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {uploadedFiles.length < 2 && uploadedFiles.length > 0 && (
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 rounded-xl text-xs font-semibold select-none">
              ⚠️ Ajoutez au moins <strong>2 images</strong> pour obtenir de meilleurs résultats d'analyse comparative.
            </div>
          )}

          {/* Action button */}
          <Button
            onClick={handleExtract}
            loading={loading}
            disabled={uploadedFiles.length === 0}
            className="w-full py-4"
          >
            ✦ Extraire le style
          </Button>

          {/* Reset button */}
          {styleResult && (
            <Button
              variant="secondary"
              onClick={() => setStyleResult(null)}
              className="w-full text-destructive hover:bg-destructive/10 border border-destructive/20"
            >
              ↺ Effacer les résultats
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {styleResult && (
        <div className="space-y-6 animate-fade-in">
          {/* Main Color Swatches Card */}
          <Card>
            <CardHeader>
              <CardTitle>Palette de Couleurs Extraite</CardTitle>
              <CardDescription>Couleurs dominantes détectées sur l'ensemble des références. Cliquez pour copier le code Hex.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                {styleResult.palette?.map((hex, index) => (
                  <div 
                    key={index}
                    onClick={() => copyToClipboard(hex)}
                    className="group border border-border/80 bg-card rounded-2xl overflow-hidden cursor-pointer hover:shadow-md transition-all active:scale-[0.98]"
                  >
                    <div className="h-16 w-full transition-transform duration-200 group-hover:brightness-95" style={{ backgroundColor: hex }} />
                    <div className="p-3 flex items-center justify-between gap-1">
                      <span className="text-xs font-mono font-bold text-muted-foreground select-none">{hex}</span>
                      <Copy className="h-3 w-3 text-muted-foreground/40 group-hover:text-foreground shrink-0" />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Style Properties Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <Card className="p-5 flex items-center gap-4">
              <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                <Type className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest select-none">Typographie</p>
                <h4 className="text-sm font-black text-foreground truncate mt-0.5">{styleResult.typography?.style || '—'}</h4>
              </div>
            </Card>

            <Card className="p-5 flex items-center gap-4">
              <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                <Maximize2 className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest select-none">Densité UI</p>
                <h4 className="text-sm font-black text-foreground truncate mt-0.5">{styleResult.density || '—'}</h4>
              </div>
            </Card>

            <Card className="p-5 flex items-center gap-4">
              <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                <Focus className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest select-none">Style Visuel</p>
                <h4 className="text-sm font-black text-foreground truncate mt-0.5">{styleResult.visual_style || '—'}</h4>
              </div>
            </Card>

            <Card className="p-5 flex items-center gap-4">
              <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0">
                <Sliders className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest select-none">Contraste Typo</p>
                <h4 className="text-sm font-black text-foreground truncate mt-0.5">{styleResult.typography?.contrast || '—'}</h4>
              </div>
            </Card>
          </div>

          {/* Dominant Mood Alert */}
          {styleResult.dominant_mood && (
            <div className="p-4 bg-primary/5 border border-primary/20 rounded-2xl flex items-center gap-3">
              <Sparkles className="h-5 w-5 text-primary shrink-0" />
              <p className="text-sm font-semibold text-foreground">
                ✦ Ambiance dominante : <span className="font-bold text-primary">{styleResult.dominant_mood}</span>
              </p>
            </div>
          )}

          {/* Detail per Reference Accordion */}
          <div className="border border-border/60 rounded-xl bg-card overflow-hidden">
            <button
              onClick={() => setExpandRefs(!expandRefs)}
              className="w-full flex items-center justify-between p-4 hover:bg-secondary/20 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Brush className="h-4.5 w-4.5 text-muted-foreground" />
                <span className="text-sm font-bold text-foreground">Détail analytique par référence</span>
              </div>
              {expandRefs ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
            </button>
            {expandRefs && (
              <div className="p-4 border-t border-border/40 bg-muted/10 space-y-4">
                {styleResult.styles_per_ref?.map((ref, idx) => (
                  <div key={idx} className="p-4 rounded-xl border border-border bg-card space-y-3">
                    <h5 className="text-sm font-extrabold text-foreground">Référence {idx + 1}</h5>
                    
                    {/* Swatches list */}
                    {ref.colors && (
                      <div className="flex flex-wrap gap-1.5">
                        {ref.colors.map((c, cidx) => (
                          <div 
                            key={cidx} 
                            onClick={() => copyToClipboard(c)}
                            className="h-6 w-6 rounded-md border border-black/10 cursor-pointer shadow-sm hover:scale-105 transition-all"
                            style={{ backgroundColor: c }}
                            title={`Copier : ${c}`}
                          />
                        ))}
                      </div>
                    )}
                    
                    <p className="text-xs text-muted-foreground">
                      Densité : <span className="font-bold text-foreground">{ref.density || '—'}</span> &nbsp;|&nbsp; 
                      Style : <span className="font-bold text-foreground">{ref.visual_style || '—'}</span> &nbsp;|&nbsp; 
                      Ambiance : <span className="font-bold text-foreground">*{ref.dominant_mood || '—'}*</span>
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Raw JSON expander */}
          <div className="border border-border/60 rounded-xl bg-card overflow-hidden">
            <button
              onClick={() => setExpandRaw(!expandRaw)}
              className="w-full flex items-center justify-between p-4 hover:bg-secondary/20 transition-colors"
            >
              <div className="flex items-center gap-2">
                <FileCode className="h-4.5 w-4.5 text-muted-foreground" />
                <span className="text-sm font-bold text-foreground">Données JSON brutes</span>
              </div>
              {expandRaw ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
            </button>
            {expandRaw && (
              <div className="p-4 border-t border-border/40 bg-muted/10">
                <pre className="text-xs font-mono bg-secondary/40 p-3 rounded-lg overflow-x-auto text-muted-foreground max-h-60">
                  {JSON.stringify(styleResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default StyleExtractor;
