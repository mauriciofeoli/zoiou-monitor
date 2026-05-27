import { Link, useNavigate } from "@tanstack/react-router";
import { Eye, LogOut, Settings } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/use-auth";

export function Header() {
  const { usuario, sair } = useAuth();
  const navigate = useNavigate();

  async function handleSair() {
    await sair();
    toast.success("Até logo!");
    navigate({ to: "/login" });
  }

  return (
    <header className="border-b border-border/70 bg-background/80 backdrop-blur sticky top-0 z-40">
      <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <span className="relative inline-flex h-9 w-9 items-center justify-center rounded-full bg-ink text-background">
            <Eye className="h-5 w-5" strokeWidth={2.2} />
          </span>
          <span className="font-serif text-2xl leading-none">
            zoiou<span className="text-success">.</span>
          </span>
        </Link>

        <nav className="flex items-center gap-1 text-sm">
          <Link
            to="/"
            activeOptions={{ exact: true }}
            activeProps={{ className: "bg-secondary text-foreground" }}
            className="px-3 py-2 rounded-md text-muted-foreground hover:text-foreground transition-colors"
          >
            Lista
          </Link>
          <Link
            to="/configuracoes"
            activeProps={{ className: "bg-secondary text-foreground" }}
            className="px-3 py-2 rounded-md text-muted-foreground hover:text-foreground transition-colors inline-flex items-center gap-1.5"
          >
            <Settings className="h-4 w-4" /> Preferências
          </Link>

          {usuario && (
            <div className="ml-2 flex items-center gap-2 pl-2 border-l border-border">
              <span className="hidden sm:block text-xs text-muted-foreground truncate max-w-[140px]">
                {usuario.email}
              </span>
              <button
                type="button"
                onClick={handleSair}
                title="Sair"
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/5 transition-colors text-sm"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sair</span>
              </button>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
