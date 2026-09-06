import { Globe } from 'lucide-react'

export default function CapitalMarketsPage() {
  return (
    <div className="content-wrap">
      <div className="placeholder-state">
        <Globe size={40} />
        <div className="section-title" style={{ marginBottom: 8 }}>Global Capital Markets</div>
        <p>
          This page will display equity vs government bond markets, market size vs GDP,
          and historical evolution across 10 countries. Coming soon — Bond Analytics is live now.
        </p>
      </div>
    </div>
  )
}
