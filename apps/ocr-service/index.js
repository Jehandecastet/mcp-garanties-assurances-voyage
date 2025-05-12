// instantair-ocr-service/index.js
import 'dotenv/config'
import express from 'express'
import { createReadStream } from 'fs'
import { promises as fs } from 'fs'
import { IncomingForm } from 'formidable'
import Axios from 'axios'
import FormData from 'form-data'

const app = express()
const PORT = process.env.PORT || 4000

// Configuration de l'API Mindee
const MINDEE_API_KEY = process.env.MINDEE_API_KEY
const MINDEE_ORG_SLUG = process.env.MINDEE_ORG_SLUG || 'judelorme'
const MINDEE_BASE_URL = 'https://api.mindee.net/v1/products'
const API_NAME = 'boarding_pass'
const API_VERSION = 'v1'

if (!MINDEE_API_KEY) {
  console.error('Erreur: MINDEE_API_KEY doit être définie')
  process.exit(1)
}

// Parser le multipart/form-data
function parseForm(req) {
  return new Promise((resolve, reject) => {
    const form = new IncomingForm({ multiples: false, keepExtensions: true })
    form.parse(req, (err, fields, files) => err ? reject(err) : resolve(files))
  })
}

// Soumettre le document et récupérer la polling URL
async function submitAsync(filepath) {
  const formData = new FormData()
  formData.append('document', createReadStream(filepath))
  const url = `${MINDEE_BASE_URL}/${MINDEE_ORG_SLUG}/${API_NAME}/${API_VERSION}/predict_async`
  const response = await Axios.post(url, formData, {
    headers: {
      ...formData.getHeaders(),
      Authorization: `Token ${MINDEE_API_KEY}`
    }
  })
  const { job } = response.data
  if (!job?.polling_url) throw new Error('polling_url non récupérée')
  return job.polling_url
}

// Polling jusqu'à completion
async function fetchResult(pollingUrl) {
  for (let i = 0; i < 30; i++) {
    const res = await Axios.get(pollingUrl, {
      headers: { Authorization: `Token ${MINDEE_API_KEY}` }
    })
    const { job, document } = res.data
    if (job?.status === 'completed' && document?.inference) {
      return document.inference
    }
    if (job?.status === 'failed') throw new Error('OCR a échoué')
    await new Promise(r => setTimeout(r, 1000))
  }
  throw new Error('Délai d’attente dépassé')
}

// Extraction des champs selon la structure DOC/MINDIDOC
function extractFields(inference) {
  // Récupère prediction top-level
  const docPred = inference.prediction || {}
  // Récupère prédiction page-level du premier page
  const pagePred = inference.pages?.[0]?.prediction || {}
  // Fusionne les deux
  const preds = { ...pagePred, ...docPred }

  // Helper pour prendre le premier champ non-null par motif
  const pick = (prefix) => {
    const keys = Object.keys(preds).filter(k => k.startsWith(prefix))
    for (const k of keys.sort()) {
      const val = preds[k]?.value || preds[k]
      if (val != null) return typeof val === 'object' ? val.text : val
    }
    return null
  }

  return {
    departureCity: pick('departure_city') || pick('departure_airport'),
    arrivalCity:   pick('destination_city') || pick('arrival_airport'),
    flightNumber:  pick('flight_number'),
    flightDate:    pick('departure_date')
  }
}

// Route POST /parse
app.post('/parse', async (req, res) => {
  try {
    const files = await parseForm(req)
    const raw = Array.isArray(files.file) ? files.file[0] : files.file
    const filepath = raw.filepath || raw.filePath || raw.path
    if (!filepath) return res.status(400).json({ message: 'Aucun fichier reçu' })

    const pollingUrl = await submitAsync(filepath)
    const inference = await fetchResult(pollingUrl)
    const output = extractFields(inference)

    await fs.unlink(filepath).catch(() => {})
    res.json(output)
  } catch (err) {
    console.error('OCR error:', err)
    res.status(500).json({ error: err.message || String(err) })
  }
})

app.listen(PORT, () => console.log(`OCR service listening on ${PORT}`))
