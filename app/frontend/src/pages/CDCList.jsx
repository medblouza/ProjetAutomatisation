import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import { useNotification } from '../hooks/useNotification';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import {
  FileText,
  Code2,
  Calendar,
  RefreshCw,
  X,
  Download,
  Clock,
  AlertCircle,
  Plus,
  Pencil,
  Trash2,
  Eye,
  Search,
  CheckCircle,
  AlertTriangle,
  FileCode,
  Sparkles,
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────

const formatDate = (isoString) => {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    return (
      d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
      ' à ' +
      d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    );
  } catch {
    return isoString;
  }
};

const timeAgo = (isoString) => {
  if (!isoString) return '';
  try {
    const diff = Date.now() - new Date(isoString).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (minutes < 1) return "À l'instant";
    if (minutes < 60) return `il y a ${minutes} min`;
    if (hours < 24) return `il y a ${hours}h`;
    return `il y a ${days} jour${days > 1 ? 's' : ''}`;
  } catch {
    return '';
  }
};

// ─────────────────────────────────────────────────────────────
// Composant : Carte d'élément avec actions CRUD
// ─────────────────────────────────────────────────────────────

const ItemCard = ({
  id,
  icon: Icon,
  iconColor,
  label,
  title,
  subtitle,
  secondaryInfo,
  onView,
  onEdit,
  onDelete,
}) => (
  <div
    className="group flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl border border-border/60 bg-card hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 transition-all duration-200"
    id={`item-card-${label.toLowerCase()}-${id}`}
  >
    <div className="flex items-center gap-4 min-w-0 flex-1">
      <div
        className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl transition-all duration-200 ${iconColor} group-hover:scale-105`}
      >
        <Icon className="h-6 w-6" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <p className="text-sm font-bold text-foreground truncate max-w-md" title={title}>
            {title}
          </p>
          <span
            className={`shrink-0 text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
              label === 'CDC'
                ? 'bg-primary/10 text-primary border border-primary/20'
                : 'bg-violet-500/10 text-violet-600 dark:text-violet-400 border border-violet-500/20'
            }`}
          >
            {label}
          </span>
          {secondaryInfo && (
            <span className="text-[11px] text-muted-foreground font-mono bg-muted/40 px-2 py-0.5 rounded">
              {secondaryInfo}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground flex-wrap">
          <Calendar className="h-3.5 w-3.5 shrink-0" />
          <span>{formatDate(subtitle)}</span>
          <span className="text-border">·</span>
          <Clock className="h-3.5 w-3.5 shrink-0" />
          <span>{timeAgo(subtitle)}</span>
        </div>
      </div>
    </div>

    {/* Boutons d'actions */}
    <div className="flex items-center gap-1.5 self-end sm:self-center shrink-0">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onView(id)}
        className="h-8 px-2.5 text-xs font-semibold text-muted-foreground hover:text-foreground hover:bg-secondary flex items-center gap-1.5"
        title="Consulter"
        id={`view-btn-${id}`}
      >
        <Eye className="h-3.5 w-3.5 text-primary" />
        <span className="hidden sm:inline">Consulter</span>
      </Button>

      <Button
        variant="ghost"
        size="sm"
        onClick={() => onEdit(id)}
        className="h-8 px-2.5 text-xs font-semibold text-muted-foreground hover:text-foreground hover:bg-secondary flex items-center gap-1.5"
        title="Modifier"
        id={`edit-btn-${id}`}
      >
        <Pencil className="h-3.5 w-3.5 text-amber-500" />
        <span className="hidden sm:inline">Modifier</span>
      </Button>

      <Button
        variant="ghost"
        size="sm"
        onClick={() => onDelete(id, title)}
        className="h-8 px-2.5 text-xs font-semibold text-muted-foreground hover:text-rose-600 hover:bg-rose-500/10 flex items-center gap-1.5"
        title="Supprimer"
        id={`delete-btn-${id}`}
      >
        <Trash2 className="h-3.5 w-3.5 text-rose-500" />
        <span className="hidden sm:inline">Supprimer</span>
      </Button>
    </div>
  </div>
);

// ─────────────────────────────────────────────────────────────
// Composant : Modal de confirmation de suppression
// ─────────────────────────────────────────────────────────────

const DeleteConfirmModal = ({ isOpen, title, itemName, onConfirm, onCancel, loading }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md bg-card border border-border rounded-2xl shadow-2xl overflow-hidden p-6 space-y-4 animate-scale-up">
        <div className="flex items-center gap-3 text-rose-500">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-rose-500/10 shrink-0">
            <AlertTriangle className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-foreground">{title}</h3>
            <p className="text-xs text-muted-foreground">Cette action est irréversible.</p>
          </div>
        </div>

        <p className="text-sm text-foreground/80 leading-relaxed bg-muted/30 p-3 rounded-xl border border-border/40">
          Êtes-vous sûr de vouloir supprimer définitivement{' '}
          <strong className="text-foreground">« {itemName} »</strong> ?
        </p>

        <div className="flex items-center justify-end gap-2.5 pt-2">
          <Button variant="outline" size="sm" onClick={onCancel} disabled={loading}>
            Annuler
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={onConfirm}
            disabled={loading}
            className="flex items-center gap-1.5 bg-rose-600 hover:bg-rose-700 text-white"
            id="confirm-delete-btn"
          >
            <Trash2 className="h-4 w-4" />
            {loading ? 'Suppression...' : 'Supprimer définitivement'}
          </Button>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// Composant : Modal Formulaire CDC (Créer / Modifier)
// ─────────────────────────────────────────────────────────────

const CDCFormModal = ({ isOpen, cdc, onSave, onClose, loading }) => {
  const [companyName, setCompanyName] = useState('');
  const [content, setContent] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    if (cdc) {
      setCompanyName(cdc.company_name || '');
      setContent(cdc.content || '');
    } else {
      setCompanyName('');
      setContent('');
    }
    setError(null);
  }, [cdc, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!companyName.trim()) {
      setError("Le nom de l'entreprise ou code client est obligatoire.");
      return;
    }
    if (!content.trim()) {
      setError('Le contenu du Cahier des Charges ne peut pas être vide.');
      return;
    }
    onSave({ company_name: companyName.trim(), content });
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget && !loading) onClose();
      }}
    >
      <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col bg-card border border-border rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/40 shrink-0 bg-muted/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-foreground">
                {cdc?.id ? `Modifier le CDC #${cdc.id}` : 'Créer un nouveau Cahier des Charges'}
              </h2>
              <p className="text-xs text-muted-foreground">
                {cdc?.id
                  ? 'Modifiez les informations et le contenu Markdown ci-dessous'
                  : 'Renseignez les détails du nouveau cahier des charges'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-secondary transition-all"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden p-6 space-y-4">
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 text-xs font-semibold">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">
              Nom de l'entreprise / Code client <span className="text-rose-500">*</span>
            </label>
            <Input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Ex: L'ART DE NANA ou CODE-1234"
              className="w-full font-medium"
              required
              id="cdc-form-company"
            />
          </div>

          <div className="flex-1 flex flex-col min-h-[300px]">
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Contenu du CDC (Markdown) <span className="text-rose-500">*</span>
              </label>
              <span className="text-[11px] text-muted-foreground">
                {content.length} caractères · {content.split('\n').length} lignes
              </span>
            </div>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="# 1. Présentation de l'entreprise&#10;...&#10;## 2. Besoins fonctionnels&#10;..."
              className="flex-1 w-full p-4 rounded-xl border border-border/80 bg-background font-mono text-xs leading-relaxed text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary resize-none"
              required
              id="cdc-form-content"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-border/40 shrink-0">
            <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={loading}>
              Annuler
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={loading}
              className="flex items-center gap-1.5"
              id="cdc-form-submit"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>Enregistrement...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="h-3.5 w-3.5" />
                  <span>{cdc?.id ? 'Enregistrer les modifications' : 'Créer le CDC'}</span>
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// Composant : Modal Formulaire DesignJSON (Créer / Modifier)
// ─────────────────────────────────────────────────────────────

const DesignJsonFormModal = ({ isOpen, record, onSave, onClose, loading }) => {
  const [companyName, setCompanyName] = useState('');
  const [filename, setFilename] = useState('design.json');
  const [content, setContent] = useState('{\n  \n}');
  const [jsonValid, setJsonValid] = useState(true);
  const [jsonErrorMsg, setJsonErrorMsg] = useState(null);

  useEffect(() => {
    if (record) {
      setCompanyName(record.company_name || '');
      setFilename(record.filename || 'design.json');
      try {
        const formatted = JSON.stringify(JSON.parse(record.content), null, 2);
        setContent(formatted);
        setJsonValid(true);
        setJsonErrorMsg(null);
      } catch {
        setContent(record.content || '');
        setJsonValid(false);
        setJsonErrorMsg('JSON invalide');
      }
    } else {
      setCompanyName('');
      setFilename('design.json');
      setContent('{\n  "pages": [],\n  "company": {}\n}');
      setJsonValid(true);
      setJsonErrorMsg(null);
    }
  }, [record, isOpen]);

  if (!isOpen) return null;

  const handleContentChange = (val) => {
    setContent(val);
    try {
      JSON.parse(val);
      setJsonValid(true);
      setJsonErrorMsg(null);
    } catch (err) {
      setJsonValid(false);
      setJsonErrorMsg(err.message);
    }
  };

  const handleFormatJson = () => {
    try {
      const parsed = JSON.parse(content);
      setContent(JSON.stringify(parsed, null, 2));
      setJsonValid(true);
      setJsonErrorMsg(null);
    } catch (err) {
      setJsonValid(false);
      setJsonErrorMsg(err.message);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!companyName.trim()) {
      setJsonErrorMsg("Le nom de l'entreprise est obligatoire.");
      return;
    }
    try {
      JSON.parse(content);
    } catch (err) {
      setJsonValid(false);
      setJsonErrorMsg(`Format JSON invalide : ${err.message}`);
      return;
    }
    onSave({
      company_name: companyName.trim(),
      filename: filename.trim() || 'design.json',
      content,
    });
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget && !loading) onClose();
      }}
    >
      <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col bg-card border border-border rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/40 shrink-0 bg-muted/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 text-violet-600 dark:text-violet-400">
              <Code2 className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-foreground">
                {record?.id ? `Modifier le JSON Design #${record.id}` : 'Créer un nouveau JSON Design'}
              </h2>
              <p className="text-xs text-muted-foreground">
                {record?.id
                  ? 'Éditez la structure JSON et les métadonnées ci-dessous'
                  : 'Renseignez les informations et collez le JSON de design'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-secondary transition-all"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">
                Nom de l'entreprise <span className="text-rose-500">*</span>
              </label>
              <Input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Ex: CDC L'ART DE NANA"
                className="w-full font-medium"
                required
                id="json-form-company"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">
                Nom de fichier source
              </label>
              <Input
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                placeholder="Ex: cdc_nana.pdf ou design.json"
                className="w-full font-mono text-xs"
                id="json-form-filename"
              />
            </div>
          </div>

          <div className="flex-1 flex flex-col min-h-[300px]">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Contenu JSON <span className="text-rose-500">*</span>
                </label>
                {jsonValid ? (
                  <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-500/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                    <CheckCircle className="h-3 w-3" /> JSON Valide
                  </span>
                ) : (
                  <span className="text-[10px] font-semibold text-rose-600 bg-rose-500/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" /> Erreur JSON
                  </span>
                )}
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleFormatJson}
                className="h-7 text-xs flex items-center gap-1 px-2.5"
                title="Formater et indenter le JSON"
              >
                <Sparkles className="h-3 w-3 text-violet-500" />
                Formater JSON
              </Button>
            </div>

            {jsonErrorMsg && !jsonValid && (
              <div className="mb-2 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-600 text-xs font-mono">
                {jsonErrorMsg}
              </div>
            )}

            <textarea
              value={content}
              onChange={(e) => handleContentChange(e.target.value)}
              placeholder="{\n  &quot;pages&quot;: []\n}"
              className="flex-1 w-full p-4 rounded-xl border border-border/80 bg-[#0d1117] font-mono text-xs leading-relaxed text-[#e6edf3] placeholder:text-muted-foreground/40 focus:outline-none focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500 resize-none"
              required
              id="json-form-content"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-border/40 shrink-0">
            <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={loading}>
              Annuler
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={loading || !jsonValid}
              className="flex items-center gap-1.5 bg-violet-600 hover:bg-violet-700 text-white"
              id="json-form-submit"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>Enregistrement...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="h-3.5 w-3.5" />
                  <span>{record?.id ? 'Enregistrer les modifications' : 'Créer le JSON'}</span>
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// Composant : Modal Consultation CDC (Markdown + Export)
// ─────────────────────────────────────────────────────────────

