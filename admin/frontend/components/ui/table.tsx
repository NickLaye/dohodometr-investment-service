import * as React from 'react'
import { cn } from '../utils/cn'

export function Table({ className, ...props }: React.HTMLAttributes<HTMLTableElement>) {
  return <table className={cn('w-full border-collapse', className)} {...props} />
}
export function Thead(props: React.HTMLAttributes<HTMLTableSectionElement>) { return <thead {...props} /> }
export function Tbody(props: React.HTMLAttributes<HTMLTableSectionElement>) { return <tbody {...props} /> }
export function Tr(props: React.HTMLAttributes<HTMLTableRowElement>) { return <tr {...props} /> }
export function Th({ className, ...props }: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return <th className={cn('text-left border-b border-gray-200 py-2', className)} {...props} />
}
export function Td({ className, ...props }: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return <td className={cn('py-2', className)} {...props} />
}


