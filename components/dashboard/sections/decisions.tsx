"use client"

import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Dash } from "@/lib/dash"
import { Estimate, Tone } from "../kit"

export function Decisions({ d }: { d: Dash }) {
  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">Each card is one decision for the founders. Impact uses our own numbers; projections are marked Estimate.</p>
      <div className="grid gap-4 md:grid-cols-2">
        {d.decisions.map((x) => (
          <Card key={x.n}>
            <CardHeader>
              <CardDescription>Decision {x.n}</CardDescription>
              <CardTitle className="text-base">{x.ask}</CardTitle>
              <CardAction><Tone tone={x.tone}>{x.tone === "danger" ? "Urgent" : x.tone === "warning" ? "This month" : "Next"}</Tone></CardAction>
            </CardHeader>
            <CardContent className="flex flex-col gap-2 text-sm">
              <p><span className="font-medium">Why: </span><span className="text-muted-foreground">{x.why}</span></p>
              <p className="flex flex-wrap items-center gap-1.5"><span className="font-medium">Expected impact: </span>{x.impact.startsWith("Estimate") && <Estimate />}<span className="text-muted-foreground">{x.impact.replace(/^Estimate:\s*/, "")}</span></p>
              <p><span className="font-medium">We recommend: </span>{x.rec}</p>
            </CardContent>
            <CardFooter className="flex flex-wrap gap-2 text-xs">
              <Badge variant="outline">Owner: {x.owner}</Badge>
              <Badge variant="secondary">Status: {x.status}</Badge>
            </CardFooter>
          </Card>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">{d.amazonPublic} Amazon is not connected yet.</p>
    </div>
  )
}
