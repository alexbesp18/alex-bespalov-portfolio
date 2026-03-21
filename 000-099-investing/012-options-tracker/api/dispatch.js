export default async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(200).end();
  }
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  const { ticker } = req.body || {};
  if (!ticker || !/^[A-Z]{1,5}$/.test(ticker)) {
    return res.status(400).json({ error: 'Invalid ticker' });
  }

  const token = process.env.GH_PAT;
  if (!token) return res.status(500).json({ error: 'GH_PAT not configured' });

  const ghRes = await fetch(
    'https://api.github.com/repos/alexbesp18/options-tracker/actions/workflows/add_ticker.yml/dispatches',
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github.v3+json' },
      body: JSON.stringify({ ref: 'master', inputs: { ticker } }),
    }
  );

  if (ghRes.ok || ghRes.status === 204) {
    return res.status(200).json({ ok: true, ticker, message: `Triggered add_ticker for ${ticker}` });
  }
  const err = await ghRes.text();
  return res.status(ghRes.status).json({ error: err });
}
