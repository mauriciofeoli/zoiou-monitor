import { useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { adicionarProduto } from "@/lib/api";

interface AdicionarProdutoModalProps {
  aberto: boolean;
  fechar: () => void;
}

export function AdicionarProdutoModal({ aberto, fechar }: AdicionarProdutoModalProps) {
  const queryClient = useQueryClient();
  const [url, setUrl] = useState("");
  const [adicionando, setAdicionando] = useState(false);

  if (!aberto) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setAdicionando(true);

    try {
      await adicionarProduto(url.trim());
      await queryClient.invalidateQueries({ queryKey: ["produtos"] });
      toast.success("Produto adicionado! O preço será capturado em breve.");
      setUrl("");
      fechar();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Não foi possível adicionar o produto.";
      toast.error(msg);
    } finally {
      setAdicionando(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/20 backdrop-blur-sm px-4"
      onClick={(e) => e.target === e.currentTarget && fechar()}
    >
      <div className="w-full max-w-md rounded-2xl bg-card border border-border shadow-lg p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-serif text-2xl text-ink">Adicionar produto</h2>
          <button
            type="button"
            onClick={fechar}
            className="rounded-full p-1.5 text-muted-foreground hover:bg-secondary transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-sm text-muted-foreground mb-5">
          Cole a URL do produto de qualquer loja. O Zoiou vai capturar o preço automaticamente e te
          avisar quando mudar.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="url-produto" className="block text-sm font-medium text-foreground mb-1.5">
              Link do produto
            </label>
            <input
              id="url-produto"
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.kabum.com.br/produto/..."
              className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={fechar}
              className="flex-1 rounded-full border border-border bg-background px-4 py-2.5 text-sm hover:bg-secondary transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={adicionando || !url.trim()}
              className="flex-1 rounded-full bg-foreground px-4 py-2.5 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-60 transition-colors flex items-center justify-center gap-2"
            >
              {adicionando ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              {adicionando ? "Adicionando..." : "Adicionar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
