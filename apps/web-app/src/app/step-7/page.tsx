// src/app/step-7/page.tsx
export default function Step7() {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-4">Étape 7 : Signature</h1>
        <form action="/confirmation">
          <p className="mb-4">Merci de signer électroniquement pour finaliser la demande :</p>
          <input type="text" placeholder="Votre nom complet" className="border p-2 mb-4 w-full" />
          <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded">Finaliser la demande</button>
        </form>
      </div>
    );
  }