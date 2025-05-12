export default async function handler(req, res) {
    // ✅ Ajoute ces headers CORS
    res.setHeader('Access-Control-Allow-Origin', '*'); // tu peux aussi spécifier ton domaine pour plus de sécurité
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-RapidAPI-Key, X-RapidAPI-Host');

  
    // ✅ Si la requête est un pré-flight OPTIONS, réponds directement
    if (req.method === 'OPTIONS') {
      return res.status(200).end();
    }
  
    try {
      const { search } = req.query;
  
      const response = await fetch(`https://aerodatabox.p.rapidapi.com/airports/search/term?q=${search}&limit=5`, {
        method: 'GET',
        headers: {
          'X-RapidAPI-Key': process.env.RAPIDAPI_KEY,
          'X-RapidAPI-Host': 'aerodatabox.p.rapidapi.com'
        }
      });
  
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
  
      const data = await response.json();
      res.status(200).json(data);
  
    } catch (error) {
      console.error(error);
      res.status(500).json({ error: error.message });
    }
  }
  
