import React, { useState } from 'react';
import useLocalState from '../hooks/useLocalState';
import { useAuth } from '../hooks/useAuth';
import { useNotification } from '../hooks/useNotification';
import { apiService } from '../services/api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { 
  Search, 
  FileText, 
  Sparkles, 
  Trash2, 
  Building2, 
  MapPin, 
  Briefcase,
  ChevronDown, 
  ChevronUp,
  Download,
  Terminal,
  FileCode,
  User,
  Clock,
  Globe,
  ShoppingBag,
  List,
  CheckCircle2,
  Tag
} from 'lucide-react';

const formatTime = (seconds) => {
  if (seconds === undefined || seconds === null) return '';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h.toString().padStart(2, '0')}h${m.toString().padStart(2, '0')}`;
};

const formatOpeningHours = (openingRanges) => {
  if (!openingRanges || !Array.isArray(openingRanges)) return [];
  const valid = openingRanges.filter(r => r.isOpeningRange && !r.isCampaign);
  if (valid.length === 0) return [];
  
  // Sort by dayOfWeek and startTime
  valid.sort((a, b) => {
    if (a.dayOfWeek !== b.dayOfWeek) return (a.dayOfWeek || 0) - (b.dayOfWeek || 0);
    return (a.startTime || 0) - (b.startTime || 0);
  });

  const daysFr = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
  const byDay = {};

  valid.forEach(r => {
    const day = r.dayOfWeek || 0;
    const horaire = `${formatTime(r.startTime)} - ${formatTime(r.endTime)}`;
    if (!byDay[day]) byDay[day] = [];
    if (!byDay[day].includes(horaire)) {
      byDay[day].push(horaire);
    }
  });

  // Group days by same schedule
  const scheduleDays = {};
  Object.keys(byDay).forEach(day => {
    const key = byDay[day].join(' et ');
    if (!scheduleDays[key]) scheduleDays[key] = [];
    scheduleDays[key].push(parseInt(day, 10));
  });

  return Object.keys(scheduleDays).map(horaireStr => {
    const days = scheduleDays[horaireStr];
    days.sort((a, b) => a - b);
    const daysText = days.map(d => daysFr[d] || `Jour ${d}`).join(', ');
    return `${daysText} : ${horaireStr}`;
  });
};

const DetailRow = ({ label, value, icon: Icon }) => {
  if (!value) return null;
  return (
    <div className="flex items-start gap-3 p-3.5 rounded-xl border border-border/50 bg-card/50 hover:border-primary/20 hover:bg-card/85 transition-all">
      {Icon && (
        <div className="mt-0.5 p-1.5 rounded-lg bg-secondary text-primary shrink-0">
          <Icon className="h-4 w-4" />
        </div>
      )}
      <div className="min-w-0 flex-1">
        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide select-none">{label}</p>
        <p className="text-sm font-semibold text-foreground mt-0.5 whitespace-pre-line leading-relaxed">{value}</p>
      </div>
    </div>
  );
};

export const DPExplorer = () => {
  const { auth, cleanedData, setCleanedData } = useAuth();
  const { addToast } = useNotification();

  const [code, setCode] = useLocalState('dp_activeCode', '');
  const [loadingInfo, setLoadingInfo] = useState(false);
  const [loadingCdc, setLoadingCdc] = useState(false);
  const [loadingClean, setLoadingClean] = useState(false);
  const [loadingDocx, setLoadingDocx] = useState(false);

  // Local state for API results — persisted so they survive tab switches
  const [result, setResult] = useLocalState('dp_clientInfo', null);
  const [cdc, setCdc] = useLocalState('dp_cdcContent', null);
  const [qaScore, setQaScore] = useLocalState('dp_qaScore', null);
  const [cleanedJson, setCleanedJson] = useLocalState('dp_cleanedJson', null);

  // Expander collapse states
  const [expandPartner, setExpandPartner] = useState(false);
  const [expandDetails, setExpandDetails] = useState(false);
  const [expandCompany, setExpandCompany] = useState(false);
  const [expandCleaned, setExpandCleaned] = useState(false);

  // Tab state for Fiche Client Synthétique
  const [activeDetailTab, setActiveDetailTab] = useState('identity');

  const handleGetInfo = async () => {
    if (!auth) {
      addToast('Veuillez vous connecter d\'abord', 'warning');
      return;
    }
    if (!code.trim()) {
      addToast('Veuillez entrer un code client', 'warning');
      return;
    }

    setLoadingInfo(true);
    try {
      const data = await apiService.getInfo(auth, code.trim());
      setResult(data);
      setActiveDetailTab('identity');
      addToast('Données récupérées avec succès !', 'success');
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || 'Erreur lors de la récupération des données';
      addToast(msg, 'error');
    } finally {
      setLoadingInfo(false);
    }
  };

  const handleGenerateCdc = async () => {
    if (!auth) {
      addToast('Veuillez vous connecter d\'abord', 'warning');
      return;
    }
    if (!code.trim()) {
      addToast('Veuillez entrer un code client', 'warning');
      return;
    }

    setLoadingCdc(true);
    try {
      const data = await apiService.generateCdc(auth, code.trim());
      setCdc(data.content);
      setQaScore(data.score);
      addToast('Cahier des charges généré avec succès !', 'success');
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || 'Erreur lors de la génération du cahier des charges';
      addToast(msg, 'error');
    } finally {
      setLoadingCdc(false);
    }
  };

  const handleCleanData = async () => {
    if (!auth) {
      addToast('Veuillez vous connecter d\'abord', 'warning');
      return;
    }
    if (!code.trim()) {
      addToast('Veuillez entrer un code client', 'warning');
      return;
    }

    setLoadingClean(true);
    try {
      const data = await apiService.cleanData(auth, code.trim());
      const cleaned = data.cleaned;
      setCleanedJson(cleaned);
      setCleanedData(cleaned); // Set in global context for Wireframe generator
      setExpandCleaned(true);
      addToast('Données nettoyées ! Vous pouvez générer le wireframe dans l\'onglet Wireframe.', 'success');
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || 'Erreur lors du nettoyage des données';
      addToast(msg, 'error');
    } finally {
      setLoadingClean(false);
    }
  };

  // Helper to trigger download of CDC as DOCX file from backend
  const downloadCdcDocx = async () => {
    if (!cdc) return;
    setLoadingDocx(true);
    addToast('Génération du fichier DOCX en cours...', 'info');
    try {
      const filename = `cahier_de_charge_${code.trim() || 'client'}.docx`;
      const blob = await apiService.downloadDocx(cdc, filename);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      addToast('Téléchargement réussi !', 'success');
    } catch (err) {
      console.error(err);
      addToast('Erreur lors du téléchargement du fichier DOCX', 'error');
    } finally {
      setLoadingDocx(false);
    }
  };

  const renderJsonAccordion = (title, data, isExpanded, setIsExpanded) => {
    return (
      <div className="border border-border/60 rounded-xl bg-card overflow-hidden">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between p-4 hover:bg-secondary/20 transition-colors"
        >
          <div className="flex items-center gap-2">
            <FileCode className="h-4.5 w-4.5 text-muted-foreground" />
            <span className="text-sm font-bold text-foreground">{title}</span>
          </div>
          {isExpanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </button>
        {isExpanded && (
          <div className="p-4 border-t border-border/40 bg-muted/10">
            <pre className="text-xs font-mono bg-secondary/40 p-3 rounded-lg overflow-x-auto text-muted-foreground max-h-60">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Configuration Header Card */}
      <Card>
        <CardHeader>
          <CardTitle>Recherche & Actions Client</CardTitle>
          <CardDescription>
            Entrez le code Sage client pour interroger la base de données, générer le cahier des charges et exécuter les scripts de préparation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4 md:flex-row md:items-end">
            <div className="flex-1">
              <Input
                id="client-code"
                label="Code Sage Client"
                placeholder="Ex: ABC01"
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            </div>
            
            {/* Control buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 shrink-0">
              <Button
                onClick={handleGetInfo}
                loading={loadingInfo}
                disabled={loadingCdc || loadingClean}
                variant="outline"
                className="w-full"
              >
                <Search className="h-4 w-4 mr-2" />
                Récupérer
              </Button>
              
              <Button
                onClick={handleGenerateCdc}
                loading={loadingCdc}
                disabled={loadingInfo || loadingClean}
                variant="outline"
                className="w-full"
              >
                <FileText className="h-4 w-4 mr-2" />
                Générer CDC
              </Button>
              
              <Button
                onClick={handleCleanData}
                loading={loadingClean}
                disabled={loadingInfo || loadingCdc}
                variant="primary"
                className="w-full"
              >
                <Sparkles className="h-4 w-4 mr-2" />
                Nettoyer
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Info Results (If Loaded) */}
      {result && (
        <div className="space-y-6 animate-fade-in">
          {/* Summary Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="flex items-center gap-4 p-5 hover:border-primary/20">
              <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary shrink-0">
                <Building2 className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest select-none">Enseigne</p>
                <h4 className="text-base font-extrabold text-foreground truncate">{result.company?.Name || '—'}</h4>
              </div>
            </Card>

            <Card className="flex items-center gap-4 p-5 hover:border-primary/20">
              <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary shrink-0">
                <Briefcase className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest select-none">Secteur</p>
                <h4 className="text-base font-extrabold text-foreground truncate">{result.company?.Industry || '—'}</h4>
              </div>
            </Card>

            <Card className="flex items-center gap-4 p-5 hover:border-primary/20">
              <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary shrink-0">
                <MapPin className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest select-none">Ville</p>
                <h4 className="text-base font-extrabold text-foreground truncate">{result.company?.BillingCity || '—'}</h4>
              </div>
            </Card>
          </div>

          {/* Fiche Client Synthétique */}
          {(() => {
            const details = Array.isArray(result.details) ? result.details[0] : result.details || {};
            const company = result.company || {};
            
            const seoKeywords = details.sites?.[0]?.seoKeywords || [];
            const socialNetworks = details.socialNetworks || [];
            
            const products = details.partnerBoutique?.shopProducts || [];
            const hasProducts = products.length > 0;
            const productCount = products.length;
            
            const siteTrees = details.sites?.[0]?.siteTrees || [];
            const hasPages = siteTrees.length > 0;
            const pagesCount = siteTrees.length;

            return (
              <Card className="border-primary/20 shadow-lg bg-gradient-to-b from-card to-card/50">
                <CardHeader className="border-b border-border/40 pb-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-xl font-bold flex items-center gap-2 text-primary">
                        <Briefcase className="h-5 w-5" />
                        Fiche Client Synthétique
                      </CardTitle>
                      <CardDescription>
                        Informations restructurées et lisibles extraites du profil client.
                      </CardDescription>
                    </div>
                    <Badge variant="outline" className="border-primary/30 text-primary font-bold">
                      Sage: {code}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  {/* Tab buttons */}
                  <div className="flex flex-wrap gap-1.5 p-1 bg-secondary/50 rounded-xl border border-border/60 mb-6 max-w-max">
                    <button
                      type="button"
                      onClick={() => setActiveDetailTab('identity')}
                      className={`px-4 py-2 text-xs font-bold rounded-lg transition-all duration-200 select-none ${
                        activeDetailTab === 'identity'
                          ? 'bg-card text-primary shadow-sm border border-border/50'
                          : 'text-muted-foreground hover:text-foreground hover:bg-card/20'
                      }`}
                    >
                      Identité & Activité
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveDetailTab('profile')}
                      className={`px-4 py-2 text-xs font-bold rounded-lg transition-all duration-200 select-none ${
                        activeDetailTab === 'profile'
                          ? 'bg-card text-primary shadow-sm border border-border/50'
                          : 'text-muted-foreground hover:text-foreground hover:bg-card/20'
                      }`}
                    >
                      Profil & Positionnement
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveDetailTab('logistics')}
                      className={`px-4 py-2 text-xs font-bold rounded-lg transition-all duration-200 select-none ${
                        activeDetailTab === 'logistics'
                          ? 'bg-card text-primary shadow-sm border border-border/50'
                          : 'text-muted-foreground hover:text-foreground hover:bg-card/20'
                      }`}
                    >
                      Localités & Horaires
                    </button>
                    {hasProducts && (
                      <button
                        type="button"
                        onClick={() => setActiveDetailTab('boutique')}
                        className={`px-4 py-2 text-xs font-bold rounded-lg transition-all duration-200 select-none ${
                          activeDetailTab === 'boutique'
                            ? 'bg-card text-primary shadow-sm border border-border/50'
                            : 'text-muted-foreground hover:text-foreground hover:bg-card/20'
                        }`}
                      >
                        Boutique ({productCount})
                      </button>
                    )}
                    {hasPages && (
                      <button
                        type="button"
                        onClick={() => setActiveDetailTab('pages')}
                        className={`px-4 py-2 text-xs font-bold rounded-lg transition-all duration-200 select-none ${
                          activeDetailTab === 'pages'
                            ? 'bg-card text-primary shadow-sm border border-border/50'
                            : 'text-muted-foreground hover:text-foreground hover:bg-card/20'
                        }`}
                      >
                        Sitemap ({pagesCount})
                      </button>
                    )}
                  </div>

                  {/* Tab contents */}
                  {activeDetailTab === 'identity' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in">
                      <DetailRow label="Enseigne" value={company.Name || details.name} icon={Building2} />
                      <DetailRow label="Secteur d'activité" value={company.Industry || details.activity} icon={Briefcase} />
                      <DetailRow label="Code APE" value={company.Libell_code_APE__c || details.code_ape} icon={FileCode} />
                      <DetailRow 
                        label="Pronom de rédaction" 
                        value={details.pronoun ? `${details.pronoun} (ex: ${details.pronoun === 'je' ? 'Rédiger à la première personne du singulier' : 'Rédiger à la première personne du pluriel'})` : null} 
                        icon={User} 
                      />
                      <DetailRow 
                        label="Structure d'équipe" 
                        value={details.isAlone !== undefined && details.isAlone !== null ? (details.isAlone === true || details.isAlone === 'true' ? 'Travaille seul(e)' : 'Travaille en équipe') : null} 
                        icon={User} 
                      />
                      
                      {seoKeywords.length > 0 && (
                        <div className="col-span-1 md:col-span-2 p-3.5 rounded-xl border border-border/50 bg-card/50">
                          <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-1.5">Mots-clés SEO suggérés</p>
                          <div className="flex flex-wrap gap-1.5">
                            {seoKeywords.map((kw, i) => (
                              <Badge key={i} variant="secondary" className="text-xs font-semibold px-2 py-0.5">
                                {kw}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {socialNetworks.length > 0 && (
                        <div className="col-span-1 md:col-span-2 p-3.5 rounded-xl border border-border/50 bg-card/50">
                          <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-1.5">Réseaux Sociaux</p>
                          <div className="flex flex-wrap gap-3">
                            {socialNetworks.map((sn, i) => {
                              return (
                                <a 
                                  key={i} 
                                  href={sn.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer" 
                                  className="flex items-center gap-2 px-3 py-1.5 border border-border hover:border-primary/50 hover:bg-primary/5 rounded-xl text-xs font-bold text-foreground transition-all"
                                >
                                  <Globe className="h-4 w-4 text-primary animate-pulse" />
                                  {sn.name || 'Lien'}
                                </a>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {activeDetailTab === 'profile' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in">
                      <DetailRow label="Présentation de l'entreprise" value={details.companyDetails} icon={FileText} />
                      <DetailRow label="Typologie client" value={details.customers} icon={User} />
                      <DetailRow label="Points forts / Atouts" value={details.keyPoints} icon={Sparkles} />
                      <DetailRow label="Distinction concurrentielle" value={details.competitor} icon={CheckCircle2} />
                      <DetailRow label="Expérience" value={details.experience} icon={Clock} />
                      <DetailRow label="Détails des services" value={details.serviceDetails} icon={List} />
                      <DetailRow label="Partenaires & Marques" value={details.partners} icon={Tag} />
                      <DetailRow label="Concepts & Objectifs Boutique" value={details.goalsStore} icon={ShoppingBag} />
                      <DetailRow label="Type de produits & Marques Boutique" value={details.productBrands} icon={Tag} />
                    </div>
                  )}

                  {activeDetailTab === 'logistics' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in">
                      <DetailRow label="Localité principale" value={details.mainLocality || company.BillingCity} icon={MapPin} />
                      <DetailRow 
                        label="Localités secondaires" 
                        value={
                          Array.isArray(details.secondaryLocalities) 
                            ? details.secondaryLocalities.join(', ') 
                            : details.secondaryLocalities
                        } 
                        icon={MapPin} 
                      />
                      <DetailRow label="Zone de couverture géographique" value={details.sites?.[0]?.coverageArea} icon={Globe} />
                      <DetailRow label="Notes exceptionnelles sur les horaires" value={details.aboutOpeningRange} icon={Clock} />
                      
                      {(() => {
                        const formattedHours = formatOpeningHours(details.openingRanges);
                        if (formattedHours.length === 0) return null;
                        return (
                          <div className="col-span-1 md:col-span-2 p-3.5 rounded-xl border border-border/50 bg-card/50">
                            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1">
                              <Clock className="h-3.5 w-3.5 text-primary" />
                              Horaires Habituels
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pl-1.5">
                              {formattedHours.map((line, i) => (
                                <p key={i} className="text-xs font-semibold text-foreground">
                                  ⏰ {line}
                                </p>
                              ))}
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  )}

                  {activeDetailTab === 'boutique' && hasProducts && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-fade-in">
                      {products.map((prod, i) => (
                        <div key={i} className="p-4 rounded-xl border border-border bg-card/40 flex flex-col justify-between gap-3 hover:border-primary/20 hover:bg-card/75 transition-all">
                          <div className="space-y-1.5">
                            <p className="text-sm font-bold text-foreground">{prod.productName || 'Produit sans nom'}</p>
                            {prod.description && (
                              <p className="text-xs text-muted-foreground leading-relaxed">{prod.description}</p>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {prod.categories && (
                              <Badge variant="outline" className="text-[10px] font-bold bg-secondary/30">
                                Cat: {prod.categories}
                              </Badge>
                            )}
                            {prod.subCategories && (
                              <Badge variant="outline" className="text-[10px] font-bold bg-secondary/30">
                                Sous-Cat: {prod.subCategories}
                              </Badge>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {activeDetailTab === 'pages' && hasPages && (
                    <div className="space-y-3.5 animate-fade-in">
                      <div className="p-3 bg-secondary/30 border border-border/40 rounded-xl">
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          Arborescence détectée pour la génération du site web. Les dossiers et les sous-pages définissent le plan du site.
                        </p>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {siteTrees.map((page, i) => {
                          const isParent = page.children && page.children.length > 0;
                          const parentName = page.parent?.name;
                          
                          return (
                            <div key={i} className="p-4 rounded-xl border border-border/80 bg-card hover:border-primary/20 transition-all flex flex-col gap-2">
                              <div className="flex items-start justify-between gap-2">
                                <div className="min-w-0">
                                  <h5 className="text-sm font-bold text-foreground truncate flex items-center gap-1.5">
                                    <FileText className="h-4 w-4 text-primary shrink-0" />
                                    {page.name}
                                  </h5>
                                  {parentName && (
                                    <p className="text-[10px] text-muted-foreground mt-0.5">
                                      Sous-page de : <span className="font-semibold">{parentName}</span>
                                    </p>
                                  )}
                                </div>
                                <div className="flex gap-1 shrink-0">
                                  {page.position === 0 && <Badge variant="primary" className="text-[9px] px-1.5 py-0.5">Accueil</Badge>}
                                  {isParent && <Badge variant="outline" className="text-[9px] px-1.5 py-0.5 bg-secondary/30">Parent</Badge>}
                                </div>
                              </div>
                              {page.description && (
                                <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed mt-1">
                                  {page.description}
                                </p>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })()}

          {/* Raw Client Data Accordions */}
          <Card>
            <CardHeader>
              <CardTitle>Données complètes extraites</CardTitle>
              <CardDescription>Visualisez la structure des données brutes stockées pour ce client.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {renderJsonAccordion("Données Partner", result.partner || {}, expandPartner, setExpandPartner)}
              {renderJsonAccordion("Détails Client", result.details || {}, expandDetails, setExpandDetails)}
              {renderJsonAccordion("Informations Company", result.company || {}, expandCompany, setExpandCompany)}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Cleaned Data Results */}
      {cleanedJson && (
        <Card className="animate-fade-in border-emerald-500/20">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <div>
              <CardTitle className="text-emerald-700 dark:text-emerald-400 flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Données nettoyées
              </CardTitle>
              <CardDescription>Les données brutes ont été filtrées et préparées pour alimenter l'éditeur de wireframes.</CardDescription>
            </div>
            <Badge variant="success">Prêt pour le Wireframe</Badge>
          </CardHeader>
          <CardContent>
            {renderJsonAccordion("Données nettoyées de l'agent", cleanedJson, expandCleaned, setExpandCleaned)}
          </CardContent>
        </Card>
      )}

      {/* Generated CDC Content */}
      {cdc && (
        <Card className="animate-fade-in">
          <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Cahier des charges généré
              </CardTitle>
              <CardDescription>Document complet structurant la demande fonctionnelle.</CardDescription>
            </div>
            {qaScore !== null && (
              <div className="flex items-center gap-2.5 px-4 py-2 bg-secondary border border-border/80 rounded-xl">
                <span className="text-xs font-semibold text-muted-foreground select-none">Qualité :</span>
                <span className="text-sm font-extrabold text-primary">{qaScore}/100</span>
              </div>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Markdown Viewer */}
            <div className="relative">
              <textarea
                readOnly
                value={cdc}
                className="w-full h-96 p-4 rounded-xl border border-input bg-muted/20 font-mono text-sm leading-relaxed text-muted-foreground focus:outline-none"
              />
            </div>
            
            <div className="flex justify-end">
              <Button onClick={downloadCdcDocx} loading={loadingDocx}>
                <Download className="h-4 w-4 mr-2" />
                Télécharger (.docx)
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DPExplorer;
