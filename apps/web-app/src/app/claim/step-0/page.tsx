// instantair-app/src/app/claim/step-0/page.tsx
'use client';

import { useFormData } from '@/context/formContext';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function Step0() {
  const router = useRouter();
  const { updateForm } = useFormData();

  // États pour l’upload de la carte
  const [bpLoading, setBpLoading] = useState(false);
  const [bpError, setBpError]     = useState<string | null>(null);

  // États pour la saisie manuelle
  const [flightData, setFlightData] = useState({
    departure: '',
    arrival: '',
    number: '',
    date: ''
  });
  const [manualError, setManualError] = useState<string | null>(null);

  // Handler upload carte d’embarquement
  const handleBpUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBpLoading(true);
    setBpError(null);

    try {
      const form = new FormData();
      form.append('file', file);

      const res = await fetch('/api/parseBoardingPass', {
        method: 'POST',
        body: form
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Erreur parsing');

      // on enregistre et on saute à l’étape 1
      updateForm({ flight: {
    departure: data.departureCity,
    arrival:   data.arrivalCity,
    number:    data.flightNumber,
    date:      data.flightDate,
  } });
      router.push('/claim/step-1');
    } catch (err: any) {
      setBpError(err.message);
    } finally {
      setBpLoading(false);
    }
  };

  // Handler saisie manuelle
  const handleManualSubmit = () => {
    const { departure, arrival, number, date } = flightData;
    if (!departure || !arrival || !number || !date) {
      setManualError('Tous les champs sont obligatoires.');
      return;
    }
    // on enregistre et on passe à l’étape 1
    updateForm({ flight: flightData });
    router.push('/claim/step-1');
  };

  return (
    <div className="max-w-md mx-auto p-4 space-y-6">
      <h1 className="text-2xl font-bold text-center">
        Commencez votre demande d’indemnisation
      </h1>

      {/* --- Bloc Import de la carte d’embarquement --- */}
      <div className="border rounded p-4">
        <h2 className="font-semibold mb-2">1. Importez votre carte d’embarquement</h2>
        <input
          type="file"
          accept="image/*,application/pdf"
          onChange={handleBpUpload}
          className="block w-full"
        />
        {bpLoading && <p className="text-gray-600 mt-2">Lecture en cours…</p>}
        {bpError   && <p className="text-red-600 mt-2">{bpError}</p>}
      </div>

      {/* --- Bloc Saisie manuelle --- */}
      <div className="border rounded p-4">
        <h2 className="font-semibold mb-2">2. Ou saisissez les infos manuellement</h2>
        <div className="space-y-3">
          <input
            type="text"
            placeholder="Aéroport de départ (IATA)"
            value={flightData.departure}
            onChange={e => setFlightData({ ...flightData, departure: e.target.value })}
            className="block w-full border p-2 rounded"
          />
          <input
            type="text"
            placeholder="Aéroport d’arrivée (IATA)"
            value={flightData.arrival}
            onChange={e => setFlightData({ ...flightData, arrival: e.target.value })}
            className="block w-full border p-2 rounded"
          />
          <input
            type="text"
            placeholder="Numéro de vol"
            value={flightData.number}
            onChange={e => setFlightData({ ...flightData, number: e.target.value })}
            className="block w-full border p-2 rounded"
          />
          <input
            type="date"
            value={flightData.date}
            onChange={e => setFlightData({ ...flightData, date: e.target.value })}
            className="block w-full border p-2 rounded"
          />
          {manualError && <p className="text-red-600">{manualError}</p>}
          <button
            onClick={handleManualSubmit}
            className="w-full bg-blue-600 text-white py-2 rounded"
          >
            Continuer
          </button>
        </div>
      </div>
    </div>
  );
}
