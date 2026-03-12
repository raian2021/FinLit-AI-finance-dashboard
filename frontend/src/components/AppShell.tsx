"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { removeToken } from "@/lib/auth";

const NavItem = ({
  href,
  label,
}: {
  href: string;
  label: string;
}) => (
  <Link
    href={href}
    className="block rounded-lg px-3 py-2 text-sm font-medium text-foreground/80 hover:text-foreground hover:bg-muted transition"
  >
    {label}
  </Link>
);

export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();

  const handleLogout = () => {
    removeToken();
    router.push('/login');
  };

  return (
    <div className="min-h-screnn bg-muted/40">
      <div className="flec min-h-screen">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-lg font-semibold tracking-tight">FinLit</div>
            <Badge variant="secondary">MVP</Badge>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-muted-foreground">
              Education, not advice
            </div>
            <button
              onClick={handleLogout}
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              Logout
            </button>
          </div>
        </header>

        <Separator className="my-5" />

        <div className="grid gap-6 md:grid-cols-[240px_1fr]">
          <aside className="rounded-2xl border bg-card p-3 h-fit">
            <div className="px-3 py-2 text-xs font-medium text-muted-foreground">
              Navigation
            </div>
            <nav className="space-y-1">
              <NavItem href="/" label="Overview" />
              <NavItem href="/transactions" label="Transactions (soon)" />
              <NavItem href="/insights" label="AI Insights (soon)" />
              <NavItem href="/settings" label="Settings (soon)" />
            </nav>
          </aside>

          <main className="space-y-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
