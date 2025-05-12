function getEnvVar(key: string): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(`❌ La variable d’environnement "${key}" est manquante. Vérifiez votre .env.local`);
  }
  return value;
}

export const AERODATABOX_API_KEY = getEnvVar('AERODATABOX_API_KEY');
export const INSTANTAIR_PROXY = getEnvVar('INSTANTAIR_PROXY');
