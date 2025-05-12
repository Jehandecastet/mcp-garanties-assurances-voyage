// src/app/step-4/page.tsx
export default function Step4() {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-4">Étape 4 : Nombre de passagers</h1>
        <form action="/step-5">
          <input type="number" placeholder="Nombre de passagers" className="border p-2 mb-4 w-full" />
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Suivant</button>
        </form>
      </div>
    );
  }
