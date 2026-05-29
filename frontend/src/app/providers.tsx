"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider, useTheme } from "next-themes";
import { useState } from "react";
import { Toaster } from "sonner";
import { AuthProvider } from "@/hooks/use-auth";

function ToasterWithTheme() {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";
  return (
    <Toaster
      richColors
      position="top-right"
      theme={isDark ? "dark" : "light"}
      style={
        {
          "--success-bg": isDark ? "oklch(0.12 0.05 250)" : "oklch(0.95 0.04 250)",
          "--success-border": isDark ? "oklch(0.22 0.1 250)" : "oklch(0.85 0.08 250)",
          "--success-text": isDark ? "oklch(0.68 0.2 250)" : "oklch(0.52 0.22 245)",
        } as React.CSSProperties
      }
    />
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          {children}
          <ToasterWithTheme />
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
