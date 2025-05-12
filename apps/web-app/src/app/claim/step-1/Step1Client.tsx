// instantair-app/src/app/claim/step-1/Step1Client.tsx
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { useFormData } from '@/context/formContext';

const AirportSearchInput = dynamic(
  () => import('@/components/AirportSearchInput'),
  { ssr: false }
);

export default function Step1({ proxyUrl }: { proxyUrl: string }) {
  const { formData, updateForm } = useFormData();
  const router = useRouter();

  const initialFlight = formData.flight || {
    departure: '',
    arrival: '',
    number: '',
    date: '',
    problemType: ''
  };
  const [flight, setFlight] = useState(initialFlight);

  

  const handleNext = () => {
    updateForm({
      flight,
      flightNumber: flight.number,
      flightDate: flight.date
    });
    router.push('/claim/step-2');
  };

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Vérification d'éligibilité</h1>

      <AirportSearchInput
        placeholder="Aéroport de départ"
        value={flight.departure}
        // onChange permet la saisie libre
        onChange={(text: string) => setFlight({ ...flight, departure: text })}
        // onSelect remplace la valeur par le code IATA choisi
        onSelect={(iata: string) => setFlight({ ...flight, departure: iata })}
        proxyUrl={proxyUrl}
      />

      <AirportSearchInput
        placeholder="Aéroport d'arrivée"
        value={flight.arrival}
        onChange={(text: string) => setFlight({ ...flight, arrival: text })}
        onSelect={(iata: string) => setFlight({ ...flight, arrival: iata })}
        proxyUrl={proxyUrl}
      />

      <input
        placeholder="Numéro de vol"
        className="block border p-2 my-2 w-full"
        value={flight.number}
        onChange={(e) => setFlight({ ...flight, number: e.target.value })}
      />

      <input
        type="date"
        className="block border p-2 my-2 w-full"
        value={flight.date}
        onChange={(e) => setFlight({ ...flight, date: e.target.value })}
      />

      <select
        className="block border p-2 my-2 w-full"
        value={flight.problemType}
        onChange={(e) => setFlight({ ...flight, problemType: e.target.value })}
      >
        <option value="">Type de problème</option>
        <option value="retard">Retard</option>
        <option value="annulation">Annulation</option>
      </select>

      <button
        className="mt-4 bg-blue-600 text-white px-4 py-2 rounded"
        onClick={handleNext}
      >
        Continuer
      </button>
    </div>
  );
}
