import Step1 from './Step1Client';

export default function Page() {
  return <Step1 proxyUrl={process.env.NEXT_PUBLIC_INSTANTAIR_PROXY || ''} />;
}
