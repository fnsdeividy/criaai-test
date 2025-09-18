import { useState, useEffect, useRef } from "react";
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
  AlertCircle
} from "lucide-react";

const PDFProcessor = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [pdfUrl, setPdfUrl] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [activeTab, setActiveTab] = useState("url");
  const { toast } = useToast();
  const resultRef = useRef<HTMLDivElement>(null);

  // API Configuration
  const API_BASE_URL = "http://localhost:8000";

  // Scroll automático para o resultado quando ele aparecer
  useEffect(() => {
    if (result && resultRef.current) {
      // Aguardar um pouco para garantir que o DOM foi atualizado
      setTimeout(() => {
        // Scroll suave para o resultado com offset para melhor visualização
        const elementPosition = resultRef.current.getBoundingClientRect().top + window.pageYOffset;
        const offsetPosition = elementPosition - 80; // 80px de offset do topo

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });

        // Feedback visual adicional
        toast({
          title: "✨ Análise concluída!",
          description: "Role para baixo para ver os resultados detalhados.",
          duration: 4000,
        });
      }, 500); // 500ms de delay para garantir que as animações terminem
    }
  }, [result, toast]);

  const handleProcess = async () => {
    if (!pdfUrl && !selectedFile) {
      toast({
        title: "Erro",
        description: "Por favor, forneça uma URL ou selecione um arquivo PDF.",
        variant: "destructive"
      });
      return;
    }

    setIsProcessing(true);

    try {
      let response;

      if (activeTab === "url" && pdfUrl) {
        // Processar via URL
        const requestData = {
          pdf_url: pdfUrl,
          case_id: `case_${Date.now()}`
        };

        response = await fetch(`${API_BASE_URL}/extract`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestData)
        });
      } else if (activeTab === "upload" && selectedFile) {
        // Processar via upload de arquivo
        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("case_id", `case_${Date.now()}`);

        response = await fetch(`${API_BASE_URL}/upload`, {
          method: "POST",
          body: formData
        });
      }

      if (!response) {
        throw new Error("Nenhuma resposta da API");
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro no processamento");
      }

      const data = await response.json();
      setResult(data);

      toast({
        title: "Processamento concluído!",
        description: "O PDF foi analisado com sucesso.",
      });

    } catch (error: any) {
      console.error("Erro no processamento:", error);
      toast({
        title: "Erro no processamento",
        description: error.message || "Falha ao processar o PDF. Verifique se a API está rodando.",
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setPdfUrl("");
    } else {
      toast({
        title: "Arquivo inválido",
        description: "Por favor, selecione apenas arquivos PDF.",
        variant: "destructive"
      });
    }
  };


  return (
    <div className="container mx-auto px-6 py-12 max-w-7xl">
      <div className="grid lg:grid-cols-2 gap-12">
        {/* Input Section */}
        <div className="space-y-8">
          <div className="text-center lg:text-left">
            <h1 className="text-4xl lg:text-5xl font-bebas text-gradient mb-4">
              Analisador de PDFs Jurídicos
            </h1>
            <p className="text-xl text-foreground-secondary font-lato">
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
              <Tabs value={activeTab} onValueChange={setActiveTab}>
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
                      value={pdfUrl}
                      onChange={(e) => {
                        setPdfUrl(e.target.value);
                        setSelectedFile(null);
                      }}
                      className="mt-2 bg-surface border-border text-foreground"
                    />
                  </div>
                </TabsContent>

                <TabsContent value="upload" className="space-y-4">
                  <div>
                    <Label htmlFor="pdf-file" className="text-foreground font-lato">
                      Arquivo PDF
                    </Label>
                    <div className="mt-2 flex items-center justify-center w-full">
                      <label
                        htmlFor="pdf-file"
                        className="flex flex-col items-center justify-center w-full h-32 border-2 border-border border-dashed rounded-xl cursor-pointer bg-surface hover:bg-surface-elevated transition-colors duration-300"
                      >
                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                          <Upload className="w-8 h-8 mb-4 text-foreground-muted" />
                          <p className="mb-2 text-sm text-foreground-muted font-lato">
                            <span className="font-semibold">Clique para enviar</span> ou arraste o arquivo
                          </p>
                          <p className="text-xs text-foreground-muted">PDF (MAX. 14MB)</p>
                        </div>
                        <input
                          id="pdf-file"
                          type="file"
                          className="hidden"
                          accept=".pdf"
                          onChange={handleFileSelect}
                        />
                      </label>
                    </div>
                    {selectedFile && (
                      <div className="flex items-center space-x-2 mt-2 p-3 bg-surface-elevated rounded-lg">
                        <FileText className="w-5 h-5 text-accent-orange" />
                        <span className="text-sm text-foreground font-lato">{selectedFile.name}</span>
                      </div>
                    )}
                  </div>
                </TabsContent>
              </Tabs>

              <Button
                onClick={handleProcess}
                disabled={isProcessing}
                className="btn-hero w-full"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    {activeTab === "upload" ? "Enviando e processando..." : "Baixando e processando..."}
                  </>
                ) : (
                  <>
                    <Brain className="w-5 h-5 mr-2" />
                    {activeTab === "upload" ? "Enviar e Analisar com IA" : "Analisar com Google Gemini"}
                  </>
                )}
              </Button>
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
        <div className="space-y-8">
          <div className="text-center lg:text-left">
            <h2 className="text-3xl font-bebas text-gradient mb-4">
              Resultado da Análise
            </h2>
            <p className="text-lg text-foreground-secondary font-lato">
              Dados estruturados prontos para uso
            </p>
          </div>

          {!result && !isProcessing && (
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
                  Processando documento...
                </h3>
                <p className="text-foreground-secondary font-lato">
                  A IA está analisando o PDF e extraindo informações
                </p>
              </CardContent>
            </Card>
          )}

          {result && (
            <div
              ref={resultRef}
              className="mt-12 pt-8 border-t border-border/30 animate-fade-in"
            >
              <div className="mb-6 text-center animate-fade-in-up">
                <div className="inline-flex items-center space-x-2 bg-primary/10 text-primary px-4 py-2 rounded-full border border-primary/20 shadow-glow">
                  <Brain className="w-5 h-5 animate-pulse" />
                  <span className="font-montserrat font-semibold">Resultados da Análise</span>
                </div>
              </div>
              <div className="animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                <ProcessResult data={result} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFProcessor;