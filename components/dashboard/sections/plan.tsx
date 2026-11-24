"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { Dash } from "@/lib/dash"

const LABEL: Record<string, [string, string]> = { "30": ["First 30 days", "Stop the leaks and restart growth"], "60": ["Days 31–60", "Own the customer relationship"], "90": ["Days 61–90", "Scale what works"] }

export function Plan({ d }: { d: Dash }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {Object.entries(d.plan).map(([k, groups]) => (
        <Card key={k}>
          <CardHeader>
            <CardTitle>{LABEL[k]?.[0] ?? k}</CardTitle>
            <CardDescription>{LABEL[k]?.[1]}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {groups.map((g) => (
              <div key={g.title}>
                <div className="mb-1 text-sm font-medium">{g.title}</div>
                <ol className="flex list-decimal flex-col gap-1 pl-5 text-sm text-muted-foreground">{g.items.map((i) => <li key={i}>{i}</li>)}</ol>
              </div>
            ))}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
