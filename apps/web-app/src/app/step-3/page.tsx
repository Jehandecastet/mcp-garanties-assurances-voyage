export default function Step3() {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-4">Étape 3 : Temps de retard</h1>
        <form action="/step-4">
          <select className="border p-2 mb-4 w-full">
            <option>Moins de 3 heures</option>
            <option>Entre 3 et 4 heures</option>
            <option>Plus de 4 heures</option>
            <option>Je ne suis jamais arrivé</option>
          </select>
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Suivant</button>
        </form>
      </div>
    );
  }