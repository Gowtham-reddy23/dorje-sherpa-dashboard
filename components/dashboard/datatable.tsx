"use client"

import * as React from "react"
import type { SortDescriptor } from "react-aria-components"
import { DownloadIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { download, toCsv } from "@/lib/attr"
import { Info } from "./kit"

export type Col<T> = { key: keyof T & string; label: string; align?: "right"; help?: string; fmt?: (v: T[keyof T], row: T) => React.ReactNode; csv?: (row: T) => string | number }

/** Sortable table (click a column header) with CSV export of the rows currently shown. */
export function DataTable<T extends Record<string, unknown>>({ label, cols, rows, file, initial, rowKey, max }: {
  label: string; cols: Col<T>[]; rows: T[]; file: string; initial?: SortDescriptor; rowKey: (r: T) => string; max?: number
}) {
  const [sort, setSort] = React.useState<SortDescriptor>(initial ?? { column: cols[1]?.key ?? cols[0].key, direction: "descending" })
  const [all, setAll] = React.useState(false)
  const sorted = React.useMemo(() => {
    const k = sort.column as keyof T
    return [...rows].sort((x, y) => {
      const va = x[k] ?? -Infinity, vb = y[k] ?? -Infinity
      const r = typeof va === "string" || typeof vb === "string" ? String(va).localeCompare(String(vb)) : Number(va) - Number(vb)
      return sort.direction === "descending" ? -r : r
    })
  }, [rows, sort])
  const shown = max && !all ? sorted.slice(0, max) : sorted
  const exportCsv = () => download(file, toCsv(cols.map((c) => ({ key: c.key, label: c.label })), sorted.map((r) => Object.fromEntries(cols.map((c) => [c.key, c.csv ? c.csv(r) : r[c.key]])))))
  return (
    <div className="flex flex-col gap-2">
      <Table aria-label={label} sortDescriptor={sort} onSortChange={setSort}>
        <TableHeader>
          {cols.map((c, i) => (
            <TableHead key={c.key} id={c.key} isRowHeader={i === 0} allowsSorting className={c.align === "right" ? "text-right" : ""}>
              <span className="inline-flex items-center gap-1">{c.label}{c.help && <Info text={c.help} />}</span>
            </TableHead>
          ))}
        </TableHeader>
        <TableBody renderEmptyState={() => <span className="text-muted-foreground">No orders match these filters</span>}>
          {shown.map((r) => (
            <TableRow key={rowKey(r)} id={rowKey(r)}>
              {cols.map((c) => <TableCell key={c.key} className={c.align === "right" ? "text-right tabular-nums whitespace-nowrap" : "max-w-72"}>{c.fmt ? c.fmt(r[c.key], r) : String(r[c.key] ?? "–")}</TableCell>)}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
        <span>{sorted.length} rows · click a column to sort</span>
        <div className="flex gap-2">
          {max && sorted.length > max && <Button variant="ghost" size="sm" onPress={() => setAll(!all)}>{all ? "Show fewer" : `Show all ${sorted.length}`}</Button>}
          <Button variant="outline" size="sm" onPress={exportCsv}><DownloadIcon /> CSV</Button>
        </div>
      </div>
    </div>
  )
}
