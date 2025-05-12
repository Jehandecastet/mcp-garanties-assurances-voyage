export default function Step2() {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-4">Étape 2 : Problème de vol</h1>
        <form action="/step-3">
          <select className="border p-2 mb-4 w-full">
            <option>Vol annulé ou modifié</option>
            <option>Vol retardé</option>
            <option>Refus d'embarquement</option>
            <option>Autre problème</option>
          </select>
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Suivant</button>
        </form>
      </div>
    );
  }