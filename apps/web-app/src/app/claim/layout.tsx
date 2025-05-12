export default function ClaimLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen px-6 py-10">
      <main className="max-w-2xl mx-auto">{children}</main>
    </div>
  );
}
