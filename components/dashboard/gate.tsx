"use client"

import * as React from "react"
import { LockIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { decrypt, type Dash } from "@/lib/dash"
import { App } from "./app"
import { closeAskSession, openAskSession } from "@/lib/ask-session"

const KEY = "dorje-founders-pass"

export function Gate() {
  const [data, setData] = React.useState<Dash | null>(null)
  const [pass, setPass] = React.useState("")
  const [state, setState] = React.useState<"idle" | "checking" | "wrong" | "error">("idle")

  const unlock = React.useCallback(async (p: string, remember: boolean) => {
    setState("checking")
    try {
      const res = await fetch("data.enc.json", { cache: "no-store" })
      if (!res.ok) throw new Error("fetch")
      const blob = await res.json()
      try {
        const d = await decrypt(blob, p)
        if (remember) sessionStorage.setItem(KEY, p)
        void openAskSession(p)
        setData(d)
        setState("idle")
      } catch {
        sessionStorage.removeItem(KEY)
        setState("wrong")
      }
    } catch {
      setState("error")
    }
  }, [])

  const [sample, setSample] = React.useState<{ passcode?: string; note?: string } | null>(null)
  React.useEffect(() => {
    fetch("sample-mode.json", { cache: "no-store" }).then((r) => (r.ok ? r.json() : null)).then((j) => j?.sample && setSample(j)).catch(() => {})
  }, [])

  React.useEffect(() => {
    const saved = sessionStorage.getItem(KEY)
    if (saved) void unlock(saved, false)
  }, [unlock])

  if (data) return <App data={data} onLock={() => { sessionStorage.removeItem(KEY); void closeAskSession(); setData(null); setPass("") }} />

  return (
    <main className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><LockIcon className="size-4" /> Dorje Teas — Founders Dashboard</CardTitle>
          <CardDescription>Private. Enter the passcode you were given. The numbers are encrypted and only unlock in your browser.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-3" onSubmit={(e) => { e.preventDefault(); void unlock(pass, true) }}>
            <Input type="password" autoComplete="current-password" placeholder="Passcode" aria-label="Passcode" value={pass} onChange={(e) => setPass(e.target.value)} autoFocus />
            <Button type="submit" isDisabled={!pass || state === "checking"}>{state === "checking" ? "Unlocking…" : "Open dashboard"}</Button>
            {state === "wrong" && <p className="text-sm text-destructive">That passcode didn&apos;t work.</p>}
            {state === "error" && <p className="text-sm text-destructive">Couldn&apos;t load the data. Refresh and try again.</p>}
          </form>
          {sample && (
            <p className="mt-3 rounded-md border border-dashed p-2 text-xs text-muted-foreground">
              <strong>Sample data mode.</strong> The numbers are fabricated for a demo. Passcode: <code>{sample.passcode}</code>. Ask Claude to &quot;Set me up&quot; to connect real data.
            </p>
          )}
        </CardContent>
      </Card>
    </main>
  )
}
