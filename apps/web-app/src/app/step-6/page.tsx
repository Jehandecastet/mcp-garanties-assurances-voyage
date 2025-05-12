// src/app/step-6/page.tsx
export default function Step6() {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-4">Étape 6 : Numéro de réservation</h1>
        <form action="/step-7">
          <input type="text" placeholder="Code de réservation (6 caractères)" className="border p-2 mb-4 w-full" />
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Suivant</button>
        </form>
      </div>
    );
  }