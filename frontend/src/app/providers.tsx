"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider, useTheme } from "next-themes";
import { useState } from "react";
import { Toaster } from "sonner";
import { AuthProvider } from "@/hooks/use-auth";

function ToasterWithTheme() {
  const { resolvedTheme } = useTheme();
  return (
    <Toaster
      richColors
      position="top-right"
      theme={(resolvedTheme ?? "light") as "light" | "dark"}
      style={
        {
          "--success-bg": "oklch(0.62 0.2 250)",
          "--success-border": "oklch(0.55 0.2 250)",
          "--success-text": "oklch(1 0 0)",
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
