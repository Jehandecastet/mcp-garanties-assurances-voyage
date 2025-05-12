import { FormProvider } from "@/context/formContext";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="bg-white text-gray-900">
        <FormProvider>
          <main className="max-w-2xl mx-auto py-8 px-4">{children}</main>
        </FormProvider>
      </body>
    </html>
  );
}
