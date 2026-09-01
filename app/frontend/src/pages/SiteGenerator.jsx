import React, { useRef, useState } from 'react';
import useLocalState from '../hooks/useLocalState';
import { useNotification } from '../hooks/useNotification';
import { apiService } from '../services/api';
import { Button } from '../components/ui/Button';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent
} from '../components/ui/Card';

import {
  Globe,
  Upload,
  Trash2,
  Download,
  Code2,
  Sparkles,
  Copy,
  Check,
  Save,
  Database,
  RotateCcw
} from 'lucide-react';

import JSZip from 'jszip';
import { saveAs } from 'file-saver';

export const SiteGenerator = () => {
  const { addToast } = useNotification();

  const fileInputRef = useRef(null);

  const [file, setFile] = useState(null);

  const [loadingDesign, setLoadingDesign] = useState(false);
  const [loadingWebsite, setLoadingWebsite] = useState(false);
  const [savingDb, setSavingDb] = useState(false);

  const [designJson, setDesignJson] = useLocalState('sg_designJson', null);
  const [jsonText, setJsonText] = useLocalState('sg_jsonText', '');

  const [generatedSite, setGeneratedSite] = useLocalState('sg_generatedSite', null);
  const [copied, setCopied] = useState(false);

  // ============================================================
  // FILE
  // ============================================================

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];

    if (!selected) return;

    const name = selected.name.toLowerCase();

    if (
      !name.endsWith('.pdf') &&
      !name.endsWith('.docx') &&
      !name.endsWith('.txt') &&
      !name.endsWith('.md')
    ) {
      addToast(
        'Format invalide. PDF, DOCX, TXT ou MD uniquement.',
        'error'
      );

      return;
    }

    setFile(selected);
    setDesignJson(null);
    setJsonText('');
    setGeneratedSite(null);
  };

  const removeFile = () => {
    setFile(null);
    setDesignJson(null);
    setJsonText('');
    setGeneratedSite(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // ============================================================
  // CDC -> DESIGN JSON
  // ============================================================

  const handleAnalyze = async () => {
    if (!file) {
      addToast(
        'Veuillez sélectionner un CDC.',
        'warning'
      );

      return;
    }

    setLoadingDesign(true);

    try {
      const design =
        await apiService.generateDesignFromFile(file);

      setDesignJson(design);

      setJsonText(
        JSON.stringify(design, null, 2)
      );

      setGeneratedSite(null);

      addToast(
        'DesignJSON généré avec succès.',
        'success'
      );

    } catch (err) {
      console.error(err);

      const message =
        err?.response?.data?.detail ||
        err?.message ||
        'Erreur pendant la génération du DesignJSON.';

      addToast(message, 'error');

    } finally {
      setLoadingDesign(false);
    }
  };

  // ============================================================
  // JSON EDIT
  // ============================================================

  const handleJsonChange = (value) => {
    setJsonText(value);

    try {
      const parsed = JSON.parse(value);

      setDesignJson(parsed);

    } catch {
      // JSON temporairement invalide pendant l'édition.
    }
  };

  // ============================================================
  // FORMAT JSON
  // ============================================================

  const formatJson = () => {
    try {
      const parsed = JSON.parse(jsonText);

      const formatted =
        JSON.stringify(parsed, null, 2);

      setJsonText(formatted);
      setDesignJson(parsed);

      addToast(
        'JSON formaté.',
        'success'
      );

    } catch {
      addToast(
        'Le JSON est invalide.',
        'error'
      );
    }
  };

  // ============================================================
  // COPY JSON
  // ============================================================

  const copyJson = async () => {
    try {
      await navigator.clipboard.writeText(jsonText);

      setCopied(true);

      setTimeout(
        () => setCopied(false),
        1500
      );

      addToast(
        'JSON copié.',
        'success'
      );

    } catch {
      addToast(
        'Impossible de copier le JSON.',
        'error'
      );
    }
  };

  // ============================================================
  // SAVE JSON TO DATABASE
  // ============================================================

  const handleSaveToDb = async () => {
    if (!jsonText.trim()) {
      addToast('Aucun JSON à sauvegarder.', 'warning');
      return;
    }

    let parsed;
    try {
      parsed = JSON.parse(jsonText);
    } catch (e) {
      addToast('Le JSON est invalide. Corrigez-le avant de sauvegarder.', 'error');
      return;
    }

    setSavingDb(true);
    try {
      const companyName =
        parsed?.project?.name ||
        (file?.name ? file.name.replace(/\.[^/.]+$/, '') : null) ||
        'Entreprise inconnue';
      const fileName = file?.name || `${companyName.toLowerCase().replace(/\s+/g, '_')}_design.json`;

      await apiService.createDesignJson({
        filename: fileName,
        company_name: companyName,
        content: JSON.stringify(parsed, null, 2),
      });

      addToast('DesignJSON sauvegardé dans la base de données ! Vous le trouverez dans l\'onglet CDC / JSON.', 'success');
    } catch (err) {
      console.error(err);
      const msg = err?.response?.data?.detail || err?.message || 'Erreur lors de la sauvegarde en base de données.';
      addToast(msg, 'error');
    } finally {
      setSavingDb(false);
    }
  };

  // ============================================================
  // GENERATE WEBSITE
  // ============================================================

  const handleGenerateWebsite = async () => {
    let parsedJson;

    // Vérification du JSON
    try {
      parsedJson = JSON.parse(jsonText);

    } catch {
      addToast(
        'Le JSON est invalide. Corrigez-le avant de générer le site.',
        'error'
      );

      return;
    }

    setLoadingWebsite(true);

    try {
      const result =
        await apiService.generateWebsiteFromDesign(
          parsedJson
        );

      setGeneratedSite(result);

      addToast(
        'Site web généré avec succès.',
        'success'
      );

    } catch (err) {
      console.error(err);

      const message =
        err?.response?.data?.detail ||
        err?.message ||
        'Erreur pendant la génération du site.';

      addToast(
        message,
        'error'
      );

    } finally {
      setLoadingWebsite(false);
    }
  };

  // ============================================================
  // DOWNLOAD ZIP
  // ============================================================

  const handleDownloadWebsite = async () => {
    if (
      !generatedSite ||
      !generatedSite.files
    ) {
      return;
    }

    try {
      const zip = new JSZip();

      generatedSite.files.forEach(
        (file) => {
          zip.file(
            file.path,
            file.content
          );
        }
      );

      const blob =
        await zip.generateAsync({
          type: 'blob'
        });

      saveAs(
        blob,
        `${generatedSite.site_name || 'site'}.zip`
      );

      addToast(
        'ZIP téléchargé.',
        'success'
      );

    } catch (err) {
      console.error(err);

      addToast(
        'Impossible de créer le ZIP.',
        'error'
      );
    }
  };

  // ============================================================
  // PREVIEW
  // ============================================================

  const getIndexHtml = () => {
    if (!generatedSite?.files) {
      return '';
    }

    const indexFile =
      generatedSite.files.find(
        (file) =>
          file.path === 'index.html'
      );

    return indexFile?.content || '';
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="space-y-6">

      {/* ======================================================
          1. GENERATION DE SITE
      ====================================================== */}

      <Card>

        <CardHeader>

          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary mb-3">

            <Globe className="h-6 w-6" />

          </div>

          <CardTitle>
            Génération de site web
          </CardTitle>

          <CardDescription>
            CDC → DesignJSON → HTML/CSS/JS
          </CardDescription>

        </CardHeader>

        <CardContent className="space-y-5">

          {/* ==================================================
              UPLOAD CDC
          ================================================== */}

          {!file ? (

            <div
              className="
                border-2
                border-dashed
                border-border
                rounded-2xl
                p-8
                flex
                flex-col
                items-center
                justify-center
                cursor-pointer
                relative
                bg-secondary/10
              "
            >

              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={handleFileChange}
                className="
                  absolute
                  inset-0
                  opacity-0
                  cursor-pointer
                "
              />

              <Upload
                className="
                  h-10
                  w-10
                  text-muted-foreground
                  mb-3
                "
              />

              <p className="text-sm font-bold">
                Upload CDC
              </p>

              <p className="text-xs text-muted-foreground mt-1">
                PDF / DOCX / TXT / MD
              </p>

            </div>

          ) : (

            <div
              className="
                p-4
                border
                border-border
                bg-secondary/30
                rounded-xl
                flex
                items-center
                justify-between
              "
            >

              <div className="flex items-center gap-3">

                <span className="text-2xl">
                  📄
                </span>

                <div>

                  <p className="text-sm font-bold">
                    {file.name}
                  </p>

                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} Mo
                  </p>

                </div>

              </div>

              <button
                onClick={removeFile}
                className="p-2 rounded-lg hover:bg-red-50"
              >

                <Trash2
                  className="h-4 w-4"
                />

              </button>

            </div>

          )}

          <Button
            onClick={handleAnalyze}
            loading={loadingDesign}
            disabled={!file || loadingDesign}
            variant="primary"
            className="w-full py-3.5"
          >

            <Sparkles className="h-4 w-4 mr-2" />

            {loadingDesign
              ? 'Analyse et génération du DesignJSON...'
              : 'Analyser le CDC'
            }

          </Button>

        </CardContent>

      </Card>


      {/* ======================================================
          2. DESIGN JSON / COLLAGE DIRECT
      ====================================================== */}

      <Card>

        <CardHeader>

          <div className="flex items-center justify-between">

            <div>

              <CardTitle>

                <Code2 className="inline h-5 w-5 mr-2" />

                DesignJSON

              </CardTitle>

              <CardDescription>

                Collez directement votre DesignJSON
                ou générez-le à partir du CDC.

              </CardDescription>

            </div>

            <div className="flex items-center gap-2 flex-wrap">

              <Button
                variant="secondary"
                onClick={formatJson}
                disabled={!jsonText.trim()}
              >
                Formater
              </Button>

              <Button
                variant="secondary"
                onClick={copyJson}
                disabled={!jsonText.trim()}
              >

                {copied
                  ? (
                    <Check className="h-4 w-4 mr-1" />
                  )
                  : (
                    <Copy className="h-4 w-4 mr-1" />
                  )
                }

                {copied
                  ? 'Copié'
                  : 'Copier'
                }

              </Button>

              <Button
                variant="secondary"
                onClick={handleSaveToDb}
                disabled={!jsonText.trim() || savingDb}
                loading={savingDb}
                title="Sauvegarder ce JSON dans la base de données (onglet CDC / JSON)"
                className="bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20"
              >
                <Save className="h-4 w-4 mr-1.5" />
                {savingDb ? 'Sauvegarde...' : 'Sauvegarder en BDD'}
              </Button>

              {(jsonText.trim() || generatedSite) && (
                <Button
                  variant="secondary"
                  onClick={() => {
                    setDesignJson(null);
                    setJsonText('');
                    setGeneratedSite(null);
                  }}
                  title="Effacer le JSON et le site généré"
                  className="text-destructive hover:bg-destructive/10 border border-destructive/20"
                >
                  <RotateCcw className="h-4 w-4 mr-1.5" />
                  Effacer
                </Button>
              )}

            </div>

          </div>

        </CardHeader>


        <CardContent className="space-y-5">

          {/* ==================================================
              JSON TEXTAREA
          ================================================== */}

          <textarea
            value={jsonText}
            onChange={(e) =>
              handleJsonChange(e.target.value)
            }
            spellCheck={false}
            placeholder={`Collez votre DesignJSON ici...

Exemple :

{
  "project": {
    "name": "Mon entreprise"
  },
  "design_system": {
    "theme": "modern-luxury"
  },
  "pages": [
    {
      "name": "Accueil"
    }
  ]
}`}
            className="
              w-full
              min-h-[700px]
              rounded-xl
              border
              border-border
              bg-[#0d1117]
              text-[#e6edf3]
              p-5
              font-mono
              text-sm
              leading-6
              outline-none
              resize-y
            "
          />

          {/* ==================================================
              GENERATE WEBSITE
          ================================================== */}

          <Button
            onClick={handleGenerateWebsite}
            loading={loadingWebsite}
            disabled={
              loadingWebsite ||
              !jsonText.trim()
            }
            variant="primary"
            className="w-full py-4 text-base"
          >

            <Globe className="h-5 w-5 mr-2" />

            {loadingWebsite
              ? 'Génération du site ...'
              : '🚀 Générer le site web'
            }

          </Button>

        </CardContent>

      </Card>


      {/* ======================================================
          3. GENERATED WEBSITE
      ====================================================== */}

      {generatedSite && (

        <Card>

          <CardHeader>

            <CardTitle>
              🌐 Site généré
            </CardTitle>

            <CardDescription>

              {generatedSite.files?.length || 0}
              {' '}fichiers générés

            </CardDescription>

          </CardHeader>


          <CardContent className="space-y-5">

            {/* ==================================================
                FILE LIST
            ================================================== */}

            <div
              className="
                rounded-xl
                border
                border-border
                bg-secondary/20
                p-4
              "
            >

              <p
                className="
                  text-sm
                  font-bold
                  mb-3
                "
              >
                📁 Fichiers
              </p>

              <div className="space-y-1">

                {generatedSite.files?.map(
                  (file, index) => (

                    <div
                      key={index}
                      className="
                        text-xs
                        font-mono
                        p-2
                        rounded
                        bg-background
                      "
                    >

                      {file.path}

                    </div>

                  )
                )}

              </div>

            </div>


            {/* ==================================================
                PREVIEW
            ================================================== */}

            {getIndexHtml() && (

              <div>

                <p
                  className="
                    text-sm
                    font-bold
                    mb-2
                  "
                >
                  👀 Aperçu
                </p>

                <iframe
                  srcDoc={getIndexHtml()}
                  title="Site généré"
                  className="
                    w-full
                    rounded-xl
                    border
                    border-border
                    bg-white
                  "
                  style={{
                    height: 800
                  }}
                  sandbox="
                    allow-scripts
                    allow-same-origin
                  "
                />

              </div>

            )}


            {/* ==================================================
                DOWNLOAD
            ================================================== */}

            <Button
              onClick={handleDownloadWebsite}
              variant="primary"
              className="w-full py-4"
            >

              <Download
                className="h-5 w-5 mr-2"
              />

              Télécharger le site (.zip)

            </Button>

          </CardContent>

        </Card>

      )}

    </div>
  );
};

export default SiteGenerator;

