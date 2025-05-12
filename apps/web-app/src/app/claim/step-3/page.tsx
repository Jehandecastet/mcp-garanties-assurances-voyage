'use client';
import { useFormData } from '@/context/formContext';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Step3() {
  const { formData, updateForm } = useFormData();
  const [loading, setLoading] = useState(true);
  const [eligible, setEligible] = useState(false);
  const [message, setMessage] = useState('');
  const router = useRouter();

  useEffect(() => {
    async function fetchData() {
      const { flightNumber, flightDate, flight } = formData;

      const delayRes = await fetch(`/api/flight-delay?flightNumber=${flightNumber}&date=${flightDate}`);
      const { delayMinutes } = await delayRes.json();

      const distanceRes = await fetch(`/api/flight-distance?from=${flight.departure}&to=${flight.arrival}`);
      const { distance } = await distanceRes.json();

      if (delayMinutes >= 180) {
        let base = 0;
        if (distance < 1500) base = 250;
        else if (distance < 3500) base = 400;
        else base = 600;

        const offer = Math.round(base * 0.7);
        updateForm({
          delayMinutes,
          isEligible: true,
          compensation: { distance, base, offer }
        });
        setEligible(true);
      } else {
        updateForm({ delayMinutes, isEligible: false });
        setMessage(`Le vol a moins de 180 min de retard (${delayMinutes} min)`);
      }
      setLoading(false);
    }
    fetchData();
  }, []);

  if (loading) return <p>Analyse en cours...</p>;
  if (!eligible) return <p className="text-red-600">{message}</p>;

  const { distance, base, offer } = formData.compensation!;

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Proposition InstantAir</h1>
      <p>✈️ Distance estimée : {distance} km</p>
      <p>💶 Indemnité théorique : {base} €</p>
      <p className="text-green-700 font-bold">⚡ Offre InstantAir : {offer} € versés immédiatement</p>
      <button onClick={() => router.push('/claim/step-4')} className="mt-4 bg-blue-600 text-white px-4 py-2 rounded">
        J’accepte et je continue
      </button>
    </div>
  );
}