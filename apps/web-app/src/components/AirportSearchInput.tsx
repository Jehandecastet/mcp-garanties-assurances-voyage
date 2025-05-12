// instantair-app/src/components/AirportSearchInput.tsx
'use client';

import { useState, useEffect } from 'react';

type Airport = {
  name: string;
  iata: string;
  city: string;
  country: string;
};

type Props = {
  placeholder: string;
  onSelect: (iata: string) => void;
  onChange?: (value: string) => void;   
  proxyUrl: string;
  /** Valeur contrôlée pour pré-remplissage */
  value?: string;
};

export default function AirportSearchInput({ placeholder, onSelect, proxyUrl, value }: Props) {
  const [query, setQuery] = useState(value ?? '');
  const [results, setResults] = useState<Airport[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);

  // Synchroniser query si value change
  useEffect(() => {
    if (value !== undefined) {
    setQuery(value);
   }
 }, [value]);   // ← only when prop changes


  // Recherche des aéroports
  useEffect(() => {
    const fetchAirports = async () => {
      if (query.length < 3) {
        setResults([]);
        setShowDropdown(false);
        return;
      }
      try {
        const res = await fetch(`${proxyUrl}/api/airports?search=${encodeURIComponent(query)}`);
        const data = await res.json();
        const items = data.items || [];
        const mappedResults = items.map((airport: any) => ({
          name: airport.name,
          iata: airport.iata,
          city: airport.city || '',
          country: airport.country || '',
        }));
        setResults(mappedResults);
        setShowDropdown(true);
      } catch (err) {
        console.error('Erreur recherche aéroports:', err);
      }
    };

    const timer = setTimeout(fetchAirports, 300);
    return () => clearTimeout(timer);
  }, [query, proxyUrl]);

  const handleSelect = (airport: Airport) => {
    onSelect(airport.iata);
    setQuery(`${airport.name} (${airport.iata})`);
    setShowDropdown(false);
  };

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => {
    const v = e.target.value;
    setQuery(v);
    onChange?.(v);                 // ← notify parent
  }}
        placeholder={placeholder}
        className="block border p-2 my-2 w-full"
      />
      {showDropdown && results.length > 0 && (
        <ul className="absolute z-50 bg-white border border-gray-300 w-full shadow-lg max-h-60 overflow-auto">
          {results.map((airport, index) => (
            <li
              key={`${airport.iata}-${index}`}
              onClick={() => handleSelect(airport)}
              className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
            >
              ✈️ {airport.name} ({airport.iata}){airport.city && ` - ${airport.city}`}{airport.country && ` (${airport.country})`}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
