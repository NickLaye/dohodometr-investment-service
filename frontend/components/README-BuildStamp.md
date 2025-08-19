### BuildStamp component

Purpose: Display current deployed build info from `/version.json`.

Usage options:
- Inline in footer:
```tsx
import BuildStamp from './BuildStamp'

export default function Footer() {
  return (
    <footer>
      <BuildStamp inline />
    </footer>
  )
}
```

- On-demand overlay for debugging: open any page with `?debug=1` query to see a floating build stamp in bottom-right.

Data source:
- Generated at build time by `scripts/write-build-meta.js` into `public/version.json`


