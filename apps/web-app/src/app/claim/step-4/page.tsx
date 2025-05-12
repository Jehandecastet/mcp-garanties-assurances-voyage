'use client';
import { useFormData } from '@/context/formContext';
import { useRouter } from 'next/navigation';

export default function Step4() {
  const { formData } = useFormData();
  const router = useRouter();

  if (!formData.isEligible) {
    return <p className="text-red-600">Votre vol n’est pas éligible à une indemnisation.</p>;
  }

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Coordonnées bancaires</h1>
      <p>Nous allons vous verser l’indemnisation de <strong>{formData.compensation?.offer} €</strong>.</p>
      <p>Merci de saisir votre IBAN :</p>
      <input type="text" className="mt-2 p-2 border rounded w-full" placeholder="FR76 XXXX XXXX XXXX XXXX XXXX XXX" />
      <button className="mt-4 bg-blue-600 text-white px-4 py-2 rounded">Valider et continuer</button>
    </div>
  );
}