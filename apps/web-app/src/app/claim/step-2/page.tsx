'use client';
import { useFormData } from '@/context/formContext';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Step2() {
  const { formData } = useFormData();
  const router = useRouter();
  const [isEligible, setIsEligible] = useState<boolean | null>(null);

  useEffect(() => {
    const { flight, isClient } = formData;
    if (!flight) return;

    // MOCK : valeurs fictives pour test
    const delayMinutes = 190;
    const cancelNoticeDays = 7;

    const eligible =
      (flight.problemType === 'retard' && delayMinutes >= 180) ||
      (flight.problemType === 'annulation' && cancelNoticeDays <= 14);

    setIsEligible(eligible);

    if (eligible) {
      if (isClient) router.push('/claim/step-3');
      else router.push('/claim/step-4');
    }
  }, [formData, router]);

  if (isEligible === false) {
    return (
      <div>
        <h1 className="text-xl font-bold mb-4">Vol non éligible</h1>
        <p className="text-red-600">Votre vol ne donne pas droit à une indemnisation selon nos critères.</p>
      </div>
    );
  }

  return <p>Vérification de l'éligibilité en cours...</p>;
}
