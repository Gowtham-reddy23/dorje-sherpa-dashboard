"use client"

import * as React from "react"
import { InfoIcon, PlugZapIcon, TrendingDownIcon, TrendingUpIcon } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardAction } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

export function Info({ text }: { text: string }) {
  return (
    <TooltipTrigger>
      <span role="button" tabIndex={0} aria-label="What does this mean?" className="inline-flex cursor-help text-muted-foreground hover:text-foreground">
        <InfoIcon className="size-3.5" />
      </span>
      <Tooltip className="max-w-72 text-xs leading-relaxed">{text}</Tooltip>
    </TooltipTrigger>
  )
}

export function Delta({ value, goodUp = true, suffix = "vs previous period" }: { value: number | null; goodUp?: boolean; suffix?: string }) {
  if (value === null || !isFinite(value)) return <span className="text-xs text-muted-foreground">No earlier data to compare</span>
  const up = value >= 0
  const good = Math.abs(value) < 2 ? null : up === goodUp
  const Icon = up ? TrendingUpIcon : TrendingDownIcon
  return (
    <span className={cn("inline-flex items-center gap-1 text-xs", good === null ? "text-muted-foreground" : good ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400")}>
      <Icon className="size-3.5" />
      {up ? "+" : "−"}{Math.abs(value).toFixed(0)}% <span className="text-muted-foreground">{suffix}</span>
    </span>
  )
}

export function Kpi({ label, value, help, delta, goodUp, sub }: { label: string; value: string; help: string; delta?: number | null; goodUp?: boolean; sub?: string }) {
  return (
    <Card size="sm" className="gap-1">
      <CardHeader>
        <CardDescription className="flex items-center gap-1.5">{label} <Info text={help} /></CardDescription>
        <CardTitle className="text-2xl! font-semibold tabular-nums">{value}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-0.5">
        {delta !== undefined && <Delta value={delta} goodUp={goodUp} />}
        {sub && <span className="text-xs text-muted-foreground">{sub}</span>}
      </CardContent>
    </Card>
  )
}

export function Panel({ title, help, description, action, children, className }: { title: string; help?: string; description?: React.ReactNode; action?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <Card className={cn("min-w-0", className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-1.5">{title} {help && <Info text={help} />}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
        {action && <CardAction>{action}</CardAction>}
      </CardHeader>
      <CardContent className="min-w-0">{children}</CardContent>
    </Card>
  )
}

export function NotConnected({ name, what }: { name: string; what: string }) {
  return (
    <Card size="sm" className="border-dashed">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm"><PlugZapIcon className="size-4 text-muted-foreground" />{name}</CardTitle>
        <CardAction><Badge variant="outline">Not connected</Badge></CardAction>
        <CardDescription>{what}</CardDescription>
      </CardHeader>
    </Card>
  )
}

export function Tone({ tone, children }: { tone?: string; children: React.ReactNode }) {
  const cls = tone === "danger" ? "bg-red-500/10 text-red-700 dark:text-red-300" : tone === "warning" ? "bg-amber-500/15 text-amber-800 dark:text-amber-300" : tone === "success" ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" : "bg-muted text-muted-foreground"
  return <Badge variant="secondary" className={cls}>{children}</Badge>
}

export function Estimate() {
  return <Badge variant="outline" className="border-amber-500/40 text-amber-700 dark:text-amber-300">Estimate</Badge>
}

export function Grid({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("grid gap-3 grid-cols-2 md:grid-cols-3 xl:grid-cols-4", className)}>{children}</div>
}

/** Plain responsive table (static content). */
export function SimpleTable({ columns, rows, align }: { columns: string[]; rows: React.ReactNode[][]; align?: ("left" | "right")[] }) {
  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            {columns.map((c, i) => <th key={c} className={cn("h-9 px-2 font-medium text-muted-foreground whitespace-nowrap", align?.[i] === "right" ? "text-right" : "text-left")}>{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b last:border-0 hover:bg-muted/40">
              {r.map((c, j) => <td key={j} className={cn("p-2 align-top", align?.[j] === "right" ? "text-right tabular-nums whitespace-nowrap" : "")}>{c}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
