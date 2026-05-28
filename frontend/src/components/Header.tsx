"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Eye, LogOut, Moon, Settings, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/use-auth";

export function Header() {
  const { usuario, sair } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  async function handleSair() {
    await sair();
    toast.success("Até logo!");
    router.push("/login");
  }

  return (
    <header className="border-b border-border/70 bg-background/80 backdrop-blur sticky top-0 z-40">
      <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="relative inline-flex h-9 w-9 items-center justify-center rounded-full bg-ink text-background">
            <Eye className="h-5 w-5" strokeWidth={2.2} />
          </span>
          <span className="font-serif text-2xl leading-none">
            zoiou<span className="text-success">.</span>
          </span>
        </Link>

        <nav className="flex items-center gap-1 text-sm">
          <Link
            href="/"
            className={[
              "px-3 py-2 rounded-md transition-colors",
              pathname === "/"
                ? "bg-secondary text-foreground"
                : "text-muted-foreground hover:text-foreground",
            ].join(" ")}
          >
            Lista
          </Link>
          <Link
            href="/configuracoes"
            className={[
              "px-3 py-2 rounded-md transition-colors inline-flex items-center gap-1.5",
              pathname === "/configuracoes"
                ? "bg-secondary text-foreground"
                : "text-muted-foreground hover:text-foreground",
            ].join(" ")}
          >
            <Settings className="h-4 w-4" /> Preferências
          </Link>

          <button
            type="button"
            onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
            title="Alternar tema"
            className="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
          >
            {mounted && (resolvedTheme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />)}
          </button>

          {usuario && (
            <div className="ml-2 flex items-center gap-2 pl-2 border-l border-border">
              <span
                title={usuario.email}
                className="hidden sm:flex h-7 w-7 items-center justify-center rounded-full bg-secondary text-xs font-medium text-foreground select-none"
              >
                {usuario.email.split("@")[0].split(".").slice(0, 2).map((p: string) => p[0]).join("").toUpperCase() || usuario.email.slice(0, 2).toUpperCase()}
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
