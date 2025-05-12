// src/app/step-5/page.tsx
export default function Step5() {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-4">Étape 5 : Carte d'embarquement</h1>
        <form action="/step-6">
          <input type="file" className="border p-2 mb-4 w-full" />
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Suivant</button>
        </form>
      </div>
    );
  }