const CDCModal = ({ cdc, onClose, onEdit }) => {
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const h = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', h);
    return () => document.removeEventListener('keydown', h);
  }, [onClose]);

  const handleDownload = async () => {
    if (!cdc?.content) return;
    setDownloading(true);
    try {
      const blob = await apiService.downloadDocx(
        cdc.content,
        `CDC_${(cdc.company_name || 'cdc').replace(/\s+/g, '_')}.docx`
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `CDC_${(cdc.company_name || 'cdc').replace(/\s+/g, '_')}.docx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col bg-card border border-border/60 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/40 shrink-0 bg-muted/10">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary shrink-0">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h2 className="text-base font-bold text-foreground truncate">{cdc.company_name}</h2>
              <p className="text-xs text-muted-foreground">Créé le {formatDate(cdc.created_at)}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0 ml-4">
            <Button
              onClick={() => {
                onClose();
                onEdit(cdc);
              }}
              variant="outline"
              size="sm"
              className="flex items-center gap-1.5"
              id={`edit-from-modal-cdc-${cdc.id}`}
            >
              <Pencil className="h-3.5 w-3.5 text-amber-500" />
              Modifier
            </Button>
            <Button
              onClick={handleDownload}
              disabled={downloading}
              variant="outline"
              size="sm"
              className="flex items-center gap-1.5"
              id={`download-cdc-${cdc.id}`}
            >
              <Download className="h-3.5 w-3.5" />
              {downloading ? 'Export...' : 'Exporter DOCX'}
            </Button>
            <button
              onClick={onClose}
              id="close-cdc-modal"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-secondary transition-all"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <pre className="whitespace-pre-wrap font-sans text-sm text-foreground leading-relaxed">
            {cdc.content}
          </pre>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// Composant : Modal Consultation DesignJSON
// ─────────────────────────────────────────────────────────────

const DesignJsonModal = ({ record, onClose, onEdit }) => {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const h = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', h);
    return () => document.removeEventListener('keydown', h);
  }, [onClose]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(record.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {}
  };

  const handleDownload = () => {
    const blob = new Blob([record.content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `DesignJSON_${(record.company_name || 'design').replace(/\s+/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="relative w-full max-w-5xl max-h-[90vh] flex flex-col bg-card border border-border/60 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/40 shrink-0 bg-muted/10">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 text-violet-600 dark:text-violet-400 shrink-0">
              <Code2 className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h2 className="text-base font-bold text-foreground truncate">{record.company_name}</h2>
              <p className="text-xs text-muted-foreground">
                {record.filename} · Créé le {formatDate(record.created_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0 ml-4">
            <Button
              onClick={() => {
                onClose();
                onEdit(record);
              }}
              variant="outline"
              size="sm"
              className="flex items-center gap-1.5"
              id={`edit-from-modal-json-${record.id}`}
            >
              <Pencil className="h-3.5 w-3.5 text-amber-500" />
              Modifier
            </Button>
            <Button
              onClick={handleCopy}
              variant="outline"
              size="sm"
              className="flex items-center gap-1.5"
              id={`copy-json-${record.id}`}
            >
              {copied ? '✓ Copié' : 'Copier JSON'}
            </Button>
            <Button
              onClick={handleDownload}
              variant="outline"
              size="sm"
              className="flex items-center gap-1.5"
              id={`download-json-${record.id}`}
            >
              <Download className="h-3.5 w-3.5" />
              Télécharger .json
            </Button>
            <button
              onClick={onClose}
              id="close-json-modal"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-secondary transition-all"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
        {/* Content — dark code editor */}
        <div className="flex-1 overflow-y-auto p-6 bg-[#0d1117]">
          <pre className="text-[#e6edf3] font-mono text-xs leading-6 whitespace-pre-wrap">
            {(() => {
              try {
                return JSON.stringify(JSON.parse(record.content), null, 2);
              } catch {
                return record.content;
              }
            })()}
          </pre>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// Composant : Section avec En-tête et bouton d'ajout
// ─────────────────────────────────────────────────────────────

const Section = ({
  icon: Icon,
  iconBg,
  title,
  count,
  loading,
  error,
  onAddNew,
  addLabel,
  addVariant = 'default',
  children,
}) => (
  <div className="space-y-4">
    <div className="flex items-center justify-between pb-2 border-b border-border/40">
      <div className="flex items-center gap-3">
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${iconBg}`}>
          <Icon className="h-4 w-4" />
        </div>
        <h3 className="text-base font-extrabold text-foreground tracking-tight">{title}</h3>
        {!loading && !error && (
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-secondary text-muted-foreground">
            {count}
          </span>
        )}
      </div>
      {onAddNew && (
        <Button
          onClick={onAddNew}
          size="sm"
          variant={addVariant}
          className="flex items-center gap-1.5 text-xs h-8 px-3 font-semibold shadow-sm"
        >
          <Plus className="h-3.5 w-3.5" />
          {addLabel}
        </Button>
      )}
    </div>
    {children}
  </div>
);

// ─────────────────────────────────────────────────────────────
// Composant : Skeletons
// ─────────────────────────────────────────────────────────────

const Skeletons = () => (
  <div className="space-y-3">
    {[1, 2, 3].map((i) => (
      <div key={i} className="h-20 rounded-2xl border border-border/40 bg-card animate-pulse" />
    ))}
  </div>
);

const EmptyState = ({ icon: Icon, title, description, onAction, actionLabel }) => (
  <Card className="border-dashed border-border/70 bg-card/50">
    <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm font-bold text-foreground">{title}</p>
        <p className="text-xs text-muted-foreground mt-1 max-w-sm">{description}</p>
      </div>
      {onAction && actionLabel && (
        <Button onClick={onAction} variant="outline" size="sm" className="mt-2 text-xs">
          <Plus className="h-3.5 w-3.5 mr-1" />
          {actionLabel}
        </Button>
      )}
    </CardContent>
  </Card>
);

const ErrorState = ({ message, onRetry }) => (
  <Card className="border-rose-500/20 bg-rose-500/5">
    <CardContent className="flex items-center justify-between p-4 text-rose-600">
      <div className="flex items-center gap-3">
        <AlertCircle className="h-5 w-5 shrink-0" />
        <p className="text-xs font-semibold">{message}</p>
      </div>
      {onRetry && (
        <Button onClick={onRetry} variant="ghost" size="sm" className="text-xs h-7">
          Réessayer
        </Button>
      )}
    </CardContent>
  </Card>
);

// ─────────────────────────────────────────────────────────────
// Page Principale CDCList
// ─────────────────────────────────────────────────────────────

export const CDCList = () => {
  const { addToast } = useNotification();

  // ── Recherche globale ─────────────────────
  const [searchTerm, setSearchTerm] = useState('');

  // ── CDC State ─────────────────────────────
  const [cdcs, setCdcs] = useState([]);
  const [cdcLoading, setCdcLoading] = useState(true);
  const [cdcError, setCdcError] = useState(null);
  const [selectedCdc, setSelectedCdc] = useState(null);
  const [editingCdc, setEditingCdc] = useState(null);
  const [isCdcFormOpen, setIsCdcFormOpen] = useState(false);
  const [savingCdc, setSavingCdc] = useState(false);

  // ── DesignJSON State ──────────────────────
  const [jsons, setJsons] = useState([]);
  const [jsonLoading, setJsonLoading] = useState(true);
  const [jsonError, setJsonError] = useState(null);
  const [selectedJson, setSelectedJson] = useState(null);
  const [editingJson, setEditingJson] = useState(null);
  const [isJsonFormOpen, setIsJsonFormOpen] = useState(false);
  const [savingJson, setSavingJson] = useState(false);

  // ── Suppression State ─────────────────────
  const [deleteModal, setDeleteModal] = useState({
    isOpen: false,
    type: null, // 'cdc' | 'json'
    id: null,
    title: '',
    loading: false,
  });

  // ── Chargement en arrière-plan ─────────────
  const [loadingDetail, setLoadingDetail] = useState(false);

  // ── Fetch CDC ─────────────────────────────
  const fetchCdcs = useCallback(async () => {
    setCdcLoading(true);
    setCdcError(null);
    try {
      const data = await apiService.getCdcList();
      setCdcs(data.cdcs ?? []);
    } catch {
      setCdcError('Impossible de charger les CDC.');
    } finally {
      setCdcLoading(false);
    }
  }, []);

  // ── Fetch DesignJSONs ─────────────────────
  const fetchJsons = useCallback(async () => {
    setJsonLoading(true);
    setJsonError(null);
    try {
      const data = await apiService.getDesignJsonList();
      setJsons(data.design_jsons ?? []);
    } catch {
      setJsonError('Impossible de charger les JSON Design.');
    } finally {
      setJsonLoading(false);
    }
  }, []);

  const refreshAll = useCallback(() => {
    fetchCdcs();
    fetchJsons();
  }, [fetchCdcs, fetchJsons]);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  // ──────────────────────────────────────────
  // Handlers CDC
  // ──────────────────────────────────────────

  const handleOpenCdc = async (id) => {
    setLoadingDetail(true);
    try {
      const data = await apiService.getCdcById(id);
      setSelectedCdc(data);
    } catch {
      addToast('Erreur lors du chargement du CDC.', 'error');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleCreateCdc = () => {
    setEditingCdc(null);
    setIsCdcFormOpen(true);
  };

  const handleEditCdc = async (idOrObj) => {
    if (typeof idOrObj === 'object' && idOrObj.content) {
      setEditingCdc(idOrObj);
      setIsCdcFormOpen(true);
      return;
    }
    const id = typeof idOrObj === 'object' ? idOrObj.id : idOrObj;
    setLoadingDetail(true);
    try {
      const fullCdc = await apiService.getCdcById(id);
      setEditingCdc(fullCdc);
      setIsCdcFormOpen(true);
    } catch {
      addToast('Impossible de récupérer le CDC pour modification.', 'error');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSaveCdc = async (formData) => {
    setSavingCdc(true);
    try {
      if (editingCdc?.id) {
        await apiService.updateCdc(editingCdc.id, formData);
        addToast('CDC mis à jour avec succès !', 'success');
      } else {
        await apiService.createCdc(formData);
        addToast('Nouveau CDC créé avec succès !', 'success');
      }
      setIsCdcFormOpen(false);
      setEditingCdc(null);
      fetchCdcs();
    } catch (err) {
      const msg = err.response?.data?.detail || "Erreur lors de l'enregistrement du CDC.";
      addToast(msg, 'error');
    } finally {
      setSavingCdc(false);
    }
  };

  const handleDeleteCdcClick = (id, title) => {
    setDeleteModal({
      isOpen: true,
      type: 'cdc',
      id,
      title: title || `CDC #${id}`,
      loading: false,
    });
  };

  // ──────────────────────────────────────────
  // Handlers DesignJSON
  // ──────────────────────────────────────────

  const handleOpenJson = async (id) => {
    setLoadingDetail(true);
    try {
      const data = await apiService.getDesignJsonById(id);
      setSelectedJson(data);
    } catch {
      addToast('Erreur lors du chargement du JSON Design.', 'error');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleCreateJson = () => {
    setEditingJson(null);
    setIsJsonFormOpen(true);
  };

  const handleEditJson = async (idOrObj) => {
    if (typeof idOrObj === 'object' && idOrObj.content) {
      setEditingJson(idOrObj);
      setIsJsonFormOpen(true);
      return;
    }
    const id = typeof idOrObj === 'object' ? idOrObj.id : idOrObj;
    setLoadingDetail(true);
    try {
      const fullJson = await apiService.getDesignJsonById(id);
      setEditingJson(fullJson);
      setIsJsonFormOpen(true);
    } catch {
      addToast('Impossible de récupérer le JSON pour modification.', 'error');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSaveJson = async (formData) => {
    setSavingJson(true);
    try {
      if (editingJson?.id) {
        await apiService.updateDesignJson(editingJson.id, formData);
        addToast('JSON Design mis à jour avec succès !', 'success');
      } else {
        await apiService.createDesignJson(formData);
        addToast('Nouveau JSON Design créé avec succès !', 'success');
      }
      setIsJsonFormOpen(false);
      setEditingJson(null);
      fetchJsons();
    } catch (err) {
      const msg = err.response?.data?.detail || "Erreur lors de l'enregistrement du JSON.";
      addToast(msg, 'error');
    } finally {
      setSavingJson(false);
    }
  };

  const handleDeleteJsonClick = (id, title) => {
    setDeleteModal({
      isOpen: true,
      type: 'json',
      id,
      title: title || `JSON #${id}`,
      loading: false,
    });
  };

  // ──────────────────────────────────────────
  // Confirmation Suppression Générique
  // ──────────────────────────────────────────

  const handleConfirmDelete = async () => {
    setDeleteModal((prev) => ({ ...prev, loading: true }));
    try {
      if (deleteModal.type === 'cdc') {
        await apiService.deleteCdc(deleteModal.id);
        addToast('CDC supprimé avec succès.', 'success');
        fetchCdcs();
      } else if (deleteModal.type === 'json') {
        await apiService.deleteDesignJson(deleteModal.id);
        addToast('JSON Design supprimé avec succès.', 'success');
        fetchJsons();
      }
      setDeleteModal({ isOpen: false, type: null, id: null, title: '', loading: false });
    } catch {
      addToast('Erreur lors de la suppression.', 'error');
      setDeleteModal((prev) => ({ ...prev, loading: false }));
    }
  };

  // ── Filtrage recherche ────────────────────
  const filteredCdcs = cdcs.filter((c) =>
    (c.company_name || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredJsons = jsons.filter(
    (j) =>
      (j.company_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (j.filename || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const isRefreshing = cdcLoading || jsonLoading;

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-foreground tracking-tight flex items-center gap-2.5">
            <FileCode className="h-6 w-6 text-primary" />
            Bibliothèque CDC & Design JSON
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Gestion complète (CRUD) des Cahiers des Charges et JSON Design stockés en base PostgreSQL.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button
            onClick={handleCreateCdc}
            size="sm"
            className="flex items-center gap-1.5 text-xs font-semibold shadow-sm"
            id="create-cdc-header-btn"
          >
            <Plus className="h-3.5 w-3.5" />
            Nouveau CDC
          </Button>

          <Button
            onClick={handleCreateJson}
            size="sm"
            className="flex items-center gap-1.5 text-xs font-semibold bg-violet-600 hover:bg-violet-700 text-white shadow-sm"
            id="create-json-header-btn"
          >
            <Plus className="h-3.5 w-3.5" />
            Nouveau JSON
          </Button>

          <Button
            onClick={refreshAll}
            variant="outline"
            size="sm"
            id="refresh-library"
            disabled={isRefreshing}
            className="flex items-center gap-1.5 text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            Actualiser
          </Button>
        </div>
      </div>

      {/* ── Barre de recherche ── */}
      {(cdcs.length > 0 || jsons.length > 0) && (
        <div className="relative max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Rechercher par nom d'entreprise ou fichier..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 text-xs"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground text-xs"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      )}

      {/* ── Section CDC ── */}
      <Section
        icon={FileText}
        iconBg="bg-primary/10 text-primary"
        title="Cahiers des Charges (CDC)"
        count={filteredCdcs.length}
        loading={cdcLoading}
        error={cdcError}
        onAddNew={handleCreateCdc}
        addLabel="Nouveau CDC"
      >
        {cdcLoading && <Skeletons />}
        {cdcError && <ErrorState message={cdcError} onRetry={fetchCdcs} />}
        {!cdcLoading && !cdcError && cdcs.length === 0 && (
          <EmptyState
            icon={FileText}
            title="Aucun CDC enregistré"
            description="Créez un nouveau CDC manuellement ou générez-en depuis l'onglet DP Explorer."
            onAction={handleCreateCdc}
            actionLabel="Créer un CDC"
          />
        )}
        {!cdcLoading && !cdcError && cdcs.length > 0 && filteredCdcs.length === 0 && (
          <p className="text-xs text-muted-foreground italic py-4 text-center">
            Aucun CDC ne correspond à la recherche « {searchTerm} ».
          </p>
        )}
        {!cdcLoading && !cdcError && filteredCdcs.length > 0 && (
          <div className="space-y-3">
            {filteredCdcs.map((cdc) => (
              <ItemCard
                key={cdc.id}
                id={cdc.id}
                icon={FileText}
                iconColor="bg-primary/10 text-primary"
                label="CDC"
                title={cdc.company_name || 'Code inconnu'}
                subtitle={cdc.created_at}
                onView={handleOpenCdc}
                onEdit={handleEditCdc}
                onDelete={handleDeleteCdcClick}
              />
            ))}
          </div>
        )}
      </Section>

      {/* ── Section JSON Design ── */}
      <Section
        icon={Code2}
        iconBg="bg-violet-500/10 text-violet-600 dark:text-violet-400"
        title="JSON Design"
        count={filteredJsons.length}
        loading={jsonLoading}
        error={jsonError}
        onAddNew={handleCreateJson}
        addLabel="Nouveau JSON"
        addVariant="outline"
      >
        {jsonLoading && <Skeletons />}
        {jsonError && <ErrorState message={jsonError} onRetry={fetchJsons} />}
        {!jsonLoading && !jsonError && jsons.length === 0 && (
          <EmptyState
            icon={Code2}
            title="Aucun JSON Design enregistré"
            description="Créez un JSON manuellement ou générez-en un depuis l'onglet Site Generator."
            onAction={handleCreateJson}
            actionLabel="Créer un JSON Design"
          />
        )}
        {!jsonLoading && !jsonError && jsons.length > 0 && filteredJsons.length === 0 && (
          <p className="text-xs text-muted-foreground italic py-4 text-center">
            Aucun JSON ne correspond à la recherche « {searchTerm} ».
          </p>
        )}
        {!jsonLoading && !jsonError && filteredJsons.length > 0 && (
          <div className="space-y-3">
            {filteredJsons.map((j) => (
              <ItemCard
                key={j.id}
                id={j.id}
                icon={Code2}
                iconColor="bg-violet-500/10 text-violet-600 dark:text-violet-400"
                label="JSON"
                title={j.company_name || j.filename || 'Design inconnu'}
                subtitle={j.created_at}
                secondaryInfo={j.filename}
                onView={handleOpenJson}
                onEdit={handleEditJson}
                onDelete={handleDeleteJsonClick}
              />
            ))}
          </div>
        )}
      </Section>

      {/* ── Loader Overlay ── */}
      {loadingDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="flex items-center gap-3 px-6 py-4 bg-card border border-border rounded-2xl shadow-2xl">
            <RefreshCw className="h-5 w-5 text-primary animate-spin" />
            <span className="text-sm font-semibold text-foreground">Chargement des données…</span>
          </div>
        </div>
      )}

      {/* ── Modales de Consultation ── */}
      {selectedCdc && (
        <CDCModal
          cdc={selectedCdc}
          onClose={() => setSelectedCdc(null)}
          onEdit={(c) => {
            setSelectedCdc(null);
            setEditingCdc(c);
            setIsCdcFormOpen(true);
          }}
        />
      )}
      {selectedJson && (
        <DesignJsonModal
          record={selectedJson}
          onClose={() => setSelectedJson(null)}
          onEdit={(j) => {
            setSelectedJson(null);
            setEditingJson(j);
            setIsJsonFormOpen(true);
          }}
        />
      )}

      {/* ── Modales d'Édition / Création ── */}
      <CDCFormModal
        isOpen={isCdcFormOpen}
        cdc={editingCdc}
        onSave={handleSaveCdc}
        onClose={() => {
          setIsCdcFormOpen(false);
          setEditingCdc(null);
        }}
        loading={savingCdc}
      />

      <DesignJsonFormModal
        isOpen={isJsonFormOpen}
        record={editingJson}
        onSave={handleSaveJson}
        onClose={() => {
          setIsJsonFormOpen(false);
          setEditingJson(null);
        }}
        loading={savingJson}
      />

      {/* ── Modale de Confirmation de Suppression ── */}
      <DeleteConfirmModal
        isOpen={deleteModal.isOpen}
        title={deleteModal.type === 'cdc' ? 'Supprimer ce Cahier des Charges' : 'Supprimer ce JSON Design'}
        itemName={deleteModal.title}
        onConfirm={handleConfirmDelete}
        onCancel={() =>
          setDeleteModal({ isOpen: false, type: null, id: null, title: '', loading: false })
        }
        loading={deleteModal.loading}
      />
    </div>
  );
};

export default CDCList;
