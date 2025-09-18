import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  FileText,
  Calendar,
  Scale,
  Clock,
  Copy,
  Download,
  ExternalLink,
  CheckCircle,
  AlertTriangle,
  BarChart3,
  Eye,
  Share2,
  Sparkles
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useState } from "react";

interface TimelineEvent {
  event_id: number;
  event_name: string;
  event_description: string;
  event_date: string;
  event_page_init: number;
  event_page_end: number;
}

interface Evidence {
  evidence_id: number;
  evidence_name: string;
  evidence_flaw: string | null;
  evidence_page_init: number;
  evidence_page_end: number;
}

interface ProcessData {
  case_id: string;
  resume: string;
  timeline: TimelineEvent[];
  evidence: Evidence[];
  persisted_at: string;
}

interface ProcessResultProps {
  data: ProcessData;
}

const ProcessResult = ({ data }: ProcessResultProps) => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState("overview");

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copiado!",
      description: "Texto copiado para a área de transferência."
    });
  };

  const downloadJSON = () => {
    const dataStr = JSON.stringify(data, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `processo-${data.case_id}.json`;
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('pt-BR');
    } catch {
      return dateString;
    }
  };

  // Calcular estatísticas
  const totalPages = Math.max(
    ...data.timeline.map(t => t.event_page_end),
    ...data.evidence.map(e => e.evidence_page_end),
    0
  );
  const evidenceWithFlaws = data.evidence.filter(e => e.evidence_flaw && e.evidence_flaw !== 'sem inconsistências').length;
  const completionScore = Math.min(100, (data.timeline.length * 20) + (data.evidence.length * 15) + (data.resume.length / 10));

  return (
    <div className="space-y-4 sm:space-y-6 animate-fade-in max-w-full overflow-hidden">
      {/* Header com Estatísticas */}
      <Card className="card-legal bg-gradient-to-r from-surface to-surface-elevated border-primary/20">
        <CardHeader>
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div className="flex items-center space-x-3 min-w-0 flex-1">
              <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-6 h-6 text-primary animate-pulse" />
              </div>
              <div className="min-w-0 flex-1">
                <CardTitle className="text-foreground font-montserrat text-lg sm:text-xl truncate">
                  Análise Concluída com IA
                </CardTitle>
                <p className="text-foreground-muted font-lato text-sm truncate">
                  Processado por Google Gemini 1.5
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 justify-center lg:justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(data.resume)}
                className="hover:bg-primary/10 hover:border-primary/30 flex-shrink-0"
              >
                <Copy className="w-4 h-4 mr-1" />
                <span className="hidden sm:inline">Copiar Resumo</span>
                <span className="sm:hidden">Copiar</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={downloadJSON}
                className="hover:bg-primary/10 hover:border-primary/30 flex-shrink-0"
              >
                <Download className="w-4 h-4 mr-1" />
                <span className="hidden sm:inline">Baixar JSON</span>
                <span className="sm:hidden">JSON</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(window.location.href)}
                className="hover:bg-primary/10 hover:border-primary/30 flex-shrink-0"
              >
                <Share2 className="w-4 h-4 mr-1" />
                <span className="hidden sm:inline">Compartilhar</span>
                <span className="sm:hidden">Share</span>
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Estatísticas Rápidas */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6">
            <div className="text-center p-3 bg-primary/5 rounded-lg border border-primary/10 min-w-0">
              <div className="text-xl sm:text-2xl font-bold text-primary font-montserrat truncate">{data.timeline.length}</div>
              <div className="text-xs text-foreground-muted font-lato">Eventos</div>
            </div>
            <div className="text-center p-3 bg-accent-orange/5 rounded-lg border border-accent-orange/10 min-w-0">
              <div className="text-xl sm:text-2xl font-bold text-accent-orange font-montserrat truncate">{data.evidence.length}</div>
              <div className="text-xs text-foreground-muted font-lato">Evidências</div>
            </div>
            <div className="text-center p-3 bg-primary-light/5 rounded-lg border border-primary-light/10 min-w-0">
              <div className="text-xl sm:text-2xl font-bold text-primary-light font-montserrat truncate">{totalPages}</div>
              <div className="text-xs text-foreground-muted font-lato">Páginas</div>
            </div>
            <div className="text-center p-3 bg-surface-elevated rounded-lg border border-border min-w-0">
              <div className="text-xl sm:text-2xl font-bold text-foreground font-montserrat truncate">{Math.round(completionScore)}%</div>
              <div className="text-xs text-foreground-muted font-lato">Completude</div>
            </div>
          </div>

          {/* Informações do Processo */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="min-w-0">
              <p className="text-sm text-foreground-muted font-lato mb-1">ID do Processo</p>
              <div className="flex items-center space-x-2 min-w-0">
                <p className="text-foreground font-montserrat font-semibold truncate flex-1 text-sm sm:text-base">{data.case_id}</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(data.case_id)}
                  className="h-6 w-6 p-0 hover:bg-primary/10 flex-shrink-0"
                >
                  <Copy className="w-3 h-3" />
                </Button>
              </div>
            </div>
            <div className="min-w-0">
              <p className="text-sm text-foreground-muted font-lato mb-1">Processado em</p>
              <p className="text-foreground font-montserrat truncate text-sm sm:text-base">{formatDate(data.persisted_at)}</p>
            </div>
            <div className="min-w-0 sm:col-span-2 lg:col-span-1">
              <p className="text-sm text-foreground-muted font-lato mb-1">Status</p>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                <span className="text-foreground font-montserrat text-sm sm:text-base">Completo</span>
              </div>
            </div>
          </div>

          {/* Barra de Progresso */}
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-foreground-muted font-lato">Análise Completa</span>
              <span className="text-sm text-foreground font-montserrat">{Math.round(completionScore)}%</span>
            </div>
            <Progress value={completionScore} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Conteúdo Principal com Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4 mb-6">
          <TabsTrigger value="overview" className="flex items-center justify-center space-x-1 sm:space-x-2 px-2 sm:px-4">
            <Eye className="w-4 h-4 flex-shrink-0" />
            <span className="text-xs sm:text-sm truncate">Visão Geral</span>
          </TabsTrigger>
          <TabsTrigger value="timeline" className="flex items-center justify-center space-x-1 sm:space-x-2 px-2 sm:px-4">
            <Calendar className="w-4 h-4 flex-shrink-0" />
            <span className="text-xs sm:text-sm truncate">Timeline</span>
          </TabsTrigger>
          <TabsTrigger value="evidence" className="flex items-center justify-center space-x-1 sm:space-x-2 px-2 sm:px-4">
            <ExternalLink className="w-4 h-4 flex-shrink-0" />
            <span className="text-xs sm:text-sm truncate">Evidências</span>
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center justify-center space-x-1 sm:space-x-2 px-2 sm:px-4">
            <BarChart3 className="w-4 h-4 flex-shrink-0" />
            <span className="text-xs sm:text-sm truncate">Análise</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab: Visão Geral */}
        <TabsContent value="overview" className="space-y-6">
          <Card className="card-legal">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-foreground font-montserrat">
                <FileText className="w-5 h-5 text-primary" />
                <span>Resumo Executivo</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <p className="text-foreground-secondary font-lato leading-relaxed text-justify">
                  {data.resume}
                </p>
              </div>
              <div className="mt-4 flex items-center justify-between">
                <div className="flex items-center space-x-2 text-sm text-foreground-muted">
                  <Sparkles className="w-4 h-4" />
                  <span>Gerado por IA</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(data.resume)}
                  className="hover:bg-primary/10"
                >
                  <Copy className="w-4 h-4 mr-1" />
                  Copiar
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Resumo Rápido */}
          <div className="grid lg:grid-cols-2 gap-6">
            <Card className="card-legal">
              <CardHeader>
                <CardTitle className="text-foreground font-montserrat text-lg">
                  Eventos Principais
                </CardTitle>
              </CardHeader>
              <CardContent>
                {data.timeline.length > 0 ? (
                  <div className="space-y-3">
                    {data.timeline.slice(0, 3).map((event) => (
                      <div key={event.event_id} className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0"></div>
                        <div>
                          <p className="text-foreground font-montserrat font-medium text-sm">
                            {event.event_name}
                          </p>
                          <p className="text-foreground-muted font-lato text-xs">
                            {formatDate(event.event_date)}
                          </p>
                        </div>
                      </div>
                    ))}
                    {data.timeline.length > 3 && (
                      <p className="text-foreground-muted font-lato text-xs text-center">
                        +{data.timeline.length - 3} eventos adicionais
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Calendar className="w-12 h-12 text-foreground-muted mx-auto mb-3 opacity-50" />
                    <p className="text-foreground-muted font-lato">Nenhum evento encontrado</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="card-legal">
              <CardHeader>
                <CardTitle className="text-foreground font-montserrat text-lg">
                  Evidências Destacadas
                </CardTitle>
              </CardHeader>
              <CardContent>
                {data.evidence.length > 0 ? (
                  <div className="space-y-3">
                    {data.evidence.slice(0, 3).map((evidence) => (
                      <div key={evidence.evidence_id} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <ExternalLink className="w-4 h-4 text-accent-orange" />
                          <span className="text-foreground font-montserrat text-sm">
                            {evidence.evidence_name}
                          </span>
                        </div>
                        {evidence.evidence_flaw && evidence.evidence_flaw !== 'sem inconsistências' && (
                          <AlertTriangle className="w-4 h-4 text-yellow-500" />
                        )}
                      </div>
                    ))}
                    {data.evidence.length > 3 && (
                      <p className="text-foreground-muted font-lato text-xs text-center">
                        +{data.evidence.length - 3} evidências adicionais
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <ExternalLink className="w-12 h-12 text-foreground-muted mx-auto mb-3 opacity-50" />
                    <p className="text-foreground-muted font-lato">Nenhuma evidência encontrada</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab: Timeline */}
        <TabsContent value="timeline">
          <Card className="card-legal">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-foreground font-montserrat">
                <Calendar className="w-5 h-5 text-primary-light" />
                <span>Timeline Cronológica</span>
                <Badge variant="secondary" className="ml-2">
                  {data.timeline.length} eventos
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {data.timeline.length > 0 ? (
                <div className="space-y-6">
                  {data.timeline.map((event, index) => (
                    <div key={event.event_id} className="relative animate-fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
                      {index < data.timeline.length - 1 && (
                        <div className="absolute left-6 top-12 w-0.5 h-16 bg-gradient-to-b from-primary to-primary/30"></div>
                      )}
                      <div className="flex space-x-4">
                        <div className="flex-shrink-0">
                          <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center border-2 border-primary/30">
                            <Clock className="w-5 h-5 text-primary" />
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="bg-surface-elevated rounded-lg p-4 border border-border/50 hover:border-primary/30 transition-all duration-300 hover:shadow-lg">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="text-foreground font-montserrat font-semibold">
                                {event.event_name}
                              </h4>
                              <div className="flex items-center space-x-2">
                                <Badge variant="outline" className="text-xs">
                                  Pág. {event.event_page_init}
                                  {event.event_page_end !== event.event_page_init &&
                                    `-${event.event_page_end}`
                                  }
                                </Badge>
                                <Badge variant="secondary" className="text-xs">
                                  {formatDate(event.event_date)}
                                </Badge>
                              </div>
                            </div>
                            <p className="text-foreground-secondary font-lato text-sm leading-relaxed">
                              {event.event_description}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-16">
                  <Calendar className="w-16 h-16 text-foreground-muted mx-auto mb-4 opacity-50" />
                  <h3 className="text-foreground font-montserrat font-semibold mb-2">
                    Nenhum evento na timeline
                  </h3>
                  <p className="text-foreground-muted font-lato">
                    O documento analisado não contém eventos cronológicos identificáveis.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Evidências */}
        <TabsContent value="evidence">
          <Card className="card-legal">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-foreground font-montserrat">
                <ExternalLink className="w-5 h-5 text-accent-orange" />
                <span>Evidências e Documentos</span>
                <Badge variant="secondary" className="ml-2">
                  {data.evidence.length} itens
                </Badge>
                {evidenceWithFlaws > 0 && (
                  <Badge variant="destructive" className="ml-2">
                    {evidenceWithFlaws} com observações
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {data.evidence.length > 0 ? (
                <div className="grid gap-4">
                  {data.evidence.map((evidence, index) => (
                    <div
                      key={evidence.evidence_id}
                      className="p-4 bg-surface-elevated rounded-lg border border-border/50 hover:border-primary/30 transition-all duration-300 hover:shadow-lg animate-fade-in-up"
                      style={{ animationDelay: `${index * 0.1}s` }}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <ExternalLink className="w-5 h-5 text-accent-orange" />
                          <h4 className="text-foreground font-montserrat font-semibold">
                            {evidence.evidence_name}
                          </h4>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="text-xs">
                            Pág. {evidence.evidence_page_init}
                            {evidence.evidence_page_end !== evidence.evidence_page_init &&
                              `-${evidence.evidence_page_end}`
                            }
                          </Badge>
                          {evidence.evidence_flaw && evidence.evidence_flaw !== 'sem inconsistências' ? (
                            <AlertTriangle className="w-4 h-4 text-yellow-500" />
                          ) : (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          )}
                        </div>
                      </div>
                      {evidence.evidence_flaw && (
                        <div className="mt-2 p-3 bg-surface rounded-lg border-l-4 border-l-yellow-500">
                          <div className="flex items-center space-x-2 mb-1">
                            <AlertTriangle className="w-4 h-4 text-yellow-500" />
                            <span className="text-sm font-montserrat font-medium text-foreground">
                              Observação
                            </span>
                          </div>
                          <p className="text-sm text-foreground-muted font-lato">
                            {evidence.evidence_flaw}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-16">
                  <ExternalLink className="w-16 h-16 text-foreground-muted mx-auto mb-4 opacity-50" />
                  <h3 className="text-foreground font-montserrat font-semibold mb-2">
                    Nenhuma evidência encontrada
                  </h3>
                  <p className="text-foreground-muted font-lato">
                    O documento analisado não contém evidências ou documentos identificáveis.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Análise */}
        <TabsContent value="analytics">
          <div className="grid gap-6">
            <Card className="card-legal">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-foreground font-montserrat">
                  <BarChart3 className="w-5 h-5 text-primary" />
                  <span>Análise Estatística</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid lg:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-foreground font-montserrat font-semibold mb-3">
                      Distribuição de Conteúdo
                    </h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-foreground-muted font-lato">Eventos na Timeline</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-16 h-2 bg-surface-elevated rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary transition-all duration-1000"
                              style={{ width: `${Math.min(100, (data.timeline.length / 10) * 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-foreground font-montserrat text-sm w-8">{data.timeline.length}</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-foreground-muted font-lato">Evidências Documentais</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-16 h-2 bg-surface-elevated rounded-full overflow-hidden">
                            <div
                              className="h-full bg-accent-orange transition-all duration-1000"
                              style={{ width: `${Math.min(100, (data.evidence.length / 10) * 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-foreground font-montserrat text-sm w-8">{data.evidence.length}</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-foreground-muted font-lato">Páginas Analisadas</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-16 h-2 bg-surface-elevated rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary-light transition-all duration-1000"
                              style={{ width: `${Math.min(100, (totalPages / 50) * 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-foreground font-montserrat text-sm w-8">{totalPages}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-foreground font-montserrat font-semibold mb-3">
                      Qualidade da Análise
                    </h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-foreground-muted font-lato">Completude</span>
                        <Badge variant="secondary">{Math.round(completionScore)}%</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-foreground-muted font-lato">Evidências Válidas</span>
                        <Badge variant={evidenceWithFlaws === 0 ? "default" : "secondary"}>
                          {data.evidence.length - evidenceWithFlaws}/{data.evidence.length}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-foreground-muted font-lato">Status</span>
                        <Badge variant="default" className="bg-green-500/10 text-green-500 border-green-500/20">
                          Processado
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Dados Brutos */}
            <Card className="card-legal">
              <CardHeader>
                <CardTitle className="text-foreground font-montserrat">
                  Dados Brutos (JSON)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-surface-elevated rounded-xl p-3 sm:p-4 max-h-64 overflow-auto border border-border/50">
                  <pre className="text-xs sm:text-sm text-primary-light font-mono whitespace-pre-wrap break-all">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </div>
                <div className="mt-3 flex justify-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(JSON.stringify(data, null, 2))}
                    className="hover:bg-primary/10"
                  >
                    <Copy className="w-4 h-4 mr-1" />
                    Copiar JSON
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ProcessResult;
