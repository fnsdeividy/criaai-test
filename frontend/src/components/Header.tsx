const Header = () => {
  return (
    <header className="border-b border-border bg-surface/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="text-3xl font-bebas text-gradient">
              PDF.AI
            </div>
            <div className="hidden md:block text-foreground-secondary font-lato">
              Processamento Inteligente de PDFs Jurídicos
            </div>
          </div>

          <div className="flex items-center space-x-6 text-sm text-foreground-muted">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-accent-orange rounded-full animate-pulse"></div>
              <span>Sistema Ativo</span>
            </div>
            <div className="hidden md:flex items-center space-x-2">
              <div className="w-2 h-2 bg-primary rounded-full"></div>
              <span>Google Gemini IA</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;