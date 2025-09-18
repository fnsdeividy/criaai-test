import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import ProcessResult from "@/components/ProcessResult";
import {
  Upload,
  Link,
  FileText,
  Brain,
  Loader2,
  AlertCircle,
  CheckCircle,
  XCircle
} from "lucide-react";

// Importações seguras
import { apiClient } from "@/services/apiClient";
import { validateUrl, validateFile, generateSecureCaseId, sanitizeString } from "@/utils/security";
import { APP_CONFIG, UPLOAD_CONFIG } from "@/config/app";
import type { ProcessData, ProcessingState, UploadProgress } from "@/types/api";

interface ProcessorState {
  pdfUrl: string;
  selectedFile: File | null;
  result: ProcessData | null;
  activeTab: "url" | "upload";
  processingState: ProcessingState;
  uploadProgress: number;
  validationErrors: string[];
}

const PDFProcessor = () => {
  const [state, setState] = useState<ProcessorState>({
    pdfUrl: "",
    selectedFile: null,
    result: null,
    activeTab: "url",
    processingState: "idle",
    uploadProgress: 0,
    validationErrors: [],
  });

  const { toast } = useToast();
  const resultRef = useRef<HTMLDivElement>(null);

  // Scroll automático seguro para o resultado
  const scrollToResult = useCallback(() => {
    if (state.result && resultRef.current) {
      setTimeout(() => {
        const element = resultRef.current;
        if (element) {
          const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
          const offsetPosition = elementPosition - 80;

          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });

          toast({
            title: "✨ Análise concluída!",
            description: "Role para baixo para ver os resultados detalhados.",
            duration: 4000,
          });
        }
      }, 500);
    }
  }, [state.result, toast]);

  useEffect(() => {
    if (state.result) {
      scrollToResult();
    }
  }, [state.result, scrollToResult]);

  // Validação em tempo real da URL
  const handleUrlChange = useCallback((url: string) => {
    const sanitizedUrl = sanitizeString(url);
    const validation = validateUrl(sanitizedUrl);

    setState(prev => ({
      ...prev,
      pdfUrl: sanitizedUrl,
      selectedFile: null,
      validationErrors: validation.errors,
    }));
  }, []);

  // Validação e seleção de arquivo
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (!file) {
      setState(prev => ({
        ...prev,
        selectedFile: null,
        validationErrors: [],
      }));
      return;
    }

    const validation = validateFile(file);

    if (validation.isValid) {
      setState(prev => ({
        ...prev,
        selectedFile: file,
        pdfUrl: "",
        validationErrors: [],
      }));

      if (validation.warnings.length > 0) {
        toast({
          title: "Aviso",
          description: validation.warnings.join(", "),
          variant: "default"
        });
      }
    } else {
      setState(prev => ({
        ...prev,
        selectedFile: null,
        validationErrors: validation.errors,
      }));

      toast({
        title: "Arquivo inválido",
        description: validation.errors[0],
        variant: "destructive"
      });
    }

    // Limpar o input para permitir reselecionar o mesmo arquivo
    event.target.value = "";
  }, [toast]);

  // Processamento principal
  const handleProcess = useCallback(async () => {
    const { pdfUrl, selectedFile, activeTab } = state;

    // Validação inicial
    if (!pdfUrl && !selectedFile) {
      toast({
        title: "Erro de validação",
        description: "Por favor, forneça uma URL ou selecione um arquivo PDF.",
        variant: "destructive"
      });
      return;
    }

    setState(prev => ({ ...prev, processingState: "validating" }));

    try {
      // Gerar case_id seguro
      const caseId = generateSecureCaseId();

      if (activeTab === "url" && pdfUrl) {
        // Processar via URL
        const urlValidation = validateUrl(pdfUrl);
        if (!urlValidation.isValid) {
          throw new Error(urlValidation.errors[0]);
        }

        setState(prev => ({ ...prev, processingState: "processing" }));

        const response = await apiClient.extractFromUrl({
          pdf_url: pdfUrl,
          case_id: caseId
        });

        if (response.error) {
          throw new Error(response.error.detail);
        }

        setState(prev => ({
          ...prev,
          result: response.data!,
          processingState: "completed"
        }));

      } else if (activeTab === "upload" && selectedFile) {
        // Processar via upload
        const fileValidation = validateFile(selectedFile);
        if (!fileValidation.isValid) {
          throw new Error(fileValidation.errors[0]);
        }

        setState(prev => ({ ...prev, processingState: "uploading" }));

        const response = await apiClient.extractFromUpload(
          {
            file: selectedFile,
            case_id: caseId
          },
          (progress) => {
            setState(prev => {
              // Determinar o estado baseado no progresso
              let newState = prev.processingState;
              if (progress <= 25) {
                newState = "uploading";
              } else if (progress <= 99) {
                newState = "polling";
              }
              
              return { 
                ...prev, 
                uploadProgress: progress,
                processingState: newState
              };
            });
          }
        );

        if (response.error) {
          throw new Error(response.error.detail);
        }

        setState(prev => ({
          ...prev,
          result: response.data!,
          processingState: "completed",
          uploadProgress: 100
        }));
      }

      toast({
        title: "Processamento concluído!",
        description: "O PDF foi analisado com sucesso.",
      });

    } catch (error) {
      console.error("Erro no processamento:", error);

      setState(prev => ({ ...prev, processingState: "error" }));

      toast({
        title: "Erro no processamento",
        description: error instanceof Error ? error.message : "Falha ao processar o PDF.",
        variant: "destructive"
      });
    }
  }, [state, toast]);

  // Resetar estado
  const handleReset = useCallback(() => {
    setState({
      pdfUrl: "",
      selectedFile: null,
      result: null,
      activeTab: "url",
      processingState: "idle",
      uploadProgress: 0,
      validationErrors: [],
    });
  }, []);

  // Estados derivados
  const isProcessing = ["validating", "uploading", "processing", "polling"].includes(state.processingState);
  const canProcess = (state.pdfUrl && state.activeTab === "url") ||
    (state.selectedFile && state.activeTab === "upload");
  const hasValidationErrors = state.validationErrors.length > 0;

  return (
    <div className="container mx-auto px-4 sm:px-6 py-8 sm:py-12 max-w-7xl">
      <div className="grid lg:grid-cols-2 gap-6 lg:gap-12">
        {/* Input Section */}
        <div className="space-y-6 sm:space-y-8">
          <div className="text-center lg:text-left">
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bebas text-gradient mb-4 leading-tight">
              Analisador de PDFs Jurídicos
            </h1>
            <p className="text-lg sm:text-xl text-foreground-secondary font-lato">
              Extraia informações estruturadas de processos em segundos
            </p>
          </div>

          <Card className="card-legal">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-foreground font-montserrat">
                <FileText className="w-6 h-6 text-accent-orange" />
                <span>Selecione o PDF</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <Tabs
                value={state.activeTab}
                onValueChange={(value) =>
                  setState(prev => ({
                    ...prev,
                    activeTab: value as "url" | "upload",
                    validationErrors: [],
                    result: null
                  }))
                }
              >
                <TabsList className="grid w-full grid-cols-2 bg-surface">
                  <TabsTrigger value="url" className="data-[state=active]:bg-primary data-[state=active]:text-white">
                    <Link className="w-4 h-4 mr-2" />
                    URL
                  </TabsTrigger>
                  <TabsTrigger value="upload" className="data-[state=active]:bg-primary data-[state=active]:text-white">
                    <Upload className="w-4 h-4 mr-2" />
                    Upload
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="url" className="space-y-4">
                  <div>
                    <Label htmlFor="pdf-url" className="text-foreground font-lato">
                      URL do PDF (link público)
                    </Label>
                    <Input
                      id="pdf-url"
                      placeholder="https://processo.tjsp.jus.br/documento/12345"
                      value={state.pdfUrl}
                      onChange={(e) => handleUrlChange(e.target.value)}
                      className={`mt-2 bg-surface border-border text-foreground ${hasValidationErrors && state.activeTab === "url" ? "border-destructive" : ""
                        }`}
                      disabled={isProcessing}
                    />
                    {hasValidationErrors && state.activeTab === "url" && (
                      <div className="mt-2 text-sm text-destructive flex items-center">
                        <XCircle className="w-4 h-4 mr-1" />
                        {state.validationErrors[0]}
                      </div>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="upload" className="space-y-4">
                  <div>
                    <Label htmlFor="pdf-file" className="text-foreground font-lato">
                      Arquivo PDF (máx. {UPLOAD_CONFIG.MAX_FILE_SIZE / (1024 * 1024)}MB)
                    </Label>
                    <div className="mt-2 flex items-center justify-center w-full">
                      <label
                        htmlFor="pdf-file"
                        className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer transition-colors duration-300 ${isProcessing ? "opacity-50 cursor-not-allowed" : "hover:bg-surface-elevated"
                          } ${hasValidationErrors && state.activeTab === "upload"
                            ? "border-destructive bg-destructive/5"
                            : "border-border bg-surface"
                          }`}
                      >
                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                          {state.processingState === "uploading" ? (
                            <Loader2 className="w-8 h-8 mb-4 text-primary animate-spin" />
                          ) : hasValidationErrors && state.activeTab === "upload" ? (
                            <XCircle className="w-8 h-8 mb-4 text-destructive" />
                          ) : state.selectedFile ? (
                            <CheckCircle className="w-8 h-8 mb-4 text-green-500" />
                          ) : (
                            <Upload className="w-8 h-8 mb-4 text-foreground-muted" />
                          )}
                          <p className="mb-2 text-sm text-foreground-muted font-lato">
                            {state.processingState === "uploading" ? (
                              <span>Enviando... {state.uploadProgress}%</span>
                            ) : (
                              <span>
                                <span className="font-semibold">Clique para enviar</span> ou arraste o arquivo
                              </span>
                            )}
                          </p>
                          <p className="text-xs text-foreground-muted">
                            PDF (MAX. {UPLOAD_CONFIG.MAX_FILE_SIZE / (1024 * 1024)}MB)
                          </p>
                        </div>
                        <input
                          id="pdf-file"
                          type="file"
                          className="hidden"
                          accept=".pdf"
                          onChange={handleFileSelect}
                          disabled={isProcessing}
                        />
                      </label>
                    </div>

                    {state.selectedFile && (
                      <div className="flex items-center space-x-2 mt-2 p-3 bg-surface-elevated rounded-lg">
                        <FileText className="w-5 h-5 text-accent-orange" />
                        <span className="text-sm text-foreground font-lato">
                          {state.selectedFile.name}
                        </span>
                        <span className="text-xs text-foreground-muted ml-auto">
                          {(state.selectedFile.size / (1024 * 1024)).toFixed(2)}MB
                        </span>
                      </div>
                    )}

                    {hasValidationErrors && state.activeTab === "upload" && (
                      <div className="mt-2 text-sm text-destructive flex items-center">
                        <XCircle className="w-4 h-4 mr-1" />
                        {state.validationErrors[0]}
                      </div>
                    )}
                  </div>
                </TabsContent>
              </Tabs>

              {/* Progress bar para upload */}
              {state.processingState === "uploading" && (
                <div className="w-full bg-surface-elevated rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-300"
                    style={{ width: `${state.uploadProgress}%` }}
                  />
                </div>
              )}

              <div className="flex space-x-2">
                <Button
                  onClick={handleProcess}
                  disabled={isProcessing || !canProcess || hasValidationErrors}
                  className="btn-hero flex-1"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      {state.processingState === "validating" && "Validando..."}
                      {state.processingState === "uploading" && "Enviando..."}
                      {state.processingState === "processing" && "Processando..."}
                      {state.processingState === "polling" && "Aguardando resultado..."}
                    </>
                  ) : (
                    <>
                      <Brain className="w-5 h-5 mr-2" />
                      {state.activeTab === "upload" ? "Enviar e Analisar" : "Analisar com IA"}
                    </>
                  )}
                </Button>

                {(state.result || isProcessing) && (
                  <Button
                    onClick={handleReset}
                    variant="outline"
                    disabled={isProcessing}
                  >
                    Novo
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Status Cards */}
          <div className="grid md:grid-cols-3 gap-4">
            <div className="card-legal text-center p-4">
              <div className="text-2xl font-bebas text-accent-orange mb-1">99.7%</div>
              <div className="text-sm text-foreground-secondary font-lato">Precisão</div>
            </div>
            <div className="card-legal text-center p-4">
              <div className="text-2xl font-bebas text-primary mb-1">15s</div>
              <div className="text-sm text-foreground-secondary font-lato">Tempo médio</div>
            </div>
            <div className="card-legal text-center p-4">
              <div className="text-2xl font-bebas text-primary-light mb-1">24/7</div>
              <div className="text-sm text-foreground-secondary font-lato">Disponível</div>
            </div>
          </div>
        </div>

        {/* Result Section */}
        <div className="space-y-6 sm:space-y-8">
          <div className="text-center lg:text-left">
            <h2 className="text-2xl sm:text-3xl font-bebas text-gradient mb-4 leading-tight">
              Resultado da Análise
            </h2>
            <p className="text-base sm:text-lg text-foreground-secondary font-lato">
              Dados estruturados prontos para uso
            </p>
          </div>

          {state.processingState === "idle" && !state.result && (
            <Card className="card-legal">
              <CardContent className="flex flex-col items-center justify-center p-12 text-center">
                <AlertCircle className="w-16 h-16 text-foreground-muted mb-4" />
                <h3 className="text-xl font-montserrat font-semibold text-foreground mb-2">
                  Aguardando análise
                </h3>
                <p className="text-foreground-secondary font-lato">
                  Selecione um PDF para começar o processamento
                </p>
              </CardContent>
            </Card>
          )}

          {isProcessing && (
            <Card className="card-legal">
              <CardContent className="flex flex-col items-center justify-center p-12 text-center">
                <Loader2 className="w-16 h-16 text-accent-orange animate-spin mb-4" />
                <h3 className="text-xl font-montserrat font-semibold text-foreground mb-2">
                  {state.processingState === "validating" && "Validando documento..."}
                  {state.processingState === "uploading" && "Enviando arquivo..."}
                  {state.processingState === "processing" && "Processando com IA..."}
                  {state.processingState === "polling" && "Aguardando processamento completar..."}
                </h3>
                <p className="text-foreground-secondary font-lato">
                  {state.processingState === "uploading" && `${state.uploadProgress}% concluído`}
                  {state.processingState === "processing" && "A IA está analisando o PDF"}
                  {state.processingState === "validating" && "Verificando arquivo e configurações"}
                  {state.processingState === "polling" && "O processamento pode levar alguns minutos para arquivos grandes"}
                </p>
              </CardContent>
            </Card>
          )}

          {state.processingState === "error" && (
            <Card className="card-legal border-destructive">
              <CardContent className="flex flex-col items-center justify-center p-12 text-center">
                <XCircle className="w-16 h-16 text-destructive mb-4" />
                <h3 className="text-xl font-montserrat font-semibold text-foreground mb-2">
                  Erro no processamento
                </h3>
                <p className="text-foreground-secondary font-lato mb-4">
                  Houve um problema ao processar o documento
                </p>
                <Button onClick={handleReset} variant="outline">
                  Tentar novamente
                </Button>
              </CardContent>
            </Card>
          )}

          {state.result && state.processingState === "completed" && (
            <div
              ref={resultRef}
              className="mt-8 sm:mt-12 pt-6 sm:pt-8 border-t border-border/30 animate-fade-in"
            >
              <div className="mb-4 sm:mb-6 text-center animate-fade-in-up">
                <div className="inline-flex items-center space-x-2 bg-primary/10 text-primary px-3 sm:px-4 py-2 rounded-full border border-primary/20 shadow-glow">
                  <Brain className="w-4 sm:w-5 h-4 sm:h-5 animate-pulse" />
                  <span className="font-montserrat font-semibold text-sm sm:text-base">Resultados da Análise</span>
                </div>
              </div>
              <div className="animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                <ProcessResult data={state.result} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFProcessor;