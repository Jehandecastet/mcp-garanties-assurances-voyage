"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle } from "lucide-react";
import Image from "next/image";
import { useState } from "react";

export default function LandingPage() {
  const [flightNumber, setFlightNumber] = useState("");
  const [flightDate, setFlightDate] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
  
    try {
      const response = await fetch("/api/eligibility", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ flightNumber, flightDate }),
      });
  
      const data = await response.json();
      console.log("Réponse de l'API :", data);
  
      alert("Formulaire envoyé avec succès !");
    } catch (error) {
      console.error("Erreur lors de l'envoi du formulaire :", error);
      alert("Une erreur est survenue, merci de réessayer.");
    }
  };  

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col items-center px-4 py-8 md:px-6 md:py-10">
      <header className="flex flex-col items-center mb-8">
        <Image src="/logo-instantair.svg" alt="InstantAir logo" width={160} height={40} className="mb-4" />
        <h1 className="text-3xl md:text-5xl font-bold text-center max-w-3xl leading-tight mb-4">
          Vol retardé ou annulé ? Transformez votre galère en gain.
        </h1>
        <p className="text-base md:text-xl text-center max-w-2xl">
          Touchez jusqu’à 600 € d’indemnisation sans effort – en quelques clics, sans paperasse.
        </p>
      </header>

      <Card className="w-full max-w-xl shadow-lg mb-10">
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              placeholder="Numéro de vol (ex : AF1234)"
              value={flightNumber}
              onChange={(e) => setFlightNumber(e.target.value)}
            />
            <Input
              placeholder="Date du vol"
              type="date"
              value={flightDate}
              onChange={(e) => setFlightDate(e.target.value)}
            />
            <Button type="submit" className="text-lg py-6">
              Vérifiez si vous êtes éligible
            </Button>
          </form>
          <p className="text-xs text-gray-500 mt-2 text-center">
            Aucun frais si vous n’obtenez rien – service 100% en ligne
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl w-full px-2 md:px-0 mb-12">
        <Feature text="Aucun document à imprimer ni courrier à envoyer" />
        <Feature text="Jusqu'à 600 € selon la règlementation EU261" />
        <Feature text="98 % de taux de succès avec nos experts" />
        <Feature text="En moins de 3 minutes, votre dossier est déposé" />
      </div>

      <section className="w-full max-w-4xl px-2 md:px-0 mb-12">
        <h2 className="text-2xl font-semibold mb-4">Ils nous font confiance</h2>
        <div className="flex flex-wrap justify-center gap-6 items-center">
          <Image src="/logos/airfrance.png" alt="Air France" width={100} height={40} />
          <Image src="/logos/ryanair.png" alt="Ryanair" width={100} height={40} />
          <Image src="/logos/americanairlines.png" alt="American Airlines" width={100} height={40} />
          <Image src="/logos/lufthansa.png" alt="Lufthansa" width={100} height={40} />
          <Image src="/logos/britishairways.png" alt="British Airways" width={100} height={40} />
          <Image src="/logos/easyjet.png" alt="EasyJet" width={100} height={40} />
        </div>
      </section>

      <section className="w-full max-w-4xl px-2 md:px-0 mb-12">
        <h2 className="text-2xl font-semibold mb-4">Ce qu’en disent nos utilisateurs</h2>
        <blockquote className="bg-gray-100 rounded-xl p-4 text-sm md:text-base">
          “Vol annulé à la dernière minute, j’ai rempli le formulaire en 2 minutes. J’ai reçu 400€ en moins de 3 semaines. Merci InstantAir !” – Claire B., Paris
        </blockquote>
      </section>

      <section className="w-full max-w-4xl px-2 md:px-0 mb-20">
        <h2 className="text-2xl font-semibold mb-4">Questions fréquentes</h2>
        <div className="space-y-4">
          <FAQ question="Qui peut demander une indemnisation ?" answer="Toute personne ayant subi un retard de plus de 3h, une annulation ou un refus d’embarquement dans les 5 dernières années." />
          <FAQ question="Combien vais-je recevoir ?" answer="Le montant dépend de la distance du vol et du retard à l’arrivée. Il peut aller jusqu’à 600€ selon la réglementation EU261." />
          <FAQ question="Combien de temps cela prend-il ?" answer="Vous déposez votre dossier en quelques minutes, et nous faisons le reste. Les indemnisations sont souvent versées en 2 à 8 semaines." />
        </div>
      </section>
    </div>
  );
}

function Feature({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-3">
      <CheckCircle className="text-green-600 w-6 h-6" />
      <span className="text-base md:text-lg">{text}</span>
    </div>
  );
}

function FAQ({ question, answer }: { question: string; answer: string }) {
  return (
    <div>
      <h3 className="font-semibold text-gray-800 mb-1">{question}</h3>
      <p className="text-sm text-gray-600">{answer}</p>
    </div>
  );
}
