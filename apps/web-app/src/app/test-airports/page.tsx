'use client';

import { useState } from 'react';

export default function TestAirports() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState('');

  const fetchAirports = async () => {
    try {
      const res = await fetch(`/api/airports?search=${query}`);
      if (!res.ok) throw new Error(`Erreur HTTP: ${res.status}`);
      const data = await res.json();
      setResults(data.items || []);
      setError('');
    } catch (err: any) {
      setError(err.message);
      setResults([]);
    }
  };

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h1 className="text-xl font-bold mb-4">🔍 Test recherche aéroports</h1>
      <input
        className="border p-2 w-full mb-2"
        placeholder="Saisir un nom d'aéroport ou une ville"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded"
        onClick={fetchAirports}
      >
        Rechercher
      </button>

      {error && <p className="text-red-600 mt-4">❌ {error}</p>}

      <ul className="mt-4 space-y-2">
        {results.map((airport, i) => (
          <li key={i} className="border p-2 rounded">
            ✈️ <strong>{airport.name}</strong> ({airport.iata}) — {airport.city}, {airport.country}
          </li>
        ))}
      </ul>
    </div>
  );
}
