import React, { useState, useEffect } from 'react';
import { useNotification } from '../hooks/useNotification';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { 
  FolderSymlink, 
  ExternalLink, 
  RefreshCw, 
  ListOrdered, 
  CheckCircle, 
  BellRing,
  FolderMinus,
  Code
} from 'lucide-react';

export const SharedFolder = () => {
  const { addToast } = useNotification();
  const [driveUrl, setDriveUrl] = useState(() => {
    return localStorage.getItem('dp_explorer_drive_url') || '';
  });

  useEffect(() => {
    localStorage.setItem('dp_explorer_drive_url', driveUrl);
  }, [driveUrl]);

  const handleOpen = () => {
    if (!driveUrl.trim()) {
      addToast('Veuillez entrer le lien du dossier partagé d\'abord', 'warning');
      return;
    }
    
    // Check if valid URL structure
    try {
      new URL(driveUrl.trim());
      window.open(driveUrl.trim(), '_blank', 'noopener,noreferrer');
      addToast('Ouverture du dossier partagé...', 'info');
    } catch (_) {
      addToast('URL invalide. Assurez-vous d\'inclure http:// ou https://', 'error');
    }
  };

  const upcomingFeatures = [
    {
      title: 'Synchronisation automatique',
      description: 'Liaison directe avec le cloud client pour repérer en continu les modifications.',
      icon: RefreshCw,
      progress: 80,
    },
    {
      title: 'Liste intégrée des fichiers',
      description: 'Consultation et recherche des ressources directement depuis cette interface.',
      icon: ListOrdered,
      progress: 40,
    },
    {
      title: 'Statut de validation des assets',
      description: 'Vérification de la conformité en arrière-plan sans action manuelle requise.',
      icon: CheckCircle,
      progress: 20,
    },
    {
      title: 'Alertes et notifications',
      description: 'Notification push lors de l\'ajout ou de la suppression d\'éléments importants.',
      icon: BellRing,
      progress: 0,
    }
  ];

  return (
    <div className="space-y-6">
      {/* Configuration Card */}
      <Card>
        <CardHeader>
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary mb-3">
            <FolderSymlink className="h-6 w-6" />
          </div>
          <CardTitle>Dossier Partagé Client</CardTitle>
          <CardDescription>
            Renseignez le lien vers le dossier de stockage du client (Google Drive, OneDrive, etc.) pour y accéder rapidement.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row items-end gap-3">
            <div className="flex-1">
              <Input
                id="drive-url"
                label="Lien du dossier cloud"
                placeholder="https://drive.google.com/drive/folders/..."
                value={driveUrl}
                onChange={(e) => setDriveUrl(e.target.value)}
              />
            </div>
            <Button onClick={handleOpen} className="shrink-0 w-full sm:w-auto">
              <ExternalLink className="h-4 w-4 mr-2" />
              Ouvrir le dossier
            </Button>
          </div>

          {driveUrl.trim() && (
            <div className="p-4 border border-border/80 bg-secondary/30 rounded-xl flex items-center justify-between gap-4 animate-fade-in">
              <div className="flex items-center gap-3.5 min-w-0">
                <div className="h-10 w-10 rounded-xl bg-card border border-border/80 flex items-center justify-center text-primary shrink-0 font-extrabold select-none">
                  📁
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-bold text-foreground truncate">Dossier client configuré</p>
                  <a 
                    href={driveUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-xs text-primary hover:underline truncate block max-w-xs sm:max-w-md mt-0.5"
                  >
                    {driveUrl}
                  </a>
                </div>
              </div>
              <Badge variant="success">Actif</Badge>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Roadmap Card */}
      <Card>
        <CardHeader>
          <CardTitle>Fonctionnalités à venir</CardTitle>
          <CardDescription>Découvrez les développements programmés pour simplifier le transfert de fichiers.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {upcomingFeatures.map((feat, index) => {
              const Icon = feat.icon;
              return (
                <div 
                  key={index}
                  className="p-5 rounded-2xl border border-border/60 bg-card/60 flex gap-4 hover:border-primary/20 transition-all group"
                >
                  <div className="h-10 w-10 rounded-xl bg-secondary flex items-center justify-center text-muted-foreground group-hover:text-primary transition-colors shrink-0">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-bold text-foreground">{feat.title}</h4>
                      {feat.progress > 0 ? (
                        <span className="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full select-none">
                          {feat.progress}%
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold text-muted-foreground bg-secondary px-2 py-0.5 rounded-full select-none">
                          Backlog
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{feat.description}</p>
                    
                    {/* Tiny progress bar */}
                    {feat.progress > 0 && (
                      <div className="w-full h-1 bg-secondary rounded-full overflow-hidden mt-1.5">
                        <div 
                          className="h-full bg-primary rounded-full transition-all"
                          style={{ width: `${feat.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SharedFolder;
