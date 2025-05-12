// instantair-app/src/pages/api/parseBoardingPass.js
import { NextApiRequest, NextApiResponse } from 'next'

export const config = { api: { bodyParser: false } }

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    return res.status(405).end('Method Not Allowed')
  }

  const OCR_URL = process.env.PARSE_BP_API_URL || 'http://localhost:4000/parse'
  console.log('📡 Proxy vers OCR @', OCR_URL)

  try {
    const ocrRes = await fetch(OCR_URL, {
      method: 'POST',
      headers: {
        // Preserve multipart boundary
        'Content-Type': req.headers['content-type']
      },
      // Pass the raw request stream
      body: req,
      // Required by Node.js fetch when sending a stream
      duplex: 'half'
    })
    const data = await ocrRes.json()
    return res.status(200).json(data)
  } catch (err) {
    console.error('Erreur proxy OCR:', err)
    return res.status(500).json({ message: 'OCR proxy failed', detail: err.message })
  }
}
