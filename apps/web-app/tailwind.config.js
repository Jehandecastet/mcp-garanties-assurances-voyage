// tailwind.config.js
module.exports = {
    content: [
      './src/**/*.{html,js,ts,jsx,tsx}', // Ciblez tous les fichiers où vous utilisez Tailwind
      "./pages/**/*.{html,js,ts,jsx,tsx}", // Pour Next.js
      "./components/**/*.{html,js,ts,jsx,tsx}", // Pour React
      // Ajoute d'autres chemins si nécessaire, par exemple :
      "./public/**/*.html",         // Si tu as des fichiers HTML dans un dossier public
      "./app/**/*.{html,js,ts,jsx,tsx}", // Pour une autre structure d'application
    ],
    theme: {
      extend: {
        colors: {
          primary: '#0077FF',  // Bleu pour l'aspect professionnel et fiable
          secondary: '#FF6700', // Orange pour attirer l'attention
          neutral: '#F0F0F0',   // Fond neutre pour la lisibilité
          accent: '#00B4D8',    // Bleu clair pour des appels à l'action
          darkGray: '#333333',  // Texte foncé pour la lisibilité
        },
        fontFamily: {
          sans: ['Poppins', 'Arial', 'sans-serif'], // Typographie moderne et propre
          serif: ['Georgia', 'serif'],
        },
      },
    },
    plugins: [],
  }
